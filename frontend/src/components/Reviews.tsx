import { Fragment, useEffect, useState } from "react";
import { api } from "../api";
import { sentimentClass, titleCase } from "../format";
import type { Provider, Review, Service } from "../types";

function Stars({ rating }: { rating: number }) {
  return (
    <span className="stars" aria-label={`${rating} out of 5`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i} className={i <= rating ? "star on" : "star off"}>
          ★
        </span>
      ))}
    </span>
  );
}

export function Reviews() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setError(null);
        const [r, p, s] = await Promise.all([api.reviews(), api.providers(), api.taxonomy()]);
        setReviews(r);
        setProviders(p);
        setServices(s);
      } catch {
        setError(
          "Could not reach the backend API. Start it from /backend with: " +
            "uvicorn houseaccount.api.app:app --port 8077",
        );
      }
    })();
  }, []);

  const providerName = (id: string) => providers.find((p) => p.id === id)?.name ?? id;
  const serviceLabel = (key: string) => services.find((s) => s.key === key)?.label ?? key;

  if (error)
    return (
      <div className="panel" style={{ borderLeft: "4px solid var(--red)" }}>
        <h3>Backend unavailable</h3>
        <p className="muted">{error}</p>
      </div>
    );

  if (reviews.length === 0) return <p className="muted">Loading reviews…</p>;

  const total = reviews.length;
  const avg = (reviews.reduce((a, r) => a + r.rating, 0) / total).toFixed(1);
  const bySent: Record<string, number> = { positive: 0, neutral: 0, negative: 0 };
  reviews.forEach((r) => (bySent[r.sentiment] += 1));
  const dist = [5, 4, 3, 2, 1].map((star) => ({
    star,
    n: reviews.filter((r) => r.rating === star).length,
  }));
  const pct = (n: number) => (total ? Math.round((n / total) * 100) : 0);
  let lastSentiment = "";

  return (
    <>
      <div className="reviews-summary">
        <div className="rs-score">
          <span className="big">{avg}</span>
          <Stars rating={Math.round(Number(avg))} />
          <div className="muted">{total} verified reviews</div>
        </div>

        <div className="rs-block">
          <h4>By sentiment</h4>
          {(["positive", "neutral", "negative"] as const).map((s) => (
            <div className="rs-row" key={s}>
              <span className="rs-label">{titleCase(s)}</span>
              <span className="rs-bar">
                <span className={`rs-fill ${s}`} style={{ width: `${pct(bySent[s])}%` }} />
              </span>
              <span className="rs-val">
                {bySent[s]} <span className="muted">({pct(bySent[s])}%)</span>
              </span>
            </div>
          ))}
        </div>

        <div className="rs-block">
          <h4>Rating distribution</h4>
          {dist.map((d) => (
            <div className="rs-row" key={d.star}>
              <span className="rs-label">{d.star}★</span>
              <span className="rs-bar">
                <span className="rs-fill star" style={{ width: `${pct(d.n)}%` }} />
              </span>
              <span className="rs-val">{d.n}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="reviews-list">
        {reviews.map((r) => {
          const showHeader = r.sentiment !== lastSentiment;
          lastSentiment = r.sentiment;
          return (
            <Fragment key={r.id}>
              {showHeader && (
                <h3 className={`review-section ${r.sentiment}`}>{titleCase(r.sentiment)}</h3>
              )}
              <div className={`review-card ${r.sentiment}`}>
                <div className="review-top">
                  <Stars rating={r.rating} />
                  <span className={sentimentClass(r.sentiment)}>{titleCase(r.sentiment)}</span>
                </div>
                <p className="review-text">“{r.text}”</p>
                <div className="review-meta">
                  <span className="rev-pro">{providerName(r.provider_id)}</span>
                  <span className="tag-chip">{serviceLabel(r.service_type)}</span>
                  <span className="muted" style={{ marginLeft: "auto" }}>
                    {r.homeowner_id}
                  </span>
                </div>
              </div>
            </Fragment>
          );
        })}
      </div>
    </>
  );
}
