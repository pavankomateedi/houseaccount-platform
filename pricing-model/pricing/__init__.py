"""HouseAccount AI pricing model — domain, data, and modeling layers.

Layering (Clean Architecture):
- metrics, calibration  -> domain (pure rules, no I/O)
- data                  -> adapter (CSV in, normalized frame out)
- features, model       -> application/infra (feature engineering + sklearn)

The Netlify endpoint (functions/) is a separate presentation layer that consumes
the exported model.json; it does not import this package at request time.
"""
