// HouseAccount.AI — provider profile pages (company storefront vs individual pro)
const ProviderTrustCard = ({ p, onMessage }) => (
  <div className="ha-panel trust-card">
    <h3>Why you can trust {p.type === "company" ? "them" : p.name.split(" ")[0]}</h3>
    <ul className="trust-list">
      {p.badges.map((b) => (
        <li key={b}>
          <Icon name="shield" size={16} sw={2} />
          <div><strong>{BADGE_LABELS[b].label}</strong><span>{BADGE_LABELS[b].desc}</span></div>
        </li>
      ))}
      <li><Icon name="check" size={16} sw={2.4} /><div><strong>{p.guarantee}</strong><span>Backed by HouseAccount if anything goes wrong</span></div></li>
    </ul>
    <div className="facts">
      <div><Icon name="bolt" size={15} sw={2} /> {p.responseTime}</div>
      <div><Icon name="pin" size={15} sw={2} /> {p.serviceArea}</div>
      <div><Icon name="calendar" size={15} sw={2} /> {p.hours}</div>
      {p.team && <div><Icon name="user" size={15} sw={2} /> Team of {p.team}</div>}
    </div>
    <button className="btn ghost full" onClick={onMessage}><Icon name="message" size={16} sw={2} /> Message {p.type === "company" ? "the team" : p.name.split(" ")[0]}</button>
  </div>
);

const ProviderServices = ({ p, nav, addToCart }) => {
  const svcs = SERVICES.filter((s) => s.providerId === p.id);
  const cats = [...new Set(svcs.map((s) => s.category))];
  return (
    <section className="prov-services">
      <h2>Services & pricing <span className="muted">— the menu</span></h2>
      {cats.map((c) => (
        <div key={c} className="cat-group">
          <div className="cat-head"><Icon name={c} size={16} sw={1.9} /> {catName(c)}</div>
          {svcs.filter((s) => s.category === c).map((s) => (
            <ServiceRow key={s.id} s={s} onOpen={(id) => nav("service", { id })} onAdd={addToCart} />
          ))}
        </div>
      ))}
    </section>
  );
};

const ProviderGallery = ({ p }) => (
  <section className="prov-gallery">
    <h2>Recent work</h2>
    <div className="gal-grid">
      {[1, 2, 3, 4].map((n) => (
        <image-slot key={n} id={`${p.id}-work-${n}`} shape="rounded" radius="12"
          placeholder={`Drop a photo of ${p.type === "company" ? p.name + "'s" : p.name.split(" ")[0] + "'s"} work`}></image-slot>
      ))}
    </div>
  </section>
);

const ProviderReviews = ({ p }) => {
  const reviews = REVIEWS[p.id] || [];
  return (
    <section className="prov-reviews">
      <div className="rev-head">
        <h2>Reviews</h2>
        <RatingLine rating={p.rating} count={p.reviewCount} size={16} />
      </div>
      <div className="rev-grid">
        {reviews.map((r, i) => <ReviewCard key={i} r={r} />)}
      </div>
    </section>
  );
};

