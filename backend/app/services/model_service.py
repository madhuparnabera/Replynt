import logging
from pathlib import Path
from typing import Any, Dict, List

import joblib
import pandas as pd

from app.utils.text import (
    combine_subject_body,
    detect_contains_deadline,
    detect_contains_money,
    normalize_text,
)

logger = logging.getLogger(__name__)

PRIORITY_LABEL_MAP = {0: "P1", 1: "P2", 2: "P3", "0": "P1", "1": "P2", "2": "P3", "P1": "P1", "P2": "P2", "P3": "P3"}
REPLY_LABEL_MAP = {0: False, 1: True, "0": False, "1": True, "No": False, "Yes": True, False: False, True: True}

# Fix 2 Option A — Business domain whitelist signals.
# If any of these are found in the normalized email text, the junk filter is
# bypassed entirely and the email is treated as relevant.
BUSINESS_WHITELIST_SIGNALS = [
    "invoice",
    "purchase order",
    "payment",
    "refund",
    "contract",
    "proposal",
    "quote",
    "statement of work",
    "sow",
    "nda",
    "agreement",
    "deadline",
    "urgent",
    "shipment",
    "delivery",
    "order",
    "ticket",
    "support",
    "escalation",
    "sla",
    "onboarding",
    "renewal",
    "subscription",
    "due date",
    "follow up",
    "action required",
]

# Fix 1 — Confidence threshold for junk short-circuit.
# A prediction of "junk" is only trusted when the model's confidence
# is at or above this value. Below it, the email passes through to
# downstream models so genuinely uncertain cases are not silently dropped.
JUNK_CONFIDENCE_THRESHOLD = 0.75


