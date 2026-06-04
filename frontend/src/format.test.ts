import { describe, expect, it } from "vitest";
import { categoryClass, pct, routeClass, sentimentClass, titleCase } from "./format";

describe("format helpers", () => {
  it("titleCases snake_case", () => {
    expect(titleCase("new_request")).toBe("New Request");
    expect(titleCase("human_review")).toBe("Human Review");
  });

  it("formats percentages", () => {
    expect(pct(0.333)).toBe("33%");
    expect(pct(1)).toBe("100%");
  });

  it("flags human review distinctly from auto", () => {
    expect(routeClass("human_review")).toContain("badge-review");
    expect(routeClass("auto")).toContain("badge-auto");
  });

  it("marks high-risk categories", () => {
    expect(categoryClass("complaint")).toContain("badge-risk");
    expect(categoryClass("cancellation")).toContain("badge-risk");
    expect(categoryClass("new_request")).toContain("badge-cat");
  });

  it("maps sentiment to its badge", () => {
    expect(sentimentClass("negative")).toBe("badge badge-negative");
  });
});