// ---------- COMPANY: storefront layout ----------
const CompanyProfile = ({ p, nav, addToCart, toast }) => (
  <main className="ha-page provider company-layout">
    <div className="banner">
      <image-slot id={`${p.id}-storefront`} shape="rect" src={p.storefrontImg} placeholder={`Drop a photo of the ${p.name} storefront, trucks, or crew`}></image-slot>
    </div>
    <div className="inner">
      <div className="ident">
        <div className="logo-pop"><Avatar provider={p} size={92} /></div>
        <div className="who">
          <ProviderKind provider={p} />
          <h1>{p.name}</h1>
          <p className="tagline">{p.tagline}</p>
          <div className="meta-line">
            <RatingLine rating={p.rating} count={p.reviewCount} size={15} />
            <span className="dot">·</span>
            <span className="muted"><Icon name="pin" size={14} sw={2} style={{ verticalAlign: "-2px" }} /> {p.serviceArea}</span>
          </div>
          <div className="badges">{p.badges.map((b) => <TrustBadge key={b} id={b} />)}</div>
        </div>
        <div className="head-cta">
          <button className="btn primary" onClick={() => document.querySelector(".prov-services")?.scrollTo ? window.scrollTo({ top: document.querySelector(".prov-services").offsetTop - 80, behavior: "smooth" }) : null}>See services</button>
          <button className="btn ghost" onClick={() => toast("Message thread opened (prototype)")}>Message</button>
        </div>
      </div>

      <div className="stat-row">
        <StatBlock value={p.yearsInBusiness} label="years in business" />
        <StatBlock value={p.jobsCompleted.toLocaleString()} label="jobs completed" />
        <StatBlock value={p.rating.toFixed(1)} label={`rating · ${p.reviewCount.toLocaleString()} reviews`} />
        <StatBlock value={p.team} label="team members" />
      </div>

      <div className="cols">
        <div className="main-col">
          <section className="prov-about">
            <h2>About {p.name}</h2>
            <p>{p.about}</p>
          </section>
          <ProviderServices p={p} nav={nav} addToCart={addToCart} />
          <ProviderGallery p={p} />
          <ProviderReviews p={p} />
        </div>
        <aside className="side-col">
          <ProviderTrustCard p={p} onMessage={() => toast("Message thread opened (prototype)")} />
        </aside>
      </div>
    </div>
  </main>
);

// ---------- INDIVIDUAL: personal profile layout ----------
const IndividualProfile = ({ p, nav, addToCart, toast }) => (
  <main className="ha-page provider individual-layout">
    <div className="inner">
      <div className="cols">
        <aside className="side-col left">
          <div className="ha-panel persona">
            <image-slot id={`${p.id}-portrait`} shape="circle" src={p.photo} placeholder={`Drop ${p.name.split(" ")[0]}'s photo`}></image-slot>
            <ProviderKind provider={p} />
            <h1>{p.name}</h1>
            <p className="tagline">{p.tagline}</p>
            <RatingLine rating={p.rating} count={p.reviewCount} size={15} />
            <div className="badges">{p.badges.map((b) => <TrustBadge key={b} id={b} compact />)}</div>
            {p.hourlyRate && (
              <div className="rate-line"><strong>{fmt$(p.hourlyRate)}/hr</strong><span className="muted"> base rate · fixed prices below</span></div>
            )}
            <button className="btn primary full" onClick={() => toast(`Message sent to ${p.name.split(" ")[0]} (prototype)`)}>
              <Icon name="message" size={16} sw={2} /> Message {p.name.split(" ")[0]}
            </button>
            <div className="facts">
              <div><Icon name="bolt" size={14} sw={2} /> {p.responseTime}</div>
              <div><Icon name="pin" size={14} sw={2} /> {p.serviceArea}</div>
              <div><Icon name="calendar" size={14} sw={2} /> {p.hours}</div>
              <div><Icon name="check" size={14} sw={2.4} /> {p.guarantee}</div>
            </div>
          </div>
          <div className="ha-panel mini-stats">
            <StatBlock value={p.yearsInBusiness} label="years experience" />
            <StatBlock value={p.jobsCompleted.toLocaleString()} label="jobs done" />
            <StatBlock value={p.rating.toFixed(1)} label="avg rating" />
          </div>
        </aside>
        <div className="main-col">
          <section className="prov-about">
            <h2>Meet {p.name.split(" ")[0]}</h2>
            <p>{p.about}</p>
            {p.skills && (
              <div className="chips">{p.skills.map((s) => <span key={s} className="chip">{s}</span>)}</div>
            )}
          </section>
          <ProviderServices p={p} nav={nav} addToCart={addToCart} />
          <ProviderGallery p={p} />
          <ProviderReviews p={p} />
        </div>
      </div>
    </div>
  </main>
);

const PageProvider = ({ route, nav, addToCart, toast }) => {
  const p = PROVIDERS.find((x) => x.id === route.id);
  if (!p) return <main className="ha-page"><div className="inner"><p style={{ padding: 40 }}>Provider not found.</p></div></main>;
  return p.type === "company"
    ? <CompanyProfile p={p} nav={nav} addToCart={addToCart} toast={toast} />
    : <IndividualProfile p={p} nav={nav} addToCart={addToCart} toast={toast} />;
};

window.PageProvider = PageProvider;
