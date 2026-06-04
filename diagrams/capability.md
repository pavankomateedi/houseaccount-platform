# HouseAccount — Capability Diagram

What the platform can do, grouped by domain. Bold = built in this week's MVP;
plain = on the roadmap (out of scope for the initial release per `DECISIONS.md`).

```mermaid
mindmap
  root((HouseAccount))
    Homeowner
      **Describe project via chat**
      **Submit web request**
      **Review quotes**
      **Accept & book**
      Photos & property profile
      Pay after completion
    Provider
      **Vetted + insured profile**
      **Service & coverage areas**
      **Quote within 2-hour window**
      Accept / decline jobs
      Invoice & collect
      Warranty follow-up
    Marketplace
      **Eligibility matching (service + coverage)**
      **Rank by rating**
      **Quote generation**
      **Booking lifecycle**
      Liquidity tracking
      AI-assisted ranking
    Message Intelligence
      **Classify intent (6 categories)**
      **Extract entities (service / timing / pricing)**
      **Sentiment & urgency**
      **Confidence scoring**
      **Dual-mode: Opus 4.8 + seeded mock**
      Multi-channel ingestion
    Workflow & Routing
      **Deterministic auto vs human-review**
      **Auto job creation (low-risk)**
      **Escalation with reason**
      Reminders & acknowledgements
      Invoice drafting
    Trust & Safety
      **Human-review queue**
      **Complaint & cancellation hold**
      Provider verification
      Fraud / off-platform monitoring
      $2,000 damage coverage
    Analytics & Ops
      **Aggregate insights dashboard**
      **Volume / sentiment / route / top services**
      **Complaint & human-review rates**
      Time-to-response & conversion
      City-by-city scaling
    Platform & Quality
      **FastAPI + React app**
      **Golden-set eval gate**
      **Domain-separated data model**
      **Offline / reproducible build**
      Security & compliance controls
```
