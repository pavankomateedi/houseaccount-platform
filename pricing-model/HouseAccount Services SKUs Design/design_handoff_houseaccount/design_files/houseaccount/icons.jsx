// HouseAccount.AI — icon set (stroke icons, UI-grade)
const HAIcon = ({ d, size = 20, sw = 1.8, style, children }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor"
    strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" style={style} aria-hidden="true">
    {d ? <path d={d}></path> : children}
  </svg>
);

const ICON_PATHS = {
  search: "M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16Zm10 2-4.35-4.35",
  cart: "M3 3h2l2.4 12.2a1.5 1.5 0 0 0 1.47 1.2h8.56a1.5 1.5 0 0 0 1.46-1.14L21 8H6.2M9.5 21a.5.5 0 1 0 0-1 .5.5 0 0 0 0 1Zm8 0a.5.5 0 1 0 0-1 .5.5 0 0 0 0 1Z",
  star: "M12 2.5l2.95 5.98 6.6.96-4.78 4.66 1.13 6.58L12 17.58l-5.9 3.1 1.13-6.58L2.45 9.44l6.6-.96L12 2.5Z",
  shield: "M12 2.8 4.5 5.6v5.2c0 4.7 3.2 8.6 7.5 10.4 4.3-1.8 7.5-5.7 7.5-10.4V5.6L12 2.8ZM9 11.8l2.2 2.2 4-4.4",
  check: "M4.5 12.5l5 5 10-11",
  clock: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Zm0-14v5l3.5 2",
  pin: "M12 21s7-5.5 7-11a7 7 0 1 0-14 0c0 5.5 7 11 7 11Zm0-8.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z",
  chevR: "M9 5.5 15.5 12 9 18.5",
  chevL: "M15 5.5 8.5 12 15 18.5",
  chevD: "M5.5 9 12 15.5 18.5 9",
  arrowL: "M19 12H5m6-7-7 7 7 7",
  close: "M5 5l14 14M19 5 5 19",
  plus: "M12 5v14M5 12h14",
  minus: "M5 12h14",
  bolt: "M13 2 4.5 13.5H11L9.8 22l8.7-11.5H12L13 2Z",
  user: "M12 12a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9Zm-8 9a8 8 0 0 1 16 0",
  store: "M4 9.5 5.4 4h13.2L20 9.5M4 9.5a2.6 2.6 0 0 0 5.3 0 2.6 2.6 0 0 0 5.4 0 2.6 2.6 0 0 0 5.3 0M5 12v8h14v-8M10 20v-5h4v5",
  camera: "M4 8h3l2-2.5h6L17 8h3a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1Zm8 9a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z",
  message: "M21 12a8.5 8.5 0 0 1-12.4 7.5L3 21l1.6-5.4A8.5 8.5 0 1 1 21 12Z",
  calendar: "M4 6.5h16M7 3.5v3m10-3v3M5 5h14a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Z",
  // categories
  repairs: "M14.5 6.5a4 4 0 0 0-5.6 4.9L3 17.3a2 2 0 1 0 2.8 2.8l5.9-5.9a4 4 0 0 0 4.9-5.6l-2.6 2.6-2.1-.6-.6-2.1 2.6-2.6Z",
  "tv-mounting": "M3 5h18v11H3V5Zm6 14.5h6M12 16v3.5",
  plumbing: "M12 3c-2.8 3.4-5.5 6.6-5.5 9.8a5.5 5.5 0 0 0 11 0C17.5 9.6 14.8 6.4 12 3Z",
  electrical: "M13 2 4.5 13.5H11L9.8 22l8.7-11.5H12L13 2Z",
  "home-mods": "M3 11.5 12 4l9 7.5M5.5 10v9.5h13V10",
  carpentry: "M3 17.5 14.5 6l3.5 3.5L6.5 21H3v-3.5ZM13 7.5l3.5 3.5M19 3l2 2-2.5 2.5-2-2L19 3Z",
  doors: "M6 21V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v17M6 21h12M14.5 12.5a.6.6 0 1 0 0-1.2.6.6 0 0 0 0 1.2Z",
  painting: "M4 4h13v5H4V4Zm13 2.5h3.5V11l-8 1.5v3M11.5 15.5h2V21h-2v-5.5Z",
  furniture: "M5 19v-6.5M19 19v-6.5M5 14h14M7 14V6a1.5 1.5 0 0 1 1.5-1.5h7A1.5 1.5 0 0 1 17 6v8M5 17h14",
  flooring: "M3 5h18v14H3V5Zm6 0v4.7m6-4.7v4.7M3 9.7h18M6 9.7v4.6m12-4.6v4.6M3 14.3h18M9 14.3V19m6-4.7V19",
  other: "M5 12.5a.8.8 0 1 0 0-1.6.8.8 0 0 0 0 1.6Zm7 0a.8.8 0 1 0 0-1.6.8.8 0 0 0 0 1.6Zm7 0a.8.8 0 1 0 0-1.6.8.8 0 0 0 0 1.6Z",
};

const Icon = ({ name, size, sw, style }) => <HAIcon d={ICON_PATHS[name] || ICON_PATHS.other} size={size} sw={sw} style={style} />;

const StarFill = ({ size = 14, frac = 1 }) => {
  const id = React.useId();
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" style={{ flex: "none" }}>
      <defs>
        <linearGradient id={id}>
          <stop offset={`${frac * 100}%`} stopColor="var(--star, #f5a623)"></stop>
          <stop offset={`${frac * 100}%`} stopColor="#dde3ea"></stop>
        </linearGradient>
      </defs>
      <path fill={`url(#${id})`} d="M12 2.5l2.95 5.98 6.6.96-4.78 4.66 1.13 6.58L12 17.58l-5.9 3.1 1.13-6.58L2.45 9.44l6.6-.96L12 2.5Z"></path>
    </svg>
  );
};

Object.assign(window, { Icon, StarFill, ICON_PATHS });
