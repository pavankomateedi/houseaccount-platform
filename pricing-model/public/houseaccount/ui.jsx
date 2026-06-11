// HouseAccount.AI — shared UI components
const { CATEGORIES, PROVIDERS, SERVICES, REVIEWS, BADGE_LABELS } = window.HA;

const catName = (id) => (CATEGORIES.find((c) => c.id === id) || {}).name || id;
const providerOf = (s) => PROVIDERS.find((p) => p.id === s.providerId);
const fmt$ = (n) => "$" + n.toLocaleString();

const CAT_HUES = {
  repairs: 214, "tv-mounting": 250, plumbing: 199, electrical: 42, "home-mods": 168,
  carpentry: 28, doors: 16, painting: 330, furniture: 150, flooring: 264, other: 214,
};

// ---------- atoms ----------
const Stars = ({ rating, size = 14 }) => (
  <span style={{ display: "inline-flex", gap: 1, alignItems: "center" }} aria-label={`${rating} stars`}>
    {[0, 1, 2, 3, 4].map((i) => (
      <StarFill key={i} size={size} frac={Math.max(0, Math.min(1, rating - i))} />
    ))}
  </span>
);

const RatingLine = ({ rating, count, size = 14 }) => (
  <span className="ha-rating">
    <Stars rating={rating} size={size} />
    <strong>{rating.toFixed(1)}</strong>
    {count != null && <span className="muted">({count.toLocaleString()})</span>}
  </span>
);

const TrustBadge = ({ id, compact }) => {
  const b = BADGE_LABELS[id];
  if (!b) return null;
  return (
    <span className={"ha-badge" + (compact ? " compact" : "")} title={b.desc}>
      <Icon name="shield" size={compact ? 12 : 14} sw={2} />
      {b.label}
    </span>
  );
};

const Avatar = ({ provider, size = 44 }) =>
  provider.photo ? (
    <img className="ha-avatar" src={provider.photo} alt={provider.name}
      style={{ width: size, height: size, borderRadius: "50%", objectFit: "cover", flex: "none" }} />
  ) : (
    <span className="ha-avatar" style={{
      width: size, height: size, fontSize: size * 0.36,
      background: `oklch(0.93 0.04 ${provider.avatarHue})`,
      color: `oklch(0.42 0.09 ${provider.avatarHue})`,
      borderRadius: provider.type === "company" ? "26%" : "50%",
    }}>
      {provider.type === "company" ? <Icon name="store" size={size * 0.5} sw={1.7} /> : provider.avatarInitials}
    </span>
  );

const ProviderKind = ({ provider }) => (
  <span className={"ha-kind " + provider.type}>
    <Icon name={provider.type === "company" ? "store" : "user"} size={12} sw={2.2} />
    {provider.type === "company" ? "Company" : "Individual Pro"}
  </span>
);

const PriceTag = ({ s, big }) => {
  const cls = "ha-price" + (big ? " big" : "");
  if (s.priceModel === "fixed") return <span className={cls}>{fmt$(s.price)}</span>;
  if (s.priceModel === "hourly") return <span className={cls}>{fmt$(s.price)}<small>/hr</small></span>;
  if (s.priceFrom != null) return <span className={cls}><small>from </small>{fmt$(s.priceFrom)}<small>{s.priceUnit || ""}</small></span>;
  return <span className={cls + " quote"}>Free quote</span>;
};

const CatTile = ({ category, size = "100%", radius = 0, iconSize = 34 }) => {
  const hue = CAT_HUES[category] ?? 214;
  return (
    <div className="ha-cattile" style={{
      width: size, height: size, borderRadius: radius,
      background: `linear-gradient(135deg, oklch(0.955 0.025 ${hue}), oklch(0.90 0.05 ${hue + 20}))`,
      color: `oklch(0.45 0.10 ${hue})`,
    }}>
      <Icon name={category} size={iconSize} sw={1.5} />
    </div>
  );
};

