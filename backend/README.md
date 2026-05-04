# REPLYNT FastAPI Backend

Production-ready FastAPI backend for REPLYNT email analysis.

## Features

- FastAPI app with modular structure
- Startup loading for all saved ML pipelines using `joblib`
- `POST /analyze-email` endpoint for email classification
- `GET /health` endpoint for service health and model readiness
- CORS enabled for frontend integration
- Version-pinned dependencies for model compatibility

## Project Structure

```text
backend/
|-- app/
|   |-- api/routes/email.py
|   |-- core/config.py
|   |-- core/logging.py
|   |-- models/schemas.py
|   |-- services/model_service.py
|   |-- utils/text.py
|   `-- main.py
|-- requirements.txt
|-- sample_requests.http
`-- README.md
```

## Install

```bash
cd C:/Users/mbmeg/Desktop/replynt_final/backend
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
```

## Run The API

```bash
cd C:/Users/mbmeg/Desktop/replynt_final/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open the docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## API Endpoints

### GET /health

Returns service status and whether all models were loaded successfully.

### POST /analyze-email

Request body:

```json
{
  "subject": "Invoice overdue",
  "body": "Please clear the payment by Friday to avoid service interruption."
}
```

Example response:

```json
{
  "junk": false,
  "priority": "P1",
  "intent": "Payment Reminder",
  "needs_reply": true,
  "confidence_scores": {
    "junk": {
      "junk": 0.0123,
      "relevant": 0.9877
    },
    "priority": {
      "P1": 0.9012,
      "P2": 0.0711,
      "P3": 0.0277
    },
    "intent": {},
    "needs_reply": {
      "No": 0.0834,
      "Yes": 0.9166
    }
  },
  "reasons": [
    "Priority predicted as P1.",
    "Intent predicted as Payment Reminder.",
    "Financial language detected in the email content.",
    "Deadline or urgency language detected in the email content.",
    "The combined signals indicate a reply is likely needed."
  ]
}
```

Note: the intent model is a `LinearSVC`, so it does not expose `predict_proba`; its confidence block will remain empty unless the model is retrained with a probabilistic estimator.

## CORS Configuration

By default, CORS allows all origins. To restrict it, create a `.env` file inside `backend/`:

```env
CORS_ALLOW_ORIGINS=["http://localhost:3000", "http://127.0.0.1:5173"]
```

## Sample cURL Requests

```bash
curl http://127.0.0.1:8000/health
```

```bash
curl -X POST http://127.0.0.1:8000/analyze-email ^
  -H "Content-Type: application/json" ^
  -d "{"subject":"Invoice overdue","body":"Please clear the payment by Friday to avoid service interruption."}"
```
