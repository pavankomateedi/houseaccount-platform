import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import {
  categoryClass,
  pct,
  routeClass,
  sentimentClass,
  titleCase,
} from "../format";
import type { AggregateStats, InsightView } from "../types";
import { BarPanel } from "./BarPanel";
import { ConversationDrawer } from "./ConversationDrawer";

export function InsightsConsole() {
  const [views, setViews] = useState<InsightView[]>([]);
  const [stats, setStats] = useState<AggregateStats | null>(null);
  const [routeFilter, setRouteFilter] = useState("all");
  const [catFilter, setCatFilter] = useState("all");
  const [selected, setSelected] = useState<InsightView | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setError(null);
      const [v, s] = await Promise.all([api.insights(), api.stats()]);
      setViews(v);
      setStats(s);
    } catch {
      setError(
        "Could not reach the backend API. Start it from /backend with: " +
          "uvicorn houseaccount.api.app:app --port 8077",
      );
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const filtered = useMemo(
    () =>
      views.filter(
        (v) =>
          (routeFilter === "all" || v.insight.route === routeFilter) &&
          (catFilter === "all" || v.insight.classification.category === catFilter),
      ),
    [views, routeFilter, catFilter],
  );

  if (error)
    return (
      <div className="panel" style={{ borderLeft: "4px solid var(--red)" }}>
        <h3>Backend unavailable</h3>
        <p className="muted">{error}</p>
      </div>
    );

  if (!stats) return <p className="muted">Loading insights…</p>;

  return (
    <>
      <p className="console-intro">
        HouseAccount's view into every <strong>homeowner ↔ provider</strong> chat — turned
        into intent, sentiment, and the next action.
      </p>
      <div className="stat-grid">
        <div className="stat-card">
          <div className="num">{stats.total}</div>
          <div className="lbl">Conversations analyzed</div>
        </div>
        <div className="stat-card alert">
          <div className="num">{pct(stats.human_review_rate)}</div>
          <div className="lbl">Routed to human review</div>
        </div>
        <div className="stat-card alert">
          <div className="num">{pct(stats.complaint_rate)}</div>
          <div className="lbl">Complaints</div>
        </div>
        <div className="stat-card">
          <div className="num">{stats.avg_confidence.toFixed(2)}</div>
          <div className="lbl">Avg engine confidence</div>
        </div>
      </div>

      <div className="panel-grid">
        <BarPanel
          title="Volume by category"
          data={stats.by_category}
          order={[
            "new_request",
            "pricing_question",
            "follow_up",
            "reschedule",
            "cancellation",
            "complaint",
          ]}
          variant={(k) => (k === "complaint" ? "negative" : "")}
        />
        <BarPanel
          title="Routing (auto vs human review)"
          data={stats.by_route}
          variant={(k) => (k === "human_review" ? "review" : "")}
        />
        <BarPanel
          title="Sentiment"
          data={stats.by_sentiment}
          order={["positive", "neutral", "negative"]}
          variant={(k) => (k === "negative" ? "negative" : "")}
        />
        <BarPanel title="Top services" data={stats.top_services} />
      </div>

      <div className="toolbar">
        <label className="muted">Route</label>
        <select value={routeFilter} onChange={(e) => setRouteFilter(e.target.value)}>
          <option value="all">All</option>
          <option value="human_review">Human review</option>
          <option value="auto">Auto</option>
        </select>
        <label className="muted">Category</label>
        <select value={catFilter} onChange={(e) => setCatFilter(e.target.value)}>
          <option value="all">All</option>
          {Object.keys(stats.by_category).map((c) => (
            <option key={c} value={c}>
              {titleCase(c)}
            </option>
          ))}
        </select>
        <span className="count">{filtered.length} conversations</span>
      </div>

      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Category</th>
            <th>Service</th>
            <th>Sentiment</th>
            <th>Urgency</th>
            <th>Route</th>
            <th>Action</th>
            <th>Conf.</th>
          </tr>
        </thead>
        <tbody>
          {filtered.map((v) => {
            const c = v.insight.classification;
            return (
              <tr key={v.conversation.id} onClick={() => setSelected(v)}>
                <td>{v.conversation.id}</td>
                <td>
                  <span className={categoryClass(c.category)}>{titleCase(c.category)}</span>
                </td>
                <td>{c.entities.service_type ?? "—"}</td>
                <td>
                  <span className={sentimentClass(c.sentiment)}>{titleCase(c.sentiment)}</span>
                </td>
                <td>{titleCase(c.entities.urgency)}</td>
                <td>
                  <span className={routeClass(v.insight.route)}>{titleCase(v.insight.route)}</span>
                </td>
                <td>{titleCase(v.insight.action)}</td>
                <td className="conf">{c.confidence.toFixed(2)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {selected && (
        <ConversationDrawer
          view={selected}
          onClose={() => setSelected(null)}
          onApplied={() => void load()}
        />
      )}
    </>
  );
}
