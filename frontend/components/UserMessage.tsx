import { Card } from "@/components/ui/card";
import { User } from "lucide-react";

interface UserMessageProps {
  content: string;
  timestamp: Date;
}

export function UserMessage({ content, timestamp }: UserMessageProps) {
  return (
    <div className="flex items-start gap-3 justify-end">
      <Card className="max-w-2xl bg-surface-muted border-default px-4 py-3">
        <p className="text-sm text-primary">{content}</p>
        <time className="text-xs text-tertiary mt-1 block">
          {timestamp.toLocaleTimeString("cs-CZ", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </time>
      </Card>
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-surface-muted flex items-center justify-center">
        <User className="h-4 w-4 text-secondary" />
      </div>
    </div>
  );
}
