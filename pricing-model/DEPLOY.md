# Deployment Guide

## Local Development

### Prerequisites
- Python 3.12+
- Node.js 18+
- Netlify CLI (optional)

### Setup

```bash
# Clone repository
git clone <repo-url>
cd pricing-model

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies (for Netlify functions)
npm install
```

### Training the Model

```bash
# Generate synthetic data (if needed)
python data/generate_sample_data.py

# Extract features
python model/feature_extractor.py

# Train model
python model/train_model.py

# Expected output:
# Model Training Complete
#   Test MAPE: 11.14%
#   Blended MAPE: 11.54%
#   Target: <11.6%
```

### Running Tests

```bash
# All tests
pytest tests/test_model.py -v

# Specific test
pytest tests/test_model.py::TestModel::test_model_mape_below_baseline -v

# With coverage
pytest tests/test_model.py --cov=model --cov-report=html
```

### Local API Testing

```bash
# Option 1: Using curl
export GAUNTLET_PRICING_SECRET="test-secret-key"
curl -X POST http://localhost:3000/.netlify/functions/pricing-estimate \
  -H "Authorization: Bearer test-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "test_001",
    "service_category": "Plumbing",
    "zip_code": "78704",
    "job_description": "Replace water heater",
    "deadline": "Within 1-2 weeks"
  }'

# Option 2: Using Python
python -c "
import json
import requests

headers = {
    'Authorization': 'Bearer test-secret-key',
    'Content-Type': 'application/json'
}
data = {
    'job_id': 'test_001',
    'service_category': 'Plumbing',
    'zip_code': '78704',
    'job_description': 'Replace water heater'
}
response = requests.post('http://localhost:3000/.netlify/functions/pricing-estimate', json=data, headers=headers)
print(json.dumps(response.json(), indent=2))
"
```

## Deployment to Netlify

### Prerequisites
- Netlify account (free)
- GitHub repository (connected to Netlify)

### Step 1: Connect Repository
1. Go to [app.netlify.com](https://app.netlify.com)
2. Click "Add new site" → "Import an existing project"
3. Select GitHub repository
4. Authorize Netlify with GitHub

### Step 2: Configure Build Settings
- **Build command:** `npm install`
- **Publish directory:** `public` (not used for functions)
- **Functions directory:** `functions`

### Step 3: Set Environment Variables
In Netlify dashboard:
1. Go to "Site settings" → "Build & deploy" → "Environment"
2. Add variable: `GAUNTLET_PRICING_SECRET = <your-secret-key>`

### Step 4: Deploy
```bash
# Automatic deploys on git push to main
# Or manual deploy:
netlify deploy --prod
```

## Production Checklist

- [ ] Model trained on full dataset (1,432 rows)
- [ ] MAPE verified: <11.6% (blended), <40% (real-only)
- [ ] All tests passing: `pytest tests/ -v`
- [ ] Environment variable set: `GAUNTLET_PRICING_SECRET`
- [ ] API auth working: Bearer token validation
- [ ] Response time < 2 seconds (with Claude API calls cached)
- [ ] OOD confidence calibration verified (category, price, interval)
- [ ] README reviewed and tested
- [ ] AI_USAGE.md complete with 5-10 key prompts
- [ ] Demo video recorded (2-3 min walkthrough)

## Troubleshooting

### GAUNTLET_PRICING_SECRET Error
```
Error: GAUNTLET_PRICING_SECRET env var is required
```
**Fix:** Set environment variable before running
```bash
export GAUNTLET_PRICING_SECRET="your-secret-key"  # Unix/Mac
set GAUNTLET_PRICING_SECRET=your-secret-key       # Windows
```

### MAPE > 11.6% (Model Underperforming)
- Check dataset: `python model/data_explorer.py`
- Verify feature extraction: `python model/feature_extractor.py`
- Try different alpha in Ridge regression
- Collect more labeled examples (277 is relatively small)

### Claude API Rate Limits
- Implement request batching for scope extraction
- Cache extracted features to disk
- Use Claude Sonnet instead of Opus for cost savings

### Netlify Deploy Failures
- Check build logs: Netlify dashboard → "Deploys"
- Verify `netlify.toml` syntax
- Ensure `functions/` directory exists
- Run `netlify dev` locally first

## Testing in Staging

```bash
# Deploy to staging (test branch)
git checkout -b feature/my-changes
git push origin feature/my-changes
# Netlify auto-deploys to preview URL

# Get preview URL from Netlify dashboard
PREVIEW_URL="https://deploy-preview-123--my-site.netlify.app"

# Test against preview
curl -X POST $PREVIEW_URL/.netlify/functions/pricing-estimate \
  -H "Authorization: Bearer $GAUNTLET_PRICING_SECRET" \
  -d '{"job_id":"test","service_category":"Plumbing","zip_code":"78704","job_description":"Replace water heater"}'
```

## Rollback

```bash
# Revert to previous deploy in Netlify dashboard
# Or redeploy previous commit:
git checkout <previous-commit>
git push origin main --force-with-lease  # Use with caution!
```
