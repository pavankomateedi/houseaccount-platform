// HouseAccount.AI — catalog / browse page
const PageCatalog = ({ route, nav, query, addToCart }) => {
  const tab = route.tab === "providers" ? "providers" : "services";
  const [cat, setCat] = React.useState(route.cat || "all");
  const [who, setWho] = React.useState("all"); // all | company | individual
  const [price, setPrice] = React.useState("all"); // all | fixed | quote

  const q = query.trim().toLowerCase();

  const services = SERVICES.filter((s) => {
    const p = providerOf(s);
    if (cat !== "all" && s.category !== cat) return false;
    if (who !== "all" && p.type !== who) return false;
    if (price === "fixed" && s.priceModel === "quote") return false;
    if (price === "quote" && s.priceModel !== "quote") return false;
    if (q && !(s.name + " " + s.blurb + " " + catName(s.category) + " " + p.name).toLowerCase().includes(q)) return false;
    return true;
  });

  const providers = PROVIDERS.filter((p) => {
    if (who !== "all" && p.type !== who) return false;
    const cats = SERVICES.filter((s) => s.providerId === p.id);
    if (cat !== "all" && !cats.some((s) => s.category === cat)) return false;
    if (q && !(p.name + " " + p.tagline + " " + cats.map((s) => s.name).join(" ")).toLowerCase().includes(q)) return false;
    return true;
  });

  const setTab = (t) => nav("catalog", { tab: t === "providers" ? "providers" : undefined });

  return (
    <main className="ha-page catalog">
      <section className="hero">
        <div className="inner">
          <h1>Every fix, one account.</h1>
          <p>Book trusted companies and independent pros for repairs, upgrades, and everything your home throws at you — upfront prices, real reviews.</p>
          <div className="trust-strip">
            <span><Icon name="shield" size={15} sw={2} /> Verified & background-checked pros</span>
            <span><Icon name="check" size={15} sw={2.4} /> Upfront pricing — or a free quote</span>
            <span><Icon name="bolt" size={15} sw={2} /> Most pros reply within an hour</span>
          </div>
        </div>
      </section>

      <div className="inner">
        <div className="toolbar">
          <div className="tabs" role="tablist">
            <button role="tab" aria-selected={tab === "services"} className={tab === "services" ? "on" : ""} onClick={() => setTab("services")}>
              Services <span className="n">{services.length}</span>
            </button>
            <button role="tab" aria-selected={tab === "providers"} className={tab === "providers" ? "on" : ""} onClick={() => setTab("providers")}>
              Providers <span className="n">{providers.length}</span>
            </button>
          </div>
          <div className="filters">
            <div className="seg" role="group" aria-label="Provider type">
              {[["all", "All pros"], ["company", "Companies"], ["individual", "Individuals"]].map(([v, l]) => (
                <button key={v} className={who === v ? "on" : ""} onClick={() => setWho(v)}>{l}</button>
              ))}
            </div>
            {tab === "services" && (
              <div className="seg" role="group" aria-label="Pricing">
                {[["all", "Any price"], ["fixed", "Upfront price"], ["quote", "Quote-based"]].map(([v, l]) => (
                  <button key={v} className={price === v ? "on" : ""} onClick={() => setPrice(v)}>{l}</button>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="cats" role="group" aria-label="Categories">
          <button className={"cat-chip" + (cat === "all" ? " on" : "")} onClick={() => setCat("all")}>All</button>
          {CATEGORIES.map((c) => (
            <button key={c.id} className={"cat-chip" + (cat === c.id ? " on" : "")} onClick={() => setCat(c.id)}>
              <Icon name={c.id} size={15} sw={1.9} />{c.name}
            </button>
          ))}
        </div>

        {tab === "services" ? (
          services.length ? (
            <div className="grid services">
              {services.map((s) => (
                <ServiceCard key={s.id} s={s} onOpen={(id) => nav("service", { id })} onOpenProvider={(id) => nav("provider", { id })} />
              ))}
            </div>
          ) : (
            <div className="no-results">
              <p>No services match — try clearing a filter.</p>
              <button className="btn ghost" onClick={() => { setCat("all"); setWho("all"); setPrice("all"); }}>Clear filters</button>
            </div>
          )
        ) : providers.length ? (
          <div className="grid providers">
            {providers.map((p) => (
              <ProviderCard key={p.id} p={p} onOpen={(id) => nav("provider", { id })} />
            ))}
          </div>
        ) : (
          <div className="no-results">
            <p>No providers match — try clearing a filter.</p>
            <button className="btn ghost" onClick={() => { setCat("all"); setWho("all"); }}>Clear filters</button>
          </div>
        )}
      </div>
    </main>
  );
};

window.PageCatalog = PageCatalog;
