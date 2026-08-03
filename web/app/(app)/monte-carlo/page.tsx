"use client";

import { PagePlaceholder } from "@/components/page-placeholder";
import { Dices } from "lucide-react";

export default function MonteCarloPage() {
  return (
    <PagePlaceholder
      title="Monte Carlo"
      description="Visualize 10,000 simulations with fan charts, probability curves and confidence intervals."
      icon={Dices}
    />
  );
}
