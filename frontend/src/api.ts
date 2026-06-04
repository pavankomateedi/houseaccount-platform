import type {
  AggregateStats,
  ApplyResult,
  Booking,
  EvalReport,
  InsightView,
  Provider,
  Quote,
  Review,
  Service,
  ServiceRequest,
} from "./types";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  health: () => get<{ status: string; mode: string }>("/api/health"),
  taxonomy: () => get<Service[]>("/api/taxonomy"),
  insights: () => get<InsightView[]>("/api/insights"),
  stats: () => get<AggregateStats>("/api/insights/stats"),
  evalReport: (mode?: string) =>
    get<EvalReport>(`/api/eval${mode ? `?mode=${mode}` : ""}`),
  applyInsight: (conversationId: string) =>
    post<ApplyResult>(`/api/insights/${conversationId}/apply`),
  providers: () => get<Provider[]>("/api/providers"),
  requests: () => get<ServiceRequest[]>("/api/requests"),
  createRequest: (body: {
    homeowner_id: string;
    service_type: string;
    zip_code: string;
    timing?: string | null;
    notes?: string;
  }) => post<ServiceRequest>("/api/requests", body),
  makeQuotes: (requestId: string) =>
    post<Quote[]>(`/api/requests/${requestId}/quotes`),
  acceptQuote: (quoteId: string, scheduledTime?: string) =>
    post<Booking>(`/api/quotes/${quoteId}/accept`, {
      scheduled_time: scheduledTime ?? null,
    }),
  bookings: () => get<Booking[]>("/api/bookings"),
  reviews: () => get<Review[]>("/api/reviews"),
};
