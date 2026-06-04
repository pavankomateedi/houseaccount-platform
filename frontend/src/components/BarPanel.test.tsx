import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { BarPanel } from "./BarPanel";

describe("BarPanel", () => {
  it("renders a row per entry with its value, sorted descending", () => {
    render(<BarPanel title="Volume" data={{ complaint: 3, new_request: 10 }} />);
    expect(screen.getByText("Volume")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    // largest value drives a full-width bar
    const fills = document.querySelectorAll(".bar-fill");
    expect(fills.length).toBe(2);
    expect((fills[0] as HTMLElement).style.width).toBe("100%");
  });

  it("accepts tuple data (top services)", () => {
    render(<BarPanel title="Top" data={[["handyman", 5]]} />);
    expect(screen.getByText("handyman")).toBeInTheDocument();
  });
});
