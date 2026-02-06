import { Card } from "@/components/ui/card";
import { User } from "lucide-react";

interface UserMessageProps {
  content: string;
  timestamp: Date;
}

export function UserMessage({ content, timestamp }: UserMessageProps) {
  return (
    <div className="flex items-start gap-3 justify-end">
      <Card className="max-w-2xl bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700 px-4 py-3">
        <p className="text-sm text-slate-900 dark:text-slate-100">{content}</p>
        <time className="text-xs text-slate-500 dark:text-slate-400 mt-1 block">
          {timestamp.toLocaleTimeString("cs-CZ", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </time>
      </Card>
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center">
        <User className="h-4 w-4 text-slate-600 dark:text-slate-300" />
      </div>
    </div>
  );
}
