"use client";

// Dedicated full-page AI Financial Coach.
// Reuses the global AiCoachProvider (same session/message state as the
// floating assistant panel) but renders in a large, focused workspace.

import { AiCoachFullPage } from "@/components/ai/ai-assistant-panel";

export default function CoachPage() {
  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      <AiCoachFullPage />
    </div>
  );
}
