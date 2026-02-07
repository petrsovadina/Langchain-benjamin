import { cn } from "@/lib/utils";
import { type AgentStatus } from "@/hooks/useConsult";

interface AgentThoughtStreamProps {
  agents: AgentStatus[];
}

const AGENT_LABELS: Record<string, string> = {
  supervisor: "\u{1F9E0} Supervisor - Klasifikuji dotaz",
  drug_agent: "\u{1F48A} Drug Agent - Prohled\u00E1v\u00E1m S\u00DAKL",
  pubmed_agent: "\u{1F30D} PubMed Agent - Prohled\u00E1v\u00E1m PubMed",
  guidelines_agent: "\u{1F4D6} Guidelines Agent - Prohled\u00E1v\u00E1m \u010CLS JEP",
  synthesizer: "\u{1F4DD} Synthesizer - Form\u00E1tuji odpov\u011B\u010F",
};

const AGENT_COLORS: Record<string, string> = {
  supervisor: "text-purple-500",
  drug_agent: "text-blue-500",
  pubmed_agent: "text-green-500",
  guidelines_agent: "text-orange-500",
  synthesizer: "text-pink-500",
};

const ALL_AGENTS = ["supervisor", "drug_agent", "pubmed_agent", "guidelines_agent", "synthesizer"];

export function AgentThoughtStream({ agents }: AgentThoughtStreamProps) {
  if (agents.length === 0) return null;

  const agentMap = new Map(agents.map((a) => [a.name, a]));

  const displayAgents = ALL_AGENTS.map((name) => {
    const agent = agentMap.get(name);
    return agent || { name, status: "idle" as const };
  });

  return (
    <div
      className="fixed top-20 left-1/2 -translate-x-1/2 z-50 animate-in slide-in-from-top-4 duration-300"
      data-testid="agent-thought-stream"
      role="status"
      aria-label="Stav agent\u016F"
    >
      <div className="bg-slate-900/90 backdrop-blur-sm text-white px-4 py-2 rounded-lg shadow-lg">
        <div className="space-y-2">
          {displayAgents.map((agent) => (
            <div
              key={agent.name}
              className={cn(
                "flex items-center gap-2 font-mono text-xs transition-opacity duration-300",
                agent.status === "idle" && "opacity-50"
              )}
              data-testid={`agent-${agent.name}`}
              data-status={agent.status}
            >
              {agent.status === "idle" && (
                <span className="h-2 w-2 bg-slate-400 rounded-full" />
              )}
              {agent.status === "running" && (
                <div className="flex gap-1">
                  <span className="h-2 w-2 bg-primary rounded-full animate-bounce shadow-lg shadow-primary/50" style={{ animationDelay: "0ms" }} />
                  <span className="h-2 w-2 bg-primary rounded-full animate-bounce shadow-lg shadow-primary/50" style={{ animationDelay: "150ms" }} />
                  <span className="h-2 w-2 bg-primary rounded-full animate-bounce shadow-lg shadow-primary/50" style={{ animationDelay: "300ms" }} />
                </div>
              )}
              {agent.status === "complete" && (
                <span className="text-green-500 animate-in fade-in duration-300">{"\u2713"}</span>
              )}
              <span className={cn(
                "text-slate-300",
                agent.status === "running" && "font-semibold",
                AGENT_COLORS[agent.name]
              )}>
                {AGENT_LABELS[agent.name] || agent.name}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
