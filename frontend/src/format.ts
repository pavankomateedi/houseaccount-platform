// Presentation helpers shared across components.

export function titleCase(s: string): string {
  return s
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function pct(x: number): string {
  return `${Math.round(x * 100)}%`;
}

export function routeClass(route: string): string {
  return route === "human_review" ? "badge badge-review" : "badge badge-auto";
}

export function sentimentClass(sentiment: string): string {
  return `badge badge-${sentiment}`;
}

export function categoryClass(category: string): string {
  return category === "complaint" || category === "cancellation"
    ? "badge badge-risk"
    : "badge badge-cat";
}
