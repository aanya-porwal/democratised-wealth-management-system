"use client";

import { PagePlaceholder } from "@/components/page-placeholder";
import { Settings } from "lucide-react";

export default function SettingsPage() {
  return (
    <PagePlaceholder
      title="Settings"
      description="Preferences, security, notifications and theme customisation."
      icon={Settings}
    />
  );
}
