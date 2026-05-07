from pathlib import Path
import json
import textwrap


BASE_DIR = Path.home() / "Desktop" / "replynt_final"
NOTEBOOK_DIR = BASE_DIR / "notebooks"
MODELS_DIR = BASE_DIR / "models"


def md(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": textwrap.dedent(text).strip("\n").splitlines(keepends=True),
    }


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": textwrap.dedent(text).strip("\n").splitlines(keepends=True),
    }


def nb(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


BOOTSTRAP = """
import importlib
import subprocess
import sys

REQUIRED_PACKAGES = {
    "numpy": "numpy",
    "pandas": "pandas",
    "sklearn": "scikit-learn",
    "matplotlib": "matplotlib",
    "seaborn": "seaborn",
    "joblib": "joblib",
}

missing = []
for module_name, package_name in REQUIRED_PACKAGES.items():
    try:
        importlib.import_module(module_name)
    except ImportError:
        missing.append(package_name)

if missing:
    print("Installing missing packages:", ", ".join(missing))
    subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
else:
    print("All base packages are already installed.")
"""


COMMON = """
from __future__ import annotations

import re
import warnings
from pathlib import Path
from typing import Iterable

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from IPython.display import display
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import LinearSVC

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid")
pd.set_option("display.max_colwidth", 160)

RANDOM_STATE = 42
BASE_DIR = Path.home() / "Desktop" / "replynt_final"
DATA_DIR = BASE_DIR / "data"
NOTEBOOK_DIR = BASE_DIR / "notebooks"
MODELS_DIR = BASE_DIR / "models"
NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

print(f"Data directory: {DATA_DIR}")
print(f"Notebook directory: {NOTEBOOK_DIR}")
print(f"Model directory: {MODELS_DIR}")
"""


HELPERS = """
def normalize_text(value: str) -> str:
    if pd.isna(value):
        return ""
    text = str(value).replace("\\r", " ").replace("\\n", " ")
    text = re.sub(r"https?://\\S+|www\\.\\S+", " URL ", text, flags=re.IGNORECASE)
    text = re.sub(r"\\S+@\\S+", " EMAIL ", text)
    text = re.sub(r"[^a-zA-Z0-9$%!?.,:/\\\\-]+", " ", text)
    text = re.sub(r"\\s+", " ", text).strip().lower()
    return text


def detect_csv(candidates: Iterable[str], required_columns: Iterable[str]) -> Path:
    required_columns = set(required_columns)
    candidates = [candidate.lower() for candidate in candidates]
    files = sorted(DATA_DIR.glob("*.csv"))

    for path in files:
        if any(candidate in path.name.lower() for candidate in candidates):
            preview = pd.read_csv(path, nrows=5)
            if required_columns.issubset(set(preview.columns)):
                return path

    for path in files:
        preview = pd.read_csv(path, nrows=5)
        if required_columns.issubset(set(preview.columns)):
            return path

    raise FileNotFoundError(
        f"Could not find a CSV in {DATA_DIR} matching names={candidates} and columns={sorted(required_columns)}"
    )


def safe_n_splits(y: pd.Series, default: int = 5) -> int:
    return max(2, min(default, int(y.value_counts().min())))


def metrics_frame(y_true, y_pred, average="macro") -> pd.DataFrame:
    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, average=average, zero_division=0),
        "recall": recall_score(y_true, y_pred, average=average, zero_division=0),
        "f1": f1_score(y_true, y_pred, average=average, zero_division=0),
    }
    return pd.DataFrame([metrics]).round(4)


def plot_confusion(y_true, y_pred, labels):
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    cm_df = pd.DataFrame(cm, index=labels, columns=labels)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm_df, annot=True, fmt="d", cmap="Blues")
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title("Confusion Matrix")
    plt.tight_layout()
    plt.show()
    return cm_df


def summarize_cv(results: dict, model_name: str) -> pd.DataFrame:
    frame = pd.DataFrame(results)
    keep = [col for col in frame.columns if col.startswith("test_")]
    summary = frame[keep].agg(["mean", "std"]).T.reset_index()
    summary.columns = ["metric", f"{model_name}_mean", f"{model_name}_std"]
    summary["metric"] = summary["metric"].str.replace("test_", "", regex=False)
    return summary
"""


NB1 = nb(
    [
        md(
            """
            # REPLYNT Notebook 1: Junk Filter

            This notebook trains REPLYNT's junk filter using TF-IDF word and character n-grams. It compares calibrated Logistic Regression with calibrated Naive Bayes, evaluates the selected model with a stratified holdout set and stratified cross-validation, explains the strongest signals, and saves the final trained pipeline as `junk_pipeline.pkl`.
            """
        ),
        md(
            """
            ## Setup

            The first cells install missing dependencies if needed and define reusable helpers for data discovery, text normalization, evaluation, and visualization.
            """
        ),
        code(BOOTSTRAP),
        code(COMMON),
        code(
            HELPERS
            + """
junk_path = detect_csv(["junk", "spam", "filter"], ["text", "relevance_label"])
print(f"Using dataset: {junk_path}")

df = pd.read_csv(junk_path)
df = df[["text", "relevance_label"]].dropna().copy()
df["text"] = df["text"].map(normalize_text)
df["relevance_label"] = df["relevance_label"].astype(str).str.strip().str.lower()
df = df[df["relevance_label"].isin(["junk", "relevant"])].reset_index(drop=True)
df["text_length"] = df["text"].str.len()

display(df.head())
display(df["relevance_label"].value_counts().to_frame("count"))
display(df["text_length"].describe().to_frame("text_length"))
"""
        ),
        md(
            """
            ## Train/Test Split and Cross-Validation

            We keep a stratified test split for final reporting and use `StratifiedKFold` on the training set to compare models fairly.
            """
        ),
        code(
            """
            X = df[["text"]].copy()
            y = df["relevance_label"].copy()

            X_train, X_test, y_train, y_test = train_test_split(
                X,
                y,
                test_size=0.20,
                stratify=y,
                random_state=RANDOM_STATE,
            )

            cv = StratifiedKFold(
                n_splits=safe_n_splits(y_train, default=5),
                shuffle=True,
                random_state=RANDOM_STATE,
            )

            print("Train shape:", X_train.shape)
            print("Test shape:", X_test.shape)
            """
        ),
        code(
            """
            word_tfidf = TfidfVectorizer(
                analyzer="word",
                ngram_range=(1, 2),
                min_df=3,
                max_df=0.98,
                sublinear_tf=True,
                strip_accents="unicode",
            )

            char_tfidf = TfidfVectorizer(
                analyzer="char_wb",
                ngram_range=(3, 5),
                min_df=3,
                sublinear_tf=True,
            )

            feature_builder = ColumnTransformer(
                transformers=[
                    ("word_tfidf", word_tfidf, "text"),
                    ("char_tfidf", char_tfidf, "text"),
                ]
            )

            logistic_pipeline = Pipeline(
                steps=[
                    ("features", feature_builder),
                    (
                        "classifier",
                        CalibratedClassifierCV(
                            estimator=LogisticRegression(
                                max_iter=4000,
                                class_weight="balanced",
                                solver="liblinear",
                                random_state=RANDOM_STATE,
                            ),
                            cv=3,
                            method="sigmoid",
                        ),
                    ),
                ]
            )

            naive_bayes_pipeline = Pipeline(
                steps=[
                    ("features", feature_builder),
                    (
                        "classifier",
                        CalibratedClassifierCV(
                            estimator=MultinomialNB(alpha=0.5),
                            cv=3,
                            method="sigmoid",
                        ),
                    ),
                ]
            )

            models = {
                "Calibrated Logistic Regression": logistic_pipeline,
                "Calibrated Naive Bayes": naive_bayes_pipeline,
            }

            scoring = {
                "accuracy": "accuracy",
                "precision": "precision_macro",
                "recall": "recall_macro",
                "f1": "f1_macro",
            }

            cv_tables = []
            cv_scores = {}
            for name, model in models.items():
                scores = cross_validate(model, X_train, y_train, cv=cv, scoring=scoring, n_jobs=1)
                cv_tables.append(summarize_cv(scores, name))
                cv_scores[name] = scores["test_f1"].mean()

            cv_report = cv_tables[0]
            for table in cv_tables[1:]:
                cv_report = cv_report.merge(table, on="metric", how="outer")

            display(cv_report.round(4))
            best_model_name = max(cv_scores, key=cv_scores.get)
            best_model = models[best_model_name]
            print("Selected model:", best_model_name)
            """
        ),
        code(
            """
            best_model.fit(X_train, y_train)
            y_pred = best_model.predict(X_test)

            display(metrics_frame(y_test, y_pred, average="macro"))
            print(classification_report(y_test, y_pred, zero_division=0))
            confusion_df = plot_confusion(y_test, y_pred, labels=["junk", "relevant"])
            display(confusion_df)
            """
        ),
        md(
            """
            ## Explainability

            When Logistic Regression wins, we inspect its learned coefficients over the TF-IDF feature space. If Naive Bayes wins, we inspect class likelihood deltas instead.
            """
        ),
        code(
            """
            if "Logistic" in best_model_name:
                calibrated = best_model.named_steps["classifier"]
                linear_model = calibrated.calibrated_classifiers_[0].estimator
                feature_names = best_model.named_steps["features"].get_feature_names_out()
                coef = linear_model.coef_[0]
                importance = pd.DataFrame(
                    {"feature": feature_names, "coefficient": coef, "abs_coefficient": np.abs(coef)}
                ).sort_values("abs_coefficient", ascending=False)

                print("Top features pushing toward junk")
                display(importance.sort_values("coefficient", ascending=False).head(20)[["feature", "coefficient"]])

                print("Top features pushing toward relevant")
                display(importance.sort_values("coefficient", ascending=True).head(20)[["feature", "coefficient"]])
            else:
                calibrated = best_model.named_steps["classifier"]
                nb_model = calibrated.calibrated_classifiers_[0].estimator
                feature_names = best_model.named_steps["features"].get_feature_names_out()
                delta = nb_model.feature_log_prob_[0] - nb_model.feature_log_prob_[1]
                importance = pd.DataFrame({"feature": feature_names, "log_prob_delta": delta})
                display(importance.sort_values("log_prob_delta", ascending=False).head(25))
            """
        ),
        code(
            """
            model_path = MODELS_DIR / "junk_pipeline.pkl"
            joblib.dump(best_model, model_path)
            print(f"Saved model to: {model_path}")
            """
        ),
        code(
            """
            sample_emails = pd.DataFrame(
                {
                    "text": [
                        normalize_text("Claim your exclusive cash reward now by clicking this limited-time URL."),
                        normalize_text("Hi team, attached is the revised customer contract for your review before tomorrow."),
                    ]
                }
            )

            sample_predictions = best_model.predict(sample_emails)
            sample_probabilities = best_model.predict_proba(sample_emails).max(axis=1)
            sample_results = sample_emails.copy()
            sample_results["predicted_label"] = sample_predictions
            sample_results["confidence"] = sample_probabilities
            display(sample_results)
            """
        ),
    ]
)


NB2 = nb(
    [
        md(
            """
            # REPLYNT Notebook 2: Priority Classifier

            This notebook predicts `P1`, `P2`, or `P3` priority using a combination of TF-IDF text features and engineered business signals such as `contains_money`, `contains_deadline`, and `text_length`. It compares a balanced LinearSVC against XGBoost, reports full evaluation metrics, explains the winning model, and saves the trained pipeline as `priority_pipeline.pkl`.
            """
        ),
        code(
            BOOTSTRAP
            + """

try:
    import xgboost
    print("XGBoost already installed:", xgboost.__version__)
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "xgboost"])
    import xgboost
    print("Installed XGBoost:", xgboost.__version__)
"""
        ),
        code(COMMON + "\nfrom xgboost import XGBClassifier"),
        code(
            HELPERS
            + """
priority_path = detect_csv(["triage", "priority"], ["subject", "body", "priority"])
print(f"Using dataset: {priority_path}")

df = pd.read_csv(priority_path)
df["subject"] = df["subject"].fillna("")
df["body"] = df["body"].fillna("")
df["email_text"] = (df["subject"].astype(str) + " " + df["body"].astype(str)).map(normalize_text)
df["contains_money"] = df.get("contains_money", False).astype(str).str.lower().isin(["true", "1", "yes"])
df["contains_deadline"] = df.get("contains_deadline", False).astype(str).str.lower().isin(["true", "1", "yes"])
df["text_length"] = df["email_text"].str.len()
df["priority"] = df["priority"].astype(str).str.strip()
df = df[df["priority"].isin(["P1", "P2", "P3"])].reset_index(drop=True)

label_map = {"P1": 0, "P2": 1, "P3": 2}
inverse_label_map = {value: key for key, value in label_map.items()}

display(df[["subject", "body", "priority", "contains_money", "contains_deadline", "text_length"]].head())
display(df["priority"].value_counts().to_frame("count"))
"""
        ),
        code(
            """
            X = df[["email_text", "contains_money", "contains_deadline", "text_length"]].copy()
            y = df["priority"].map(label_map)

            X_train, X_test, y_train, y_test = train_test_split(
                X,
                y,
                test_size=0.20,
                stratify=y,
                random_state=RANDOM_STATE,
            )

            cv = StratifiedKFold(
                n_splits=safe_n_splits(pd.Series(y_train), default=5),
                shuffle=True,
                random_state=RANDOM_STATE,
            )
            """
        ),
        code(
            """
            text_vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.98,
                sublinear_tf=True,
                strip_accents="unicode",
            )

            feature_builder = ColumnTransformer(
                transformers=[
                    ("text", text_vectorizer, "email_text"),
                    (
                        "numeric",
                        Pipeline(
                            steps=[
                                ("imputer", SimpleImputer(strategy="median")),
                                ("scaler", StandardScaler(with_mean=False)),
                            ]
                        ),
                        ["text_length"],
                    ),
                    ("flags", SimpleImputer(strategy="most_frequent"), ["contains_money", "contains_deadline"]),
                ]
            )

            linear_svc_pipeline = Pipeline(
                steps=[
                    ("features", feature_builder),
                    ("classifier", LinearSVC(class_weight="balanced", random_state=RANDOM_STATE)),
                ]
            )

            xgb_pipeline = Pipeline(
                steps=[
                    ("features", feature_builder),
                    (
                        "classifier",
                        XGBClassifier(
                            objective="multi:softprob",
                            num_class=3,
                            n_estimators=250,
                            max_depth=6,
                            learning_rate=0.08,
                            subsample=0.9,
                            colsample_bytree=0.8,
                            min_child_weight=2,
                            reg_lambda=1.0,
                            eval_metric="mlogloss",
                            random_state=RANDOM_STATE,
                            n_jobs=4,
                            tree_method="hist",
                        ),
                    ),
                ]
            )

            models = {"LinearSVC": linear_svc_pipeline, "XGBoost": xgb_pipeline}
            scoring = {
                "accuracy": "accuracy",
                "precision": "precision_macro",
                "recall": "recall_macro",
                "f1": "f1_macro",
            }

            cv_tables = []
            cv_scores = {}
            for name, model in models.items():
                scores = cross_validate(model, X_train, y_train, cv=cv, scoring=scoring, n_jobs=1)
                cv_tables.append(summarize_cv(scores, name))
                cv_scores[name] = scores["test_f1"].mean()

            cv_report = cv_tables[0]
            for table in cv_tables[1:]:
                cv_report = cv_report.merge(table, on="metric", how="outer")

            display(cv_report.round(4))
            best_model_name = max(cv_scores, key=cv_scores.get)
            best_model = models[best_model_name]
            print("Selected model:", best_model_name)
            """
        ),
        code(
            """
            best_model.fit(X_train, y_train)
            y_pred = best_model.predict(X_test)

            y_test_labels = pd.Series(y_test).map(inverse_label_map)
            y_pred_labels = pd.Series(y_pred).map(inverse_label_map)

            display(metrics_frame(y_test_labels, y_pred_labels, average="macro"))
            print(classification_report(y_test_labels, y_pred_labels, zero_division=0))
            confusion_df = plot_confusion(y_test_labels, y_pred_labels, labels=["P1", "P2", "P3"])
            display(confusion_df)
            """
        ),
        md(
            """
            ## Explainability

            LinearSVC exposes class-wise coefficients, while XGBoost exposes feature importances. The code below adapts to whichever model wins.
            """
        ),
        code(
            """
            feature_names = best_model.named_steps["features"].get_feature_names_out()
            classifier = best_model.named_steps["classifier"]

            if best_model_name == "LinearSVC":
                coef_frame = pd.DataFrame(classifier.coef_.T, index=feature_names, columns=["P1", "P2", "P3"])
                for label in ["P1", "P2", "P3"]:
                    print(f"Top features for {label}")
                    display(coef_frame[label].sort_values(ascending=False).head(15).reset_index().rename(columns={"index": "feature", label: "weight"}))
            else:
                importance = pd.DataFrame({"feature": feature_names, "importance": classifier.feature_importances_})
                display(importance.sort_values("importance", ascending=False).head(25))
            """
        ),
        code(
            """
            model_path = MODELS_DIR / "priority_pipeline.pkl"
            joblib.dump(best_model, model_path)
            print(f"Saved model to: {model_path}")
            """
        ),
        code(
            """
            sample_email = pd.DataFrame(
                {
                    "email_text": [normalize_text("Urgent: please approve the payment request by 5 PM today so finance can process it.")],
                    "contains_money": [True],
                    "contains_deadline": [True],
                    "text_length": [89],
                }
            )

            predicted_priority = pd.Series(best_model.predict(sample_email)).map(inverse_label_map)
            sample_output = sample_email.copy()
            sample_output["predicted_priority"] = predicted_priority.values
            display(sample_output)
            """
        ),
    ]
)


NB3 = nb(
    [
        md(
            """
            # REPLYNT Notebook 3: Intent Classifier

            This notebook predicts the intent class for incoming email. It uses TF-IDF text features with a balanced LinearSVC, handles rare classes by adapting the number of stratified folds, reports evaluation metrics, surfaces the most common confusion pairs, and saves the trained pipeline as `intent_pipeline.pkl`.
            """
        ),
        code(BOOTSTRAP),
        code(COMMON),
        code(
            HELPERS
            + """
intent_path = detect_csv(["triage", "intent"], ["subject", "body", "intent"])
print(f"Using dataset: {intent_path}")

df = pd.read_csv(intent_path)
df["subject"] = df["subject"].fillna("")
df["body"] = df["body"].fillna("")
df["email_text"] = (df["subject"].astype(str) + " " + df["body"].astype(str)).map(normalize_text)
df["intent"] = df["intent"].astype(str).str.strip()
df = df[df["intent"].ne("")].reset_index(drop=True)

counts = df["intent"].value_counts()
rare_classes = counts[counts < 5]
display(counts.to_frame("count"))
if rare_classes.empty:
    print("No intent classes have fewer than 5 examples.")
else:
    print("Rare classes detected. Stratified folds will be reduced automatically.")
    display(rare_classes.to_frame("count"))
"""
        ),
        code(
            """
            X = df[["email_text"]].copy()
            y = df["intent"].copy()

            X_train, X_test, y_train, y_test = train_test_split(
                X,
                y,
                test_size=0.20,
                stratify=y,
                random_state=RANDOM_STATE,
            )

            cv = StratifiedKFold(
                n_splits=safe_n_splits(y_train, default=5),
                shuffle=True,
                random_state=RANDOM_STATE,
            )
            """
        ),
        code(
            """
            intent_pipeline = Pipeline(
                steps=[
                    (
                        "features",
                        ColumnTransformer(
                            transformers=[
                                (
                                    "text",
                                    TfidfVectorizer(
                                        ngram_range=(1, 2),
                                        min_df=2,
                                        max_df=0.98,
                                        sublinear_tf=True,
                                        strip_accents="unicode",
                                    ),
                                    "email_text",
                                )
                            ]
                        ),
                    ),
                    ("classifier", LinearSVC(class_weight="balanced", random_state=RANDOM_STATE)),
                ]
            )

            scoring = {
                "accuracy": "accuracy",
                "precision": "precision_macro",
                "recall": "recall_macro",
                "f1": "f1_macro",
            }

            cv_results = cross_validate(intent_pipeline, X_train, y_train, cv=cv, scoring=scoring, n_jobs=1)
            display(summarize_cv(cv_results, "LinearSVC").round(4))
            """
        ),
        code(
            """
            intent_pipeline.fit(X_train, y_train)
            y_pred = intent_pipeline.predict(X_test)

            display(metrics_frame(y_test, y_pred, average="macro"))
            print(classification_report(y_test, y_pred, zero_division=0))
            labels = sorted(y_train.unique())
            confusion_df = plot_confusion(y_test, y_pred, labels=labels)
            display(confusion_df)
            """
        ),
        md(
            """
            ## Top Confusion Classes

            The most frequent off-diagonal pairs tell us which intents are hardest to separate and where more data or business heuristics may help.
            """
        ),
        code(
            """
            confusions = []
            for actual in confusion_df.index:
                for predicted in confusion_df.columns:
                    if actual != predicted and confusion_df.loc[actual, predicted] > 0:
                        confusions.append(
                            {"actual": actual, "predicted": predicted, "count": int(confusion_df.loc[actual, predicted])}
                        )

            confusion_pairs = pd.DataFrame(confusions).sort_values("count", ascending=False)
            display(confusion_pairs.head(10))
            """
        ),
        code(
            """
            feature_names = intent_pipeline.named_steps["features"].get_feature_names_out()
            classifier = intent_pipeline.named_steps["classifier"]
            coef_frame = pd.DataFrame(classifier.coef_.T, index=feature_names, columns=classifier.classes_)

            for label in classifier.classes_:
                print(f"Top features for {label}")
                display(coef_frame[label].sort_values(ascending=False).head(15).reset_index().rename(columns={"index": "feature", label: "weight"}))
            """
        ),
        code(
            """
            model_path = MODELS_DIR / "intent_pipeline.pkl"
            joblib.dump(intent_pipeline, model_path)
            print(f"Saved model to: {model_path}")
            """
        ),
        code(
            """
            sample_email = pd.DataFrame(
                {"email_text": [normalize_text("Can we set up a 30-minute meeting tomorrow to review the contract status?")]}
            )

            sample_output = sample_email.copy()
            sample_output["predicted_intent"] = intent_pipeline.predict(sample_email)
            display(sample_output)
            """
        ),
    ]
)


NB4 = nb(
    [
        md(
            """
            # REPLYNT Notebook 4: Needs Reply Predictor

            This notebook predicts whether an email needs a reply using message text together with priority and intent. It compares Logistic Regression against XGBoost, reports holdout metrics and probability scores, explains the strongest model signals, and saves the final pipeline as `needs_reply_pipeline.pkl`.
            """
        ),
        code(
            BOOTSTRAP
            + """

try:
    import xgboost
    print("XGBoost already installed:", xgboost.__version__)
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "xgboost"])
    import xgboost
    print("Installed XGBoost:", xgboost.__version__)
"""
        ),
        code(COMMON + "\nfrom xgboost import XGBClassifier"),
        code(
            HELPERS
            + """
reply_path = detect_csv(["triage", "reply"], ["needs_reply", "priority", "intent"])
print(f"Using dataset: {reply_path}")

df = pd.read_csv(reply_path)
subject_text = df.get("subject", pd.Series("", index=df.index)).fillna("").astype(str)
body_text = df.get("body", pd.Series("", index=df.index)).fillna("").astype(str)
combined_text = df.get("combined_text", pd.Series("", index=df.index)).fillna("").astype(str)

fallback_text = subject_text + " " + body_text
df["email_text"] = np.where(combined_text.str.strip().eq(""), fallback_text, combined_text)
df["email_text"] = pd.Series(df["email_text"], index=df.index).map(normalize_text)
df["priority"] = df["priority"].astype(str).str.strip()
df["intent"] = df["intent"].astype(str).str.strip()
df["needs_reply"] = df["needs_reply"].astype(str).str.strip()
df = df[df["needs_reply"].isin(["Yes", "No"])].reset_index(drop=True)

label_map = {"No": 0, "Yes": 1}
inverse_label_map = {value: key for key, value in label_map.items()}

display(df[["email_text", "priority", "intent", "needs_reply"]].head())
display(df["needs_reply"].value_counts().to_frame("count"))
"""
        ),
        code(
            """
            X = df[["email_text", "priority", "intent"]].copy()
            y = df["needs_reply"].map(label_map)

            X_train, X_test, y_train, y_test = train_test_split(
                X,
                y,
                test_size=0.20,
                stratify=y,
                random_state=RANDOM_STATE,
            )

            cv = StratifiedKFold(
                n_splits=safe_n_splits(pd.Series(y_train), default=5),
                shuffle=True,
                random_state=RANDOM_STATE,
            )
            """
        ),
        code(
            """
            feature_builder = ColumnTransformer(
                transformers=[
                    (
                        "text",
                        TfidfVectorizer(
                            ngram_range=(1, 2),
                            min_df=2,
                            max_df=0.98,
                            sublinear_tf=True,
                            strip_accents="unicode",
                        ),
                        "email_text",
                    ),
                    (
                        "categorical",
                        Pipeline(
                            steps=[
                                ("imputer", SimpleImputer(strategy="most_frequent")),
                                ("onehot", OneHotEncoder(handle_unknown="ignore")),
                            ]
                        ),
                        ["priority", "intent"],
                    ),
                ]
            )

            logistic_pipeline = Pipeline(
                steps=[
                    ("features", feature_builder),
                    ("classifier", LogisticRegression(max_iter=4000, class_weight="balanced", random_state=RANDOM_STATE)),
                ]
            )

            negative_count = int((y_train == 0).sum())
            positive_count = int((y_train == 1).sum())
            scale_pos_weight = negative_count / max(positive_count, 1)

            xgb_pipeline = Pipeline(
                steps=[
                    ("features", feature_builder),
                    (
                        "classifier",
                        XGBClassifier(
                            objective="binary:logistic",
                            n_estimators=300,
                            max_depth=5,
                            learning_rate=0.08,
                            subsample=0.9,
                            colsample_bytree=0.8,
                            min_child_weight=2,
                            reg_lambda=1.0,
                            eval_metric="logloss",
                            scale_pos_weight=scale_pos_weight,
                            random_state=RANDOM_STATE,
                            n_jobs=4,
                            tree_method="hist",
                        ),
                    ),
                ]
            )

            models = {"Logistic Regression": logistic_pipeline, "XGBoost": xgb_pipeline}
            scoring = {
                "accuracy": "accuracy",
                "precision": "precision_macro",
                "recall": "recall_macro",
                "f1": "f1_macro",
            }

            cv_tables = []
            cv_scores = {}
            for name, model in models.items():
                scores = cross_validate(model, X_train, y_train, cv=cv, scoring=scoring, n_jobs=1)
                cv_tables.append(summarize_cv(scores, name))
                cv_scores[name] = scores["test_f1"].mean()

            cv_report = cv_tables[0]
            for table in cv_tables[1:]:
                cv_report = cv_report.merge(table, on="metric", how="outer")

            display(cv_report.round(4))
            best_model_name = max(cv_scores, key=cv_scores.get)
            best_model = models[best_model_name]
            print("Selected model:", best_model_name)
            """
        ),
        code(
            """
            best_model.fit(X_train, y_train)
            y_pred = best_model.predict(X_test)

            y_test_labels = pd.Series(y_test).map(inverse_label_map)
            y_pred_labels = pd.Series(y_pred).map(inverse_label_map)

            display(metrics_frame(y_test_labels, y_pred_labels, average="macro"))
            print(classification_report(y_test_labels, y_pred_labels, zero_division=0))
            confusion_df = plot_confusion(y_test_labels, y_pred_labels, labels=["No", "Yes"])
            display(confusion_df)
            """
        ),
        md(
            """
            ## Probability Scores and Explainability

            We inspect holdout probabilities for the positive class (`Yes`) and show feature importance from the selected classifier.
            """
        ),
        code(
            """
            probabilities = best_model.predict_proba(X_test)
            probability_table = X_test.copy()
            probability_table["actual"] = y_test_labels.values
            probability_table["predicted"] = y_pred_labels.values
            probability_table["probability_yes"] = probabilities[:, 1]
            display(probability_table.head(10))

            feature_names = best_model.named_steps["features"].get_feature_names_out()
            classifier = best_model.named_steps["classifier"]

            if best_model_name == "Logistic Regression":
                importance = pd.DataFrame(
                    {
                        "feature": feature_names,
                        "coefficient": classifier.coef_[0],
                        "abs_coefficient": np.abs(classifier.coef_[0]),
                    }
                ).sort_values("abs_coefficient", ascending=False)
                display(importance.head(25)[["feature", "coefficient"]])
            else:
                importance = pd.DataFrame({"feature": feature_names, "importance": classifier.feature_importances_})
                display(importance.sort_values("importance", ascending=False).head(25))
            """
        ),
        code(
            """
            model_path = MODELS_DIR / "needs_reply_pipeline.pkl"
            joblib.dump(best_model, model_path)
            print(f"Saved model to: {model_path}")
            """
        ),
        code(
            """
            sample_email = pd.DataFrame(
                {
                    "email_text": [normalize_text("Please review the payment issue and confirm whether we should respond to the customer today.")],
                    "priority": ["P1"],
                    "intent": ["Payment Reminder"],
                }
            )

            sample_prediction = pd.Series(best_model.predict(sample_email)).map(inverse_label_map)
            sample_probability = best_model.predict_proba(sample_email)[:, 1]

            sample_output = sample_email.copy()
            sample_output["predicted_needs_reply"] = sample_prediction.values
            sample_output["probability_yes"] = sample_probability
            display(sample_output)
            """
        ),
    ]
)


NOTEBOOKS = {
    "NB1_Final_Junk_Filter.ipynb": NB1,
    "NB2_Final_Priority_Classifier.ipynb": NB2,
    "NB3_Final_Intent_Classifier.ipynb": NB3,
    "NB4_Final_Needs_Reply_Predictor.ipynb": NB4,
}


def main() -> None:
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    for name, payload in NOTEBOOKS.items():
        target = NOTEBOOK_DIR / name
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Wrote {target}")


if __name__ == "__main__":
    main()