// ---------- cards ----------
const ServiceCard = ({ s, onOpen, onOpenProvider }) => {
  const p = providerOf(s);
  return (
    <article className="ha-card service" onClick={() => onOpen(s.id)} role="link" tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onOpen(s.id)}>
      <div className="thumb">
        <CatTile category={s.category} iconSize={38} />
        {s.popular && <span className="pop-flag">Popular</span>}
        <span className="time-flag"><Icon name="clock" size={12} sw={2.2} />{s.time}</span>
      </div>
      <div className="body">
        <div className="cat-line">{catName(s.category)}</div>
        <h3>{s.name}</h3>
        <RatingLine rating={s.rating} count={s.reviewCount} size={13} />
        <button className="prov-line" onClick={(e) => { e.stopPropagation(); onOpenProvider(p.id); }}>
          <Avatar provider={p} size={24} />
          <span className="prov-name">{p.name}</span>
          {p.badges.includes("verified") && <Icon name="shield" size={13} sw={2.2} style={{ color: "var(--green)" }} />}
        </button>
        <div className="foot">
          <PriceTag s={s} />
          <span className="cta">{s.priceModel === "quote" ? "Get quote" : "Book"} <Icon name="chevR" size={13} sw={2.4} /></span>
        </div>
      </div>
    </article>
  );
};

const ProviderCard = ({ p, onOpen }) => {
  const svcs = SERVICES.filter((s) => s.providerId === p.id);
  const cats = [...new Set(svcs.map((s) => catName(s.category)))];
  return (
    <article className="ha-card provider" onClick={() => onOpen(p.id)} role="link" tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && onOpen(p.id)}>
      <div className="head">
        <Avatar provider={p} size={56} />
        <div className="who">
          <ProviderKind provider={p} />
          <h3>{p.name}</h3>
          <RatingLine rating={p.rating} count={p.reviewCount} size={13} />
        </div>
      </div>
      <p className="tagline">{p.tagline}</p>
      <div className="chips">
        {cats.slice(0, 4).map((c) => <span key={c} className="chip">{c}</span>)}
        {cats.length > 4 && <span className="chip more">+{cats.length - 4}</span>}
      </div>
      <div className="stats">
        <span><strong>{p.yearsInBusiness}</strong> yrs</span>
        <span><strong>{p.jobsCompleted.toLocaleString()}</strong> jobs</span>
        <span className="resp"><Icon name="bolt" size={13} sw={2} />{p.responseTime.replace("Usually responds in ", "Replies ")}</span>
      </div>
      <div className="badges">
        {p.badges.map((b) => <TrustBadge key={b} id={b} compact />)}
      </div>
      <div className="foot">
        <span className="muted">{svcs.length} services</span>
        <span className="cta">View profile <Icon name="chevR" size={13} sw={2.4} /></span>
      </div>
    </article>
  );
};

// Compact row used on provider profile pages
const ServiceRow = ({ s, onOpen, onAdd }) => (
  <div className="ha-svcrow" onClick={() => onOpen(s.id)} role="link" tabIndex={0}
    onKeyDown={(e) => e.key === "Enter" && onOpen(s.id)}>
    <CatTile category={s.category} size={56} radius={12} iconSize={24} />
    <div className="mid">
      <h4>{s.name}</h4>
      <p>{s.blurb}</p>
      <div className="meta">
        <RatingLine rating={s.rating} count={s.reviewCount} size={12} />
        <span className="dot">·</span>
        <span className="muted"><Icon name="clock" size={12} sw={2} style={{ verticalAlign: "-2px" }} /> {s.time}</span>
      </div>
    </div>
    <div className="end">
      <PriceTag s={s} />
      <button className={"btn sm " + (s.priceModel === "quote" ? "ghost" : "primary")}
        onClick={(e) => { e.stopPropagation(); onAdd(s); }}>
        {s.priceModel === "quote" ? "Request quote" : "Add"}
      </button>
    </div>
  </div>
);

const ReviewCard = ({ r }) => (
  <div className="ha-review">
    <div className="top">
      <span className="ha-avatar reviewer">{r.name[0]}</span>
      <div>
        <strong>{r.name}</strong>
        <div className="sub"><Stars rating={r.rating} size={12} /> <span className="muted">{r.date} · {r.service}</span></div>
      </div>
    </div>
    <p>{r.text}</p>
  </div>
);

const StatBlock = ({ value, label }) => (
  <div className="ha-stat"><strong>{value}</strong><span>{label}</span></div>
);

Object.assign(window, {
  catName, providerOf, fmt$, CAT_HUES,
  Stars, RatingLine, TrustBadge, Avatar, ProviderKind, PriceTag, CatTile,
  ServiceCard, ProviderCard, ServiceRow, ReviewCard, StatBlock,
});
