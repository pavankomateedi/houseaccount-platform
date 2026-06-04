interface Props {
  title: string;
  data: Record<string, number> | [string, number][];
  variant?: (key: string) => "" | "review" | "negative";
  // Explicit row order (by key). Keys not listed fall to the bottom. When
  // omitted, rows sort by value descending.
  order?: string[];
}

export function BarPanel({ title, data, variant, order }: Props) {
  const entries = Array.isArray(data) ? data : Object.entries(data);
  const sorted = order
    ? [...entries].sort((a, b) => {
        const ia = order.indexOf(a[0]);
        const ib = order.indexOf(b[0]);
        return (ia === -1 ? order.length : ia) - (ib === -1 ? order.length : ib);
      })
    : [...entries].sort((a, b) => b[1] - a[1]);
  const max = Math.max(1, ...sorted.map(([, v]) => v));
  return (
    <div className="panel">
      <h3>{title}</h3>
      {sorted.map(([key, val]) => (
        <div className="bar-row" key={key}>
          <span className="name">{key.replace(/_/g, " ")}</span>
          <span className="val">{val}</span>
          <span className="bar-track">
            <span
              className={`bar-fill ${variant ? variant(key) : ""}`}
              style={{ width: `${(val / max) * 100}%` }}
            />
          </span>
        </div>
      ))}
    </div>
  );
}
