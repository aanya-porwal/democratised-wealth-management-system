"use client";

import { PagePlaceholder } from "@/components/page-placeholder";
import { FileSearch } from "lucide-react";

export default function ResearchPage() {
  return (
    <PagePlaceholder
      title="Research Reports"
      description="Institutional-style research reports from the Security Selection Engine."
      icon={FileSearch}
    />
  );
}
