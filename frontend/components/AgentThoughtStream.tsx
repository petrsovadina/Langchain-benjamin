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

export function AgentThoughtStream({ agents }: AgentThoughtStreamProps) {
  if (agents.length === 0) return null;

  return (
    <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50">
      <div className="bg-slate-900/90 backdrop-blur-sm text-white px-4 py-2 rounded-lg shadow-lg">
        <div className="space-y-2">
          {agents.map((agent) => (
            <div key={agent.name} className="flex items-center gap-2 font-mono text-xs">
              {agent.status === "running" && (
                <div className="flex gap-1">
                  <span className="h-2 w-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="h-2 w-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="h-2 w-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              )}
              {agent.status === "complete" && (
                <span className="text-green-500">{"\u2713"}</span>
              )}
              <span className="text-slate-300">
                {AGENT_LABELS[agent.name] || agent.name}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
