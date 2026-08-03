"use client";

import { PagePlaceholder } from "@/components/page-placeholder";
import { Bell } from "lucide-react";

export default function NotificationsPage() {
  return (
    <PagePlaceholder
      title="Notification Centre"
      description="Alerts, insights and reminders from the backend notification service."
      icon={Bell}
    />
  );
}
