import { describe, it, expect } from "vitest";
import {
  formatCurrency,
  formatPercent,
  formatNumber,
  getErrorMessage,
  cn,
} from "./utils";

describe("formatting helpers", () => {
  it("formats currency in INR", () => {
    expect(formatCurrency(100000)).toContain("₹");
    expect(formatCurrency(null)).toBe("—");
  });

  it("formats percentages from 0-1 ratios", () => {
    expect(formatPercent(0.62)).toBe("62.0%");
    expect(formatPercent(undefined)).toBe("—");
  });

  it("formats numbers with INR grouping", () => {
    expect(formatNumber(100000)).toMatch(/1,00,000/);
  });
});

describe("getErrorMessage", () => {
  it("extracts Error messages", () => {
    expect(getErrorMessage(new Error("boom"))).toBe("boom");
  });

  it("accepts plain strings", () => {
    expect(getErrorMessage("oops")).toBe("oops");
  });

  it("reads detail/error fields from API-ish objects", () => {
    expect(getErrorMessage({ detail: "Invalid credentials" })).toBe(
      "Invalid credentials"
    );
  });

  it("uses the fallback for unknown values", () => {
    expect(getErrorMessage(42, "Everything broke")).toBe("Everything broke");
  });
});

describe("cn", () => {
  it("merges class names and resolves conflicts", () => {
    expect(cn("px-2 p-4", "p-2")).toContain("p-2");
  });
});

