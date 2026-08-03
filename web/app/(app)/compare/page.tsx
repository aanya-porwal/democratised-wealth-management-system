"use client";

import { PagePlaceholder } from "@/components/page-placeholder";
import { GitCompareArrows } from "lucide-react";

export default function ComparePage() {
  return (
    <PagePlaceholder
      title="Security Comparison"
      description="Compare multiple securities side by side with interactive tables and charts."
      icon={GitCompareArrows}
    />
  );
}
