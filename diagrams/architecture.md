# HouseAccount — Architecture Diagram

End-to-end architecture of the trust-first marketplace plus the
message-intelligence engine. Mirrors the built system 1:1 (FastAPI backend +
React frontend, dual-mode Claude Opus / seeded mock, deterministic routing).

```mermaid
flowchart TB
    subgraph Channels["Customer channels"]
        SMS["Text / SMS chat<br/>(homeowner ↔ platform)"]
        WEB["Web request form<br/>(+ photos)"]
    end

    subgraph FE["Frontend — React + Vite (TS)"]
        IC["Insights Console<br/>aggregate + triage queue"]
        CD["Conversation drill-down<br/>chat ⟷ extracted insight"]
        MP["Marketplace UI<br/>request → quote → book"]
    end

    subgraph API["API — FastAPI"]
        EP["/api/insights · /api/eval<br/>/api/requests · /api/quotes · /api/bookings/"]
    end

    subgraph ENGINE["Message-Intelligence Engine"]
        direction TB
        CLS{"Classifier (dual-mode)"}
        OPUS["Claude Opus 4.8<br/>(live, structured tool-call,<br/>prompt-cached system)"]
        MOCK["Seeded heuristic<br/>(mock — offline / CI)"]
        EXTRACT["Category · entities · sentiment ·<br/>urgency · confidence"]
        ROUTER["Deterministic router<br/>(auditable rules)"]
        INSIGHT["Insight<br/>route + action + reason"]
        CLS --> OPUS
        CLS --> MOCK
        OPUS --> EXTRACT
        MOCK --> EXTRACT
        EXTRACT --> ROUTER --> INSIGHT
    end

    subgraph MARKET["Marketplace Core"]
        REQ["Service requests"]
        MATCH["Matching<br/>eligibility (service+coverage)<br/>then rank by rating"]
        QUOTE["Quotes<br/>(2-hour window)"]
        BOOK["Bookings<br/>(pay after completion)"]
        PROV["Vetted + insured providers"]
        REQ --> MATCH --> QUOTE --> BOOK
        PROV --> MATCH
    end

    HUMAN["Human-review queue<br/>(trust & safety:<br/>complaints, cancellations,<br/>negative, urgent, low-confidence)"]

    subgraph EVAL["Eval harness (offline)"]
        GOLD["Golden set (25)"]
        THRESH["Thresholds:<br/>category F1≥.85 · route≥.90<br/>entities≥.80 · sentiment≥.80"]
        GOLD --> THRESH
    end

    subgraph DATA["Domain-separated stores"]
        DM["Marketplace data"]
        DC["Communications data"]
        DA["Analytics / insights"]
    end

    SMS --> EP
    WEB --> EP
    IC --> EP
    CD --> EP
    MP --> EP
    EP --> CLS
    EP --> REQ
    INSIGHT -->|"auto · create_job"| REQ
    INSIGHT -->|"escalate / hold"| HUMAN
    INSIGHT --> DA
    REQ --- DM
    SMS --- DC
    ENGINE -.measured by.-> EVAL

    classDef eng fill:#e6f7f5,stroke:#0b7d7d,color:#0f2742;
    classDef mkt fill:#e7eef6,stroke:#1c3a5e,color:#0f2742;
    classDef risk fill:#fae3e1,stroke:#d2544b,color:#0f2742;
    class ENGINE,CLS,OPUS,MOCK,EXTRACT,ROUTER,INSIGHT eng;
    class MARKET,REQ,MATCH,QUOTE,BOOK,PROV mkt;
    class HUMAN risk;
```

## Key flows

1. **Chat → insight → action.** A customer text is classified (Opus or mock),
   entities/sentiment/urgency extracted, then a *deterministic* router decides
   `auto` vs `human_review` and the action. Low-risk new requests auto-create a
   marketplace job; everything risky is held for a human.
2. **Marketplace.** Requests match to vetted, insured providers by eligibility
   then rating; providers quote within a 2-hour window; the homeowner accepts a
   quote to create a booking; payment is after completion.
3. **Measured quality.** The engine is gated by an offline eval against a
   hand-verified golden set — the quality claim is a number, not an assertion.
