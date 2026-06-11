// HouseAccount.AI — app shell: routing, cart state, tweaks
const HA_TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "primaryColor": "#1d4e89",
  "cardRadius": 14,
  "catalogDensity": "cozy"
}/*EDITMODE-END*/;

const parseHash = () => {
  const h = location.hash.replace(/^#\/?/, "");
  const [page, arg] = h.split("/");
  if (page === "provider" && arg) return { page: "provider", id: arg };
  if (page === "service" && arg) return { page: "service", id: arg };
  if (page === "catalog" && arg === "providers") return { page: "catalog", tab: "providers" };
  return { page: "catalog" };
};

const App = () => {
  const [t, setTweak] = useTweaks(HA_TWEAK_DEFAULTS);
  const [route, setRoute] = React.useState(parseHash());
  const [query, setQuery] = React.useState("");
  const [cart, setCart] = React.useState(() => {
    try { return JSON.parse(localStorage.getItem("ha-cart-v1")) || []; } catch (e) { return []; }
  });
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [toastState, setToastState] = React.useState(null);

  React.useEffect(() => {
    const onHash = () => { setRoute(parseHash()); window.scrollTo(0, 0); };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  React.useEffect(() => {
    try { localStorage.setItem("ha-cart-v1", JSON.stringify(cart)); } catch (e) {}
  }, [cart]);

  const nav = (page, opts = {}) => {
    let h = "#/" + page;
    if (page === "catalog" && opts.tab === "providers") h += "/providers";
    if (opts.id) h += "/" + opts.id;
    if (location.hash === h) { setRoute(parseHash()); window.scrollTo(0, 0); }
    else location.hash = h;
  };

  const toast = (msg) => {
    const id = Date.now();
    setToastState({ id, msg });
    setTimeout(() => setToastState((cur) => (cur && cur.id === id ? null : cur)), 2600);
  };

  const addToCart = (s, opts = {}) => {
    const kind = s.priceModel === "quote" ? "quote" : "book";
    setCart((items) => {
      if (kind === "quote") {
        if (items.some((i) => i.serviceId === s.id && i.kind === "quote")) return items;
        return [...items, { key: s.id + "-q", kind, serviceId: s.id }];
      }
      const optionIndex = opts.optionIndex || 0;
      const key = s.id + "-" + optionIndex;
      const existing = items.find((i) => i.key === key);
      if (existing) return items.map((i) => (i.key === key ? { ...i, qty: (i.qty || 1) + (opts.qty || 1) } : i));
      return [...items, { key, kind, serviceId: s.id, optionIndex, qty: opts.qty || 1 }];
    });
    toast(kind === "quote" ? "Quote request added — it's free" : "Added to cart");
    setDrawerOpen(true);
  };

  const removeFromCart = (key) => setCart((items) => items.filter((i) => i.key !== key));
  const changeQty = (key, d) =>
    setCart((items) => items.map((i) => (i.key === key ? { ...i, qty: Math.max(1, (i.qty || 1) + d) } : i)));

  const cartCount = cart.reduce((n, i) => n + (i.kind === "book" ? i.qty || 1 : 1), 0);

  const pageEl =
    route.page === "provider" ? <PageProvider route={route} nav={nav} addToCart={addToCart} toast={toast} /> :
    route.page === "service" ? <PageService route={route} nav={nav} addToCart={addToCart} toast={toast} /> :
    <PageCatalog route={route} nav={nav} query={query} addToCart={addToCart} />;

  return (
    <div className="ha-root" style={{
      "--primary": t.primaryColor,
      "--radius": t.cardRadius + "px",
      "--grid-min": t.catalogDensity === "compact" ? "236px" : "280px",
    }}>
      <Header nav={nav} route={route} cartCount={cartCount} onCartOpen={() => setDrawerOpen(true)} query={query} setQuery={setQuery} />
      {pageEl}
      <Footer />
      <CartDrawer open={drawerOpen} items={cart} onClose={() => setDrawerOpen(false)}
        onRemove={removeFromCart} onQty={changeQty} nav={nav} />
      <Toast toast={toastState} />
    </div>
  );
};

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
