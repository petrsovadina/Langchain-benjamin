export function MessageSkeleton() {
  return (
    <div className="space-y-3 animate-pulse">
      <div className="flex items-start gap-3">
        <div className="h-8 w-8 rounded-full bg-slate-200 dark:bg-slate-700" />
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-3/4" />
          <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/2" />
        </div>
      </div>
    </div>
  );
}
