// Mirrors the backend pydantic models (houseaccount/models.py + marketplace).

export type Category =
  | "new_request"
  | "reschedule"
  | "cancellation"
  | "complaint"
  | "pricing_question"
  | "follow_up";

export type Route = "auto" | "human_review";
export type Sentiment = "positive" | "neutral" | "negative";
export type Urgency = "low" | "medium" | "high";

export interface Message {
  sender: "homeowner" | "provider";
  text: string;
}

export interface Entities {
  service_type: string | null;
  timing: string | null;
  urgency: Urgency;
  property_ref: string | null;
  pricing_ref: string | null;
}

export interface Classification {
  category: Category;
  entities: Entities;
  sentiment: Sentiment;
  confidence: number;
  rationale: string;
}

export interface Conversation {
  id: string;
  homeowner_id: string;
  zip_code: string;
  messages: Message[];
  provider_id: string | null;
  provider_name: string | null;
}

export interface Insight {
  conversation_id: string;
  classification: Classification;
  route: Route;
  action: string;
  escalation_reason: string | null;
  linked_request_id: string | null;
}

export interface InsightView {
  conversation: Conversation;
  insight: Insight;
}

export interface AggregateStats {
  total: number;
  by_category: Record<string, number>;
  by_sentiment: Record<string, number>;
  by_urgency: Record<string, number>;
  by_route: Record<string, number>;
  by_action: Record<string, number>;
  top_services: [string, number][];
  complaint_rate: number;
  human_review_rate: number;
  avg_confidence: number;
}

export interface EvalReport {
  mode: string;
  n: number;
  category_f1: number;
  route_f1: number;
  entity_score: number;
  sentiment_accuracy: number;
  urgency_accuracy: number;
  passed: boolean;
  failures: string[];
}

export interface Service {
  key: string;
  label: string;
  group: string;
}

export interface Provider {
  id: string;
  name: string;
  services: string[];
  coverage_zips: string[];
  rating: number;
  vetted: boolean;
  insured: boolean;
  jobs_done: number;
}

export interface ServiceRequest {
  id: string;
  homeowner_id: string;
  service_type: string;
  zip_code: string;
  timing: string | null;
  notes: string;
  status: string;
  source: string;
  created_from_conversation_id: string | null;
}

export interface Quote {
  id: string;
  request_id: string;
  provider_id: string;
  amount: number;
  quote_window_hours: number;
  status: string;
}

export interface Booking {
  id: string;
  request_id: string;
  provider_id: string;
  quote_id: string;
  scheduled_time: string | null;
  status: string;
}

export interface ApplyResult {
  created_request_id: string | null;
  request: ServiceRequest | null;
  message: string;
}

export interface Review {
  id: string;
  provider_id: string;
  homeowner_id: string;
  service_type: string;
  rating: number;
  sentiment: Sentiment;
  text: string;
}
