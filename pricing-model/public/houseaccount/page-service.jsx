// HouseAccount.AI — service detail page (PDP)
const AlsoLike = ({ s, nav }) => {
  const picks = [
    ...SERVICES.filter((x) => x.id !== s.id && x.category === s.category && x.providerId !== s.providerId),
    ...SERVICES.filter((x) => x.id !== s.id && x.providerId !== s.providerId && x.popular && x.category !== s.category),
    ...SERVICES.filter((x) => x.id !== s.id && x.providerId === s.providerId),
  ];
  const seen = new Set();
  const list = picks.filter((x) => (seen.has(x.id) ? false : seen.add(x.id))).slice(0, 4);
  if (!list.length) return null;
  return (
    <aside className="also-like">
      <h2>You may also like</h2>
      <div className="mini-list">
        {list.map((x) => {
          const xp = providerOf(x);
          return (
            <button key={x.id} className="mini-card" onClick={() => nav("service", { id: x.id })}>
              <CatTile category={x.category} size={62} radius={10} iconSize={26} />
              <span className="info">
                <strong>{x.name}</strong>
                <span className="by">{xp.name}</span>
                <span className="row">
                  <StarFill size={12} frac={1} /> {x.rating.toFixed(1)}
                  <span className="sep">·</span>
                  <PriceTag s={x} />
                </span>
              </span>
            </button>
          );
        })}
      </div>
    </aside>
  );
};

