// HouseAccount.AI — header, footer, cart drawer, toast
const Logo = ({ onClick }) => (
  <button className="ha-logo" onClick={onClick} aria-label="HouseAccount.AI home">
    <span className="mark">
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M3 11.2 12 3.5l9 7.7" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"></path>
        <path d="M5.5 10.2V20h13v-9.8" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"></path>
        <path d="M9.5 20v-5.5h5V20" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"></path>
      </svg>
    </span>
    <span className="word">HouseAccount<em>.AI</em></span>
  </button>
);

const Header = ({ nav, route, cartCount, onCartOpen, query, setQuery }) => (
  <header className="ha-header">
    <div className="inner">
      <Logo onClick={() => nav("catalog")} />
      <nav className="links">
        <button className={route.page === "catalog" && route.tab !== "providers" ? "on" : ""}
          onClick={() => nav("catalog")}>Services</button>
        <button className={route.page === "catalog" && route.tab === "providers" ? "on" : ""}
          onClick={() => nav("catalog", { tab: "providers" })}>Providers</button>
      </nav>
      <div className="search">
        <Icon name="search" size={16} sw={2} />
        <input
          placeholder="Search services or pros…"
          value={query}
          onChange={(e) => { setQuery(e.target.value); if (route.page !== "catalog") nav("catalog"); }}
          aria-label="Search services or providers"
        />
      </div>
      <button className="cart-btn" onClick={onCartOpen} aria-label={`Cart, ${cartCount} items`}>
        <Icon name="cart" size={20} sw={1.9} />
        {cartCount > 0 && <span className="count">{cartCount}</span>}
      </button>
    </div>
  </header>
);

const Footer = () => (
  <footer className="ha-footer">
    <div className="inner">
      <span>HouseAccount.AI — every fix, one account.</span>
      <span className="muted">Concept prototype · all providers & reviews are illustrative</span>
    </div>
  </footer>
);

// ---------- cart ----------
const cartTotal = (items) =>
  items.filter((i) => i.kind === "book").reduce((sum, i) => {
    const s = SERVICES.find((x) => x.id === i.serviceId);
    const delta = s.options ? (s.options.choices[i.optionIndex || 0].delta || 0) : 0;
    return sum + (s.price + delta) * (i.qty || 1);
  }, 0);

const CartDrawer = ({ open, items, onClose, onRemove, onQty, nav }) => {
  const booked = items.filter((i) => i.kind === "book");
  const quotes = items.filter((i) => i.kind === "quote");
  return (
    <div className={"ha-drawer-wrap" + (open ? " open" : "")} aria-hidden={!open}>
      <div className="scrim" onClick={onClose}></div>
      <aside className="ha-drawer" role="dialog" aria-label="Cart">
        <div className="head">
          <h2>Your cart</h2>
          <button className="icon-btn" onClick={onClose} aria-label="Close cart"><Icon name="close" size={18} sw={2} /></button>
        </div>
        <div className="scroll">
          {items.length === 0 && (
            <div className="empty">
              <Icon name="cart" size={36} sw={1.4} />
              <p>Nothing here yet.</p>
              <button className="btn ghost" onClick={() => { onClose(); nav("catalog"); }}>Browse services</button>
            </div>
          )}
          {booked.length > 0 && <div className="sec-label">Booked services</div>}
          {booked.map((i) => {
            const s = SERVICES.find((x) => x.id === i.serviceId);
            const p = providerOf(s);
            const delta = s.options ? (s.options.choices[i.optionIndex || 0].delta || 0) : 0;
            return (
              <div className="line" key={i.key}>
                <CatTile category={s.category} size={48} radius={10} iconSize={20} />
                <div className="mid">
                  <strong>{s.name}</strong>
                  {s.options && <span className="muted">{s.options.label}: {s.options.choices[i.optionIndex || 0].name}</span>}
                  <span className="muted">{p.name}</span>
                  <div className="qty">
                    <button onClick={() => onQty(i.key, -1)} aria-label="Decrease"><Icon name="minus" size={12} sw={2.4} /></button>
                    <span>{i.qty || 1}</span>
                    <button onClick={() => onQty(i.key, 1)} aria-label="Increase"><Icon name="plus" size={12} sw={2.4} /></button>
                  </div>
                </div>
                <div className="end">
                  <span className="amt">{fmt$((s.price + delta) * (i.qty || 1))}{s.priceModel === "hourly" ? <small>/hr</small> : null}</span>
                  <button className="rm" onClick={() => onRemove(i.key)}>Remove</button>
                </div>
              </div>
            );
          })}
          {quotes.length > 0 && <div className="sec-label">Quote requests <span className="free-pill">Free</span></div>}
          {quotes.map((i) => {
            const s = SERVICES.find((x) => x.id === i.serviceId);
            const p = providerOf(s);
            return (
              <div className="line" key={i.key}>
                <CatTile category={s.category} size={48} radius={10} iconSize={20} />
                <div className="mid">
                  <strong>{s.name}</strong>
                  <span className="muted">{p.name} · replies with a price in ~24h</span>
                </div>
                <div className="end">
                  <span className="amt quote">Quote</span>
                  <button className="rm" onClick={() => onRemove(i.key)}>Remove</button>
                </div>
              </div>
            );
          })}
        </div>
        {items.length > 0 && (
          <div className="foot">
            {booked.length > 0 && (
              <div className="total"><span>Subtotal</span><strong>{fmt$(cartTotal(items))}</strong></div>
            )}
            {quotes.length > 0 && booked.length === 0 && (
              <div className="total"><span>{quotes.length} quote request{quotes.length > 1 ? "s" : ""}</span><strong>Free</strong></div>
            )}
            <button className="btn primary lg" onClick={() => alert("Prototype ends here — checkout flow coming next!")}>
              {booked.length > 0 ? "Continue to scheduling" : "Send quote requests"}
            </button>
            <p className="fine">Pay nothing until the job is scheduled. Quotes are always free.</p>
          </div>
        )}
      </aside>
    </div>
  );
};

const Toast = ({ toast }) =>
  toast ? (
    <div className="ha-toast" key={toast.id}>
      <Icon name="check" size={16} sw={2.4} /> {toast.msg}
    </div>
  ) : null;

Object.assign(window, { Logo, Header, Footer, CartDrawer, Toast, cartTotal });
