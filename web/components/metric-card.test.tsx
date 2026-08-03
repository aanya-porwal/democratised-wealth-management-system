import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MetricCard } from "./metric-card";

describe("MetricCard", () => {
  it("renders label, value and sublabel", () => {
    render(
      <MetricCard label="Net Worth" value="₹1,00,000" sublabel="vs last month" />
    );
    expect(screen.getByText("Net Worth")).toBeInTheDocument();
    expect(screen.getByText("₹1,00,000")).toBeInTheDocument();
    expect(screen.getByText("vs last month")).toBeInTheDocument();
  });

  it("renders a positive trend with ▲", () => {
    render(<MetricCard label="Returns" value="12%" trend={4.2} />);
    expect(screen.getByText("▲ 4.2%")).toBeInTheDocument();
  });

  it("renders a negative trend with ▼", () => {
    render(<MetricCard label="Returns" value="12%" trend={-1.5} />);
    expect(screen.getByText("▼ 1.5%")).toBeInTheDocument();
  });

  it("does not render trend when omitted", () => {
    render(<MetricCard label="Cash" value="₹50,000" />);
    expect(screen.queryByText(/▲/)).not.toBeInTheDocument();
    expect(screen.queryByText(/▼/)).not.toBeInTheDocument();
  });
});

