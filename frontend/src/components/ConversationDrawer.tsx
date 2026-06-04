import { useState } from "react";
import { api } from "../api";
import { categoryClass, routeClass, sentimentClass, titleCase } from "../format";
import type { ApplyResult, InsightView } from "../types";

interface Props {
  view: InsightView;
  onClose: () => void;
  onApplied: () => void;
}

export function ConversationDrawer({ view, onClose, onApplied }: Props) {
  const { conversation, insight } = view;
  const c = insight.classification;
  const [result, setResult] = useState<ApplyResult | null>(null);
  const [busy, setBusy] = useState(false);

  const canAutoApply =
    insight.route === "auto" &&
    insight.action === "create_job" &&
    c.entities.service_type !== null;

  async function apply() {
    setBusy(true);
    try {
      const r = await api.applyInsight(conversation.id);
      setResult(r);
      onApplied();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-head">
          <div>
            <div style={{ fontWeight: 700 }}>
              Homeowner {conversation.homeowner_id}
              {conversation.provider_name && (
                <> ↔ {conversation.provider_name}</>
              )}
            </div>
            <div style={{ fontSize: 12, color: "#9fb3c8" }}>
              {conversation.id} · ZIP {conversation.zip_code} · 👁 HouseAccount visibility
            </div>
          </div>
          <button className="x" onClick={onClose} aria-label="close">
            ×
          </button>
        </div>

        <div className="drawer-body">
          <div className="chat">
            {conversation.messages.map((m, i) => (
              <div className={`bubble ${m.sender}`} key={i}>
                <div className="who">
                  {m.sender === "homeowner"
                    ? "Homeowner"
                    : conversation.provider_name ?? "Service provider"}
                </div>
                {m.text}
              </div>
            ))}
          </div>
          <p className="oversight-note">
            👁 HouseAccount has full visibility into this homeowner ↔ provider chat.
            The engine reads every thread and recommends the action on the right.
          </p>

          <div className="extract">
            <h4>Engine extraction</h4>
            <div className="kv">
              <span className="k">Category</span>
              <span className="v">
                <span className={categoryClass(c.category)}>{titleCase(c.category)}</span>
              </span>
            </div>
            <div className="kv">
              <span className="k">Service</span>
              <span className="v">{c.entities.service_type ?? "—"}</span>
            </div>
            <div className="kv">
              <span className="k">Timing</span>
              <span className="v">{c.entities.timing ?? "—"}</span>
            </div>
            <div className="kv">
              <span className="k">Urgency</span>
              <span className="v">{titleCase(c.entities.urgency)}</span>
            </div>
            <div className="kv">
              <span className="k">Pricing ref</span>
              <span className="v">{c.entities.pricing_ref ?? "—"}</span>
            </div>
            <div className="kv">
              <span className="k">Sentiment</span>
              <span className="v">
                <span className={sentimentClass(c.sentiment)}>{titleCase(c.sentiment)}</span>
              </span>
            </div>
            <div className="kv">
              <span className="k">Confidence</span>
              <span className="v conf">{c.confidence.toFixed(2)}</span>
            </div>
            <div className="kv">
              <span className="k">Route</span>
              <span className="v">
                <span className={routeClass(insight.route)}>{titleCase(insight.route)}</span>
              </span>
            </div>
            <div className="kv">
              <span className="k">Action</span>
              <span className="v">{titleCase(insight.action)}</span>
            </div>
            {insight.escalation_reason && (
              <div className="kv">
                <span className="k">Reason</span>
                <span className="v">{titleCase(insight.escalation_reason)}</span>
              </div>
            )}

            {canAutoApply && !result && (
              <button className="apply-btn" onClick={apply} disabled={busy}>
                {busy ? "Applying…" : "Apply → create job"}
              </button>
            )}
            {!canAutoApply && !result && insight.route === "human_review" && (
              <p className="apply-note">
                Held for a human — {titleCase(insight.escalation_reason ?? "review")}.
                No auto-action taken.
              </p>
            )}
            {!canAutoApply && !result && insight.route === "auto" && (
              <p className="apply-note">
                Auto-routed. Action “{titleCase(insight.action)}” is handled
                downstream — no new job to create here.
              </p>
            )}
            {result && <p className="apply-note">{result.message}</p>}
            {result?.created_request_id && (
              <p className="apply-note">
                Created request <b>{result.created_request_id}</b>.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