const PageService = ({ route, nav, addToCart, toast }) => {
  const s = SERVICES.find((x) => x.id === route.id);
  const [opt, setOpt] = React.useState(0);
  const [qty, setQty] = React.useState(1);
  const [addonOn, setAddonOn] = React.useState(false);
  const [addonOpen, setAddonOpen] = React.useState(false);
  React.useEffect(() => { setOpt(0); setQty(1); setAddonOn(false); setAddonOpen(false); }, [route.id]);

  if (!s) return <main className="ha-page"><div className="inner"><p style={{ padding: 40 }}>Service not found.</p></div></main>;
  const p = providerOf(s);
  const isCo = p.type === "company";
  const delta = s.options ? (s.options.choices[opt].delta || 0) : 0;
  const isQuote = s.priceModel === "quote";
  const unit = s.priceModel === "hourly" ? "/hr" : "";
  const addonCost = addonOn && s.addon ? s.addon.price : 0;
  const lineTotal = isQuote ? 0 : (s.price + delta) * qty + addonCost;
  const more = SERVICES.filter((x) => x.providerId === p.id && x.id !== s.id);
  const reviews = (REVIEWS[p.id] || []).slice(0, 2);

  return (
    <main className="ha-page service-detail">
      <div className="inner">
        <button className="crumb" onClick={() => nav("catalog")}><Icon name="arrowL" size={15} sw={2.2} /> All services</button>
        <div className="pdp three-col">
          <div className="media">
            <div className="main-shot">
              <CatTile category={s.category} iconSize={52} />
            </div>
            <div className="thumbs">
              {[1, 2].map((n) => (
                <div key={n} className="thumb-frame"><CatTile category={s.category} iconSize={24} /></div>
              ))}
            </div>
            <section className="includes">
              <h2>What's included</h2>
              <ul>
                {s.includes.map((it, i) => (
                  <li key={i}><Icon name="check" size={15} sw={2.6} /> {it}</li>
                ))}
              </ul>
            </section>
          </div>

          <div className="buy">
            <div className="byline">
              By <button className="link" onClick={() => nav("provider", { id: p.id })}>{p.name}</button>
              {p.badges.includes("verified") && <Icon name="shield" size={13} sw={2.2} style={{ color: "var(--green)", verticalAlign: "-2px" }} />}
              {s.sku && <span className="sku">/ Service#: <strong>{s.sku}</strong></span>}
            </div>
            <h1>{s.name}</h1>
            <div className="meta-line">
              <RatingLine rating={s.rating} count={s.reviewCount} size={15} />
              <span className="dot">·</span>
              <span className="muted"><Icon name="clock" size={14} sw={2} style={{ verticalAlign: "-2px" }} /> {s.time}</span>
            </div>
            <p className="blurb">{s.blurb}</p>

            <div className={"ha-panel prov-card " + (isCo ? "co" : "solo")} onClick={() => nav("provider", { id: p.id })}
              role="link" tabIndex={0} onKeyDown={(e) => e.key === "Enter" && nav("provider", { id: p.id })}>
              <Avatar provider={p} size={44} />
              <div className="who">
                <span className="kind-label">{isCo ? "Sold & serviced by" : "Your pro — does every job personally"}</span>
                <strong>{p.name} <Icon name="chevR" size={13} sw={2.4} style={{ verticalAlign: "-2px" }} /></strong>
                <span className="muted">
                  {isCo
                    ? `Team of ${p.team} · ${p.yearsInBusiness} yrs · ${p.jobsCompleted.toLocaleString()} jobs · ${p.guarantee}`
                    : `${p.yearsInBusiness} yrs experience · ${p.jobsCompleted.toLocaleString()} jobs · ${p.guarantee}`}
                </span>
                <span className="resp"><Icon name="bolt" size={12} sw={2} /> {p.responseTime}</span>
              </div>
              <div className="mini-badges">
                {p.badges.slice(0, 2).map((b) => <TrustBadge key={b} id={b} compact />)}
              </div>
            </div>

            <div className="ha-panel order-box">
              <div className="price-line">
                <PriceTag s={s.options ? { ...s, price: s.price + delta } : s} big />
                {!isQuote && <span className="muted">{s.priceModel === "hourly" ? s.time : "upfront, all-in price"}</span>}
                {isQuote && <span className="muted">free, no-obligation quote</span>}
              </div>
              {!isQuote && s.priceModel === "fixed" && s.price + delta >= 100 && (
                <div className="installments">
                  Pay in 4 interest-free installments of <strong>{fmt$(Math.ceil(((s.price + delta) * qty + addonCost) / 4))}</strong>
                  <span className="ha-pay">HA&nbsp;Pay</span>
                  <button className="link" onClick={(e) => { e.stopPropagation(); toast("HA Pay details (prototype)"); }}>Learn more</button>
                </div>
              )}

              {s.options && (
                <div className="opts">
                  <label>{s.options.label}</label>
                  <div className="opt-row">
                    {s.options.choices.map((c, i) => (
                      <button key={i} className={"opt" + (opt === i ? " on" : "")} onClick={() => setOpt(i)}>
                        {c.name}{c.delta ? <small>+{fmt$(c.delta)}</small> : null}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {s.addon && !isQuote && (
                <div className="addon-wrap">
                  <label className={"addon" + (addonOn ? " on" : "")}>
                    <input type="checkbox" checked={addonOn} onChange={(e) => setAddonOn(e.target.checked)} />
                    <span className="name">Add {s.addon.name}
                      <button className="link" onClick={(e) => { e.preventDefault(); e.stopPropagation(); setAddonOpen(!addonOpen); }}>
                        {addonOpen ? "Hide details" : "Show details"}
                      </button>
                    </span>
                    <span className="amt">{fmt$(s.addon.price)}</span>
                  </label>
                  {addonOpen && (
                    <p className="addon-details">Added to the same visit by the same pro — no extra trip fee. Remove it any time before the job is scheduled.</p>
                  )}
                </div>
              )}

              {!isQuote && (
                <div className="opts">
                  <label>{s.priceModel === "hourly" ? "Hours" : "Quantity"}</label>
                  <div className="qty">
                    <button onClick={() => setQty(Math.max(1, qty - 1))} aria-label="Decrease"><Icon name="minus" size={14} sw={2.4} /></button>
                    <span>{qty}</span>
                    <button onClick={() => setQty(qty + 1)} aria-label="Increase"><Icon name="plus" size={14} sw={2.4} /></button>
                  </div>
                </div>
              )}

              <button className="btn primary lg full" onClick={() => addToCart(s, { optionIndex: opt, qty })}>
                {isQuote ? "Request free quote" : `Add to cart — ${fmt$(lineTotal)}${unit}`}
              </button>
              {s.availability && (
                <div className={"avail " + (s.availability.tone || "ok")}>
                  <Icon name={s.availability.tone === "warn" ? "bolt" : "calendar"} size={14} sw={2.2} /> {s.availability.text}
                </div>
              )}
              <div className="assurance">
                <span><Icon name="shield" size={14} sw={2} /> {BADGE_LABELS[p.badges[0]].label}</span>
                <span><Icon name="check" size={14} sw={2.4} /> {p.guarantee}</span>
              </div>
            </div>

            {reviews.length > 0 && (
              <div className="pdp-reviews">
                <h2>Recent reviews <button className="link" onClick={() => nav("provider", { id: p.id })}>see all {p.reviewCount.toLocaleString()}</button></h2>
                {reviews.map((r, i) => <ReviewCard key={i} r={r} />)}
              </div>
            )}
          </div>

          <AlsoLike s={s} nav={nav} />
        </div>

        {more.length > 0 && (
          <section className="more-from">
            <h2>More from {p.name}</h2>
            <div className="rows">
              {more.map((x) => (
                <ServiceRow key={x.id} s={x} onOpen={(id) => nav("service", { id })} onAdd={(svc) => addToCart(svc)} />
              ))}
            </div>
          </section>
        )}
      </div>
    </main>
  );
};

window.PageService = PageService;
