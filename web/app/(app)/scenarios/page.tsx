"use client";

import { PagePlaceholder } from "@/components/page-placeholder";
import { FlaskConical } from "lucide-react";

export default function ScenariosPage() {
  return (
    <PagePlaceholder
      title="Scenario Analysis"
      description="What-if analysis: salary changes, market crashes, retirement shifts and more."
      icon={FlaskConical}
    />
  );
}