class ModelService:
    def __init__(self, models_dir: Path) -> None:
        self.models_dir = Path(models_dir)
        self.models: Dict[str, Any] = {}

    def load_models(self) -> None:
        model_files = {
            "junk": "junk_pipeline.pkl",
            "priority": "priority_pipeline.pkl",
            "intent": "intent_pipeline.pkl",
            "needs_reply": "needs_reply_pipeline.pkl",
        }

        loaded: Dict[str, Any] = {}
        for key, file_name in model_files.items():
            path = self.models_dir / file_name
            if not path.exists():
                raise FileNotFoundError(f"Required model file not found: {path}")
            loaded[key] = joblib.load(path)
            logger.info("Loaded %s model from %s", key, path)

        self.models = loaded

    @property
    def is_ready(self) -> bool:
        return all(name in self.models for name in ["junk", "priority", "intent", "needs_reply"])

    def loaded_model_names(self) -> List[str]:
        return sorted(self.models.keys())

    def analyze_email(self, subject: str, body: str) -> Dict[str, Any]:
        if not self.is_ready:
            raise RuntimeError("Models are not loaded")

        combined_text = combine_subject_body(subject, body)
        normalized_text = normalize_text(combined_text)
        reasons: List[str] = []
        confidence_scores: Dict[str, Dict[str, float]] = {}

        # ------------------------------------------------------------------
        # Fix 2 Option A — Whitelist pre-check.
        # If the email contains known business-domain signals, skip the junk
        # filter entirely. This prevents the NB model (trained on generic
        # spam data) from mis-classifying legitimate business emails.
        # ------------------------------------------------------------------
        whitelist_hit = self._check_business_whitelist(normalized_text)
        if whitelist_hit:
            logger.debug("Business whitelist match on signal '%s'; bypassing junk filter.", whitelist_hit)
            reasons.append(f"Business signal '{whitelist_hit}' detected; junk filter bypassed.")
            is_junk = False
            confidence_scores["junk"] = {"relevant": 1.0, "junk": 0.0}
        else:
            # ---------------------------------------------------------------
            # Fix 1 — Confidence-gated junk short-circuit.
            # Only treat the email as junk when the model's confidence meets
            # or exceeds JUNK_CONFIDENCE_THRESHOLD (0.75). Below that cutoff
            # the prediction is treated as uncertain and passes downstream.
            # ---------------------------------------------------------------
            junk_payload = pd.DataFrame({"text": [normalized_text]})
            junk_prediction = self.models["junk"].predict(junk_payload)[0]
            junk_probabilities = self._predict_proba_map(self.models["junk"], junk_payload)
            confidence_scores["junk"] = junk_probabilities

            raw_is_junk = str(junk_prediction).strip().lower() == "junk"
            junk_confidence = junk_probabilities.get("junk", 0.0)

            if raw_is_junk and junk_confidence >= JUNK_CONFIDENCE_THRESHOLD:
                is_junk = True
                logger.debug(
                    "Email classified as junk with confidence %.4f (threshold %.2f).",
                    junk_confidence,
                    JUNK_CONFIDENCE_THRESHOLD,
                )
            elif raw_is_junk:
                # Model predicted junk but confidence is below threshold —
                # log and fall through to downstream models.
                is_junk = False
                reasons.append(
                    f"Junk predicted but confidence {junk_confidence:.2f} is below "
                    f"threshold {JUNK_CONFIDENCE_THRESHOLD}; treating as relevant."
                )
                logger.debug(
                    "Junk prediction below confidence threshold (%.4f < %.2f); passing through.",
                    junk_confidence,
                    JUNK_CONFIDENCE_THRESHOLD,
                )
            else:
                is_junk = False

        if is_junk:
            reasons.append("Email classified as junk, so downstream models were skipped.")
            return {
                "junk": True,
                "priority": None,
                "intent": None,
                "needs_reply": None,
                "confidence_scores": confidence_scores,
                "reasons": reasons,
            }

        engineered = self._build_engineered_features(normalized_text)
        priority_prediction = self.models["priority"].predict(engineered)[0]
        priority_probabilities = self._predict_proba_map(self.models["priority"], engineered, PRIORITY_LABEL_MAP)
        priority_label = PRIORITY_LABEL_MAP.get(priority_prediction, str(priority_prediction))
        confidence_scores["priority"] = priority_probabilities

        intent_payload = pd.DataFrame({"email_text": [normalized_text]})
        intent_prediction = self.models["intent"].predict(intent_payload)[0]
        intent_probabilities = self._predict_proba_map(self.models["intent"], intent_payload)
        confidence_scores["intent"] = intent_probabilities
        intent_label = str(intent_prediction)

        reply_payload = pd.DataFrame(
            {
                "email_text": [normalized_text],
                "priority": [priority_label],
                "intent": [intent_label],
            }
        )
        reply_prediction = self.models["needs_reply"].predict(reply_payload)[0]
        reply_probabilities = self._predict_proba_map(
            self.models["needs_reply"],
            reply_payload,
            {0: "No", 1: "Yes", "0": "No", "1": "Yes"},
        )
        confidence_scores["needs_reply"] = reply_probabilities
        needs_reply = REPLY_LABEL_MAP.get(reply_prediction, str(reply_prediction).strip().lower() == "yes")

        reasons.extend(self._build_reasons(priority_label, intent_label, needs_reply, engineered))

        return {
            "junk": False,
            "priority": priority_label,
            "intent": intent_label,
            "needs_reply": needs_reply,
            "confidence_scores": confidence_scores,
            "reasons": reasons,
        }

    def _check_business_whitelist(self, normalized_text: str) -> str | None:
        """Return the first matching whitelist signal found in the text, or None."""
        for signal in BUSINESS_WHITELIST_SIGNALS:
            if signal in normalized_text:
                return signal
        return None

    def _build_engineered_features(self, normalized_text: str) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "email_text": [normalized_text],
                "contains_money": [detect_contains_money(normalized_text)],
                "contains_deadline": [detect_contains_deadline(normalized_text)],
                "text_length": [len(normalized_text)],
            }
        )

    def _predict_proba_map(self, model: Any, payload: pd.DataFrame, label_map: Dict[Any, str] | None = None) -> Dict[str, float]:
        if not hasattr(model, "predict_proba"):
            return {}

        probabilities = model.predict_proba(payload)[0]
        classes = getattr(model, "classes_", range(len(probabilities)))
        result: Dict[str, float] = {}
        for cls, score in zip(classes, probabilities):
            label = label_map.get(cls, cls) if label_map else cls
            result[str(label)] = round(float(score), 4)
        return result

    def _build_reasons(self, priority: str, intent: str, needs_reply: bool, engineered: pd.DataFrame) -> List[str]:
        reasons: List[str] = [f"Priority predicted as {priority}.", f"Intent predicted as {intent}."]
        if int(engineered.loc[0, "contains_money"]) == 1:
            reasons.append("Financial language detected in the email content.")
        if int(engineered.loc[0, "contains_deadline"]) == 1:
            reasons.append("Deadline or urgency language detected in the email content.")
        if needs_reply:
            reasons.append("The combined signals indicate a reply is likely needed.")
        else:
            reasons.append("The combined signals indicate a reply is probably not needed.")
        return reasons
