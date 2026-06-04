import { useEffect, useState } from "react";
import { api } from "./api";
import { InsightsConsole } from "./components/InsightsConsole";
import { Marketplace } from "./components/Marketplace";
import { Reviews } from "./components/Reviews";

type Tab = "insights" | "marketplace" | "reviews";

const STATUS_LABEL: Record<string, string> = {
  mock: "Demo data",
  live: "Live",
  offline: "Offline",
  "…": "Connecting…",
};

export function App() {
  const [tab, setTab] = useState<Tab>("insights");
  const [mode, setMode] = useState<string>("…");

  useEffect(() => {
    api
      .health()
      .then((h) => setMode(h.mode))
      .catch(() => setMode("offline"));
  }, []);

  return (
    <>
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path
                d="M3 11.5 12 4l9 7.5M5.5 10v9h13v-9M9.5 19v-5h5v5"
                stroke="#fff"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </span>
          <div>
            <div className="logo">
              House<span>Account</span>
            </div>
            <div className="tagline">Visibility into every homeowner ↔ provider chat · turned into action</div>
          </div>
        </div>
        <div className="spacer" />
        <div className="mode-pill">{STATUS_LABEL[mode] ?? mode}</div>
      </header>
      <nav className="tabs">
        <button className={`tab ${tab === "insights" ? "active" : ""}`} onClick={() => setTab("insights")}>
          Insights Console
        </button>
        <button
          className={`tab ${tab === "marketplace" ? "active" : ""}`}
          onClick={() => setTab("marketplace")}
        >
          Marketplace
        </button>
        <button
          className={`tab ${tab === "reviews" ? "active" : ""}`}
          onClick={() => setTab("reviews")}
        >
          Ratings &amp; Reviews
        </button>
      </nav>
      <main>
        {tab === "insights" && <InsightsConsole />}
        {tab === "marketplace" && <Marketplace />}
        {tab === "reviews" && <Reviews />}
      </main>
    </>
  );
}
