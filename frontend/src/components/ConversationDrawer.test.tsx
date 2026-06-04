import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { InsightView } from "../types";
import { ConversationDrawer } from "./ConversationDrawer";

vi.mock("../api", () => ({ api: { applyInsight: vi.fn() } }));

function makeView(overrides: Partial<InsightView["insight"]>): InsightView {
  return {
    conversation: {
      id: "conv-0001",
      homeowner_id: "ho-1",
      zip_code: "94110",
      provider_id: "pro-01",
      provider_name: "Bayview Handy Co.",
      messages: [{ sender: "homeowner", text: "I need help with handyman work." }],
    },
    insight: {
      conversation_id: "conv-0001",
      classification: {
        category: "new_request",
        entities: {
          service_type: "handyman",
          timing: "Saturday",
          urgency: "low",
          property_ref: null,
          pricing_ref: null,
        },
        sentiment: "neutral",
        confidence: 0.9,
        rationale: "",
      },
      route: "auto",
      action: "create_job",
      escalation_reason: null,
      linked_request_id: null,
      ...overrides,
    },
  };
}

describe("ConversationDrawer", () => {
  it("offers apply for auto-routed create_job with a known service", () => {
    render(<ConversationDrawer view={makeView({})} onClose={() => {}} onApplied={() => {}} />);
    expect(screen.getByText("Apply → create job")).toBeInTheDocument();
    expect(screen.getByText("handyman")).toBeInTheDocument();
  });

  it("holds human-review conversations instead of auto-acting", () => {
    const view = makeView({ route: "human_review", action: "escalate", escalation_reason: "high_risk_category:complaint" });
    render(<ConversationDrawer view={view} onClose={() => {}} onApplied={() => {}} />);
    expect(screen.queryByText("Apply → create job")).not.toBeInTheDocument();
    expect(screen.getByText(/Held for a human/)).toBeInTheDocument();
  });
});
