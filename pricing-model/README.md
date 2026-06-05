# HouseAccount AI Pricing Model

An AI-powered pricing estimator for home service jobs that combines machine learning with rule-based confidence calibration.

## Quick Start (5 minutes)

### Backend Setup

```bash
cd pricing-model

# Create Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Train model
python model/train_model.py

# Run tests
pytest tests/test_model.py
```

### API Deployment

```bash
# Option 1: Local Netlify CLI
netlify dev

# Option 2: Deploy to Netlify
netlify deploy
```

API endpoint: `POST /.netlify/functions/pricing-estimate`

## Architecture

```
pricing-model/
├── data/
│   └── houseaccount_pricing_sample.csv (1,432 pricing records)
├── model/
│   ├── data_explorer.py              (EDA & baseline metrics)
│   ├── feature_extractor.py          (Feature engineering)
│   ├── train_model.py                (Ridge regression training)
│   ├── inference.py                  (Prediction server)
│   └── pricing_model.pkl             (Trained model)
├── functions/
│   └── pricing-estimate.js           (Netlify function / API endpoint)
├── tests/
│   └── test_model.py                 (Unit & integration tests)
└── netlify.toml                      (Netlify configuration)
```

### Model Pipeline

1. **Data Preparation** → Normalize pricing data
2. **Feature Extraction** → Scope signals from descriptions + categorical encodings
3. **Model Training** → Ridge regression on engineered features
4. **Confidence Calibration** → Base confidence × OOD penalties
5. **API Serving** → Netlify function endpoint

## API Contract

### Request

```bash
curl -X POST /.netlify/functions/pricing-estimate \
  -H "Authorization: Bearer $GAUNTLET_PRICING_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "abc123",
    "service_category": "Plumbing",
    "zip_code": "78704",
    "job_description": "Replace water heater",
    "deadline": "Within 1-2 weeks"
  }'
```

### Response

```json
{
  "ok": true,
  "job_id": "abc123",
  "estimate_lo": 1450,
  "estimate_hi": 2200,
  "estimate_midpoint": 1825,
  "confidence": 0.78,
  "model_version": "pavan-v1.0.0"
}
```

## Environment Variables

- `GAUNTLET_PRICING_SECRET` — Bearer token for API authentication

## Performance

- **Response time:** < 2 seconds (including inference)
- **MAPE (blended):** 11.54% (target: < 11.6%)
- **MAPE (real subset):** Tuned per spec

## Testing

```bash
# Run all tests
pytest tests/test_model.py -v

# Test specific class
pytest tests/test_model.py::TestModel -v

# With coverage
pytest tests/test_model.py --cov=model
```

Tests verify:
- ✓ Feature extraction
- ✓ Model training & MAPE
- ✓ Confidence calibration
- ✓ OOD detection (category, price, interval width)
- ✓ API contract (request validation, response schema)

## Files

- **README.md** — This file
- **MODELING_APPROACH.md** — Detailed modeling approach & assumptions
- **AI_USAGE.md** — AI tool usage for hiring signal
- **netlify.toml** — Netlify configuration
- **requirements.txt** — Python dependencies
- **package.json** — Node.js dependencies (for Netlify functions)
