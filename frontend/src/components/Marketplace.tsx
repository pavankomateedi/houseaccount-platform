import { useEffect, useState } from "react";
import { api } from "../api";
import { titleCase } from "../format";
import type { Booking, Provider, Quote, Service, ServiceRequest } from "../types";

export function Marketplace() {
  const [taxonomy, setTaxonomy] = useState<Service[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [requests, setRequests] = useState<ServiceRequest[]>([]);
  const [serviceType, setServiceType] = useState("handyman");
  const [zip, setZip] = useState("94110");
  const [timing, setTiming] = useState("this Saturday morning");
  const [quotes, setQuotes] = useState<Record<string, Quote[]>>({});
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      setError(null);
      const [t, p, r, b] = await Promise.all([
        api.taxonomy(),
        api.providers(),
        api.requests(),
        api.bookings(),
      ]);
      setTaxonomy(t);
      setProviders(p);
      setRequests(r);
      setBookings(b);
    } catch {
      setError(
        "Could not reach the backend API. Start it from /backend with: " +
          "uvicorn houseaccount.api.app:app --port 8077",
      );
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function createRequest() {
    await api.createRequest({ homeowner_id: "ho-web", service_type: serviceType, zip_code: zip, timing });
    await refresh();
  }

  async function getQuotes(reqId: string) {
    const qs = await api.makeQuotes(reqId);
    setQuotes((prev) => ({ ...prev, [reqId]: qs }));
    await refresh();
  }

  async function accept(q: Quote) {
    await api.acceptQuote(q.id, timing);
    setQuotes((prev) => ({ ...prev, [q.request_id]: [] }));
    await refresh();
  }

  const providerName = (id: string) => providers.find((p) => p.id === id)?.name ?? id;

  if (error)
    return (
      <div className="panel" style={{ borderLeft: "4px solid var(--red)" }}>
        <h3>Backend unavailable</h3>
        <p className="muted">{error}</p>
      </div>
    );

  return (
    <div className="panel-grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
      <div>
        <div className="panel">
          <h3>Request a service (homeowner)</h3>
          <div className="form">
            <label className="full">
              Service
              <select value={serviceType} onChange={(e) => setServiceType(e.target.value)}>
                {taxonomy.map((s) => (
                  <option key={s.key} value={s.key}>
                    {s.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              ZIP
              <input value={zip} onChange={(e) => setZip(e.target.value)} />
            </label>
            <label>
              Timing
              <input value={timing} onChange={(e) => setTiming(e.target.value)} />
            </label>
          </div>
          <button className="btn" style={{ marginTop: 14 }} onClick={createRequest}>
            Submit request
          </button>
          <div className="feature-chips">
            <span className="feature-chip">
              <span className="fc-ic">🛡️</span> Vetted &amp; insured pros
            </span>
            <span className="feature-chip">
              <span className="fc-ic">⏱️</span> Quotes in 2 hours
            </span>
            <span className="feature-chip">
              <span className="fc-ic">✅</span> Pay after completion
            </span>
            <span className="feature-chip">
              <span className="fc-ic">💰</span> Lowest-price guarantee
            </span>
          </div>
        </div>

        <div className="panel" style={{ marginTop: 16 }}>
          <h3>Vetted providers ({providers.length})</h3>
          {providers.map((p) => (
            <div className="provider-row" key={p.id}>
              <span className="nm">{p.name}</span>
              <span className="star">★ {p.rating.toFixed(1)}</span>
              <span className="muted">{p.jobs_done} jobs</span>
              {p.insured && <span className="tag-chip">insured</span>}
            </div>
          ))}
        </div>
      </div>

      <div>
        <div className="panel">
          <h3>Requests ({requests.length})</h3>
          {requests.length === 0 && <p className="muted">No requests yet.</p>}
          {requests.map((r) => (
            <div key={r.id} style={{ borderBottom: "1px solid var(--line)", padding: "10px 0" }}>
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <b>{r.id}</b>
                <span className="tag-chip">{r.service_type}</span>
                <span className="muted">ZIP {r.zip_code}</span>
                {r.source === "chat" && <span className="status status-chat">from chat</span>}
                <span className="muted" style={{ marginLeft: "auto" }}>
                  {titleCase(r.status)}
                </span>
              </div>
              {(quotes[r.id]?.length ?? 0) === 0 ? (
                <button className="btn secondary" style={{ marginTop: 8 }} onClick={() => getQuotes(r.id)}>
                  Get quotes
                </button>
              ) : (
                quotes[r.id].map((q) => (
                  <div className="quote-card" key={q.id}>
                    <span className="amt">${q.amount.toFixed(0)}</span>
                    <div>
                      <div style={{ fontWeight: 600 }}>{providerName(q.provider_id)}</div>
                      <div className="muted">{q.quote_window_hours}-hour quote window</div>
                    </div>
                    <button className="btn" style={{ marginLeft: "auto", width: "auto" }} onClick={() => accept(q)}>
                      Accept
                    </button>
                  </div>
                ))
              )}
            </div>
          ))}
        </div>

        {bookings.length > 0 && (
          <div className="panel" style={{ marginTop: 16 }}>
            <h3>Bookings ({bookings.length})</h3>
            {bookings.map((b) => (
              <div className="provider-row" key={b.id}>
                <span className="nm">{b.id}</span>
                <span className="muted">{providerName(b.provider_id)}</span>
                <span className="tag-chip">{b.scheduled_time ?? "TBD"}</span>
                <span className="status status-chat" style={{ marginLeft: "auto" }}>
                  {b.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
