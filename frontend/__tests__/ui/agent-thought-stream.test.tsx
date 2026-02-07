import { render, screen } from "@testing-library/react";
import { AgentThoughtStream } from "@/components/AgentThoughtStream";
import type { AgentStatus } from "@/hooks/useConsult";

describe("AgentThoughtStream", () => {
  describe("Empty State", () => {
    test("renders nothing when agents array is empty", () => {
      const { container } = render(<AgentThoughtStream agents={[]} />);
      expect(container.innerHTML).toBe("");
    });
  });

  describe("Idle State", () => {
    test("shows all 5 agents when at least one is active", () => {
      const agents: AgentStatus[] = [
        { name: "supervisor", status: "running" },
      ];
      render(<AgentThoughtStream agents={agents} />);

      expect(screen.getByTestId("agent-supervisor")).toBeInTheDocument();
      expect(screen.getByTestId("agent-drug_agent")).toBeInTheDocument();
      expect(screen.getByTestId("agent-pubmed_agent")).toBeInTheDocument();
      expect(screen.getByTestId("agent-guidelines_agent")).toBeInTheDocument();
      expect(screen.getByTestId("agent-synthesizer")).toBeInTheDocument();
    });

    test("idle agents have opacity-50", () => {
      const agents: AgentStatus[] = [
        { name: "supervisor", status: "running" },
      ];
      render(<AgentThoughtStream agents={agents} />);

      const drugAgent = screen.getByTestId("agent-drug_agent");
      expect(drugAgent.className).toContain("opacity-50");
    });

    test("idle agents have grey dot indicator", () => {
      const agents: AgentStatus[] = [
        { name: "supervisor", status: "running" },
      ];
      render(<AgentThoughtStream agents={agents} />);

      const drugAgent = screen.getByTestId("agent-drug_agent");
      const dot = drugAgent.querySelector(".bg-slate-400");
      expect(dot).toBeInTheDocument();
    });

    test("idle agents have data-status=idle", () => {
      const agents: AgentStatus[] = [
        { name: "supervisor", status: "running" },
      ];
      render(<AgentThoughtStream agents={agents} />);

      const drugAgent = screen.getByTestId("agent-drug_agent");
      expect(drugAgent).toHaveAttribute("data-status", "idle");
    });
  });

  describe("Running State", () => {
    test("running agent has bouncing dots", () => {
      const agents: AgentStatus[] = [
        { name: "supervisor", status: "running" },
      ];
      render(<AgentThoughtStream agents={agents} />);

      const supervisor = screen.getByTestId("agent-supervisor");
      const dots = supervisor.querySelectorAll(".animate-bounce");
      expect(dots).toHaveLength(3);
    });

    test("running agent dots have glow effect", () => {
      const agents: AgentStatus[] = [
        { name: "supervisor", status: "running" },
      ];
      render(<AgentThoughtStream agents={agents} />);

      const supervisor = screen.getByTestId("agent-supervisor");
      const dots = supervisor.querySelectorAll(".shadow-lg");
      expect(dots.length).toBeGreaterThan(0);
    });

    test("running agent label is semibold", () => {
      const agents: AgentStatus[] = [
        { name: "supervisor", status: "running" },
      ];
      render(<AgentThoughtStream agents={agents} />);

      const supervisor = screen.getByTestId("agent-supervisor");
      const label = supervisor.querySelector(".font-semibold");
      expect(label).toBeInTheDocument();
    });

    test("running agent does not have opacity-50", () => {
      const agents: AgentStatus[] = [
        { name: "supervisor", status: "running" },
      ];
      render(<AgentThoughtStream agents={agents} />);

      const supervisor = screen.getByTestId("agent-supervisor");
      expect(supervisor.className).not.toContain("opacity-50");
    });

    test("running agent has data-status=running", () => {
      const agents: AgentStatus[] = [
        { name: "supervisor", status: "running" },
      ];
      render(<AgentThoughtStream agents={agents} />);

      const supervisor = screen.getByTestId("agent-supervisor");
      expect(supervisor).toHaveAttribute("data-status", "running");
    });
  });

  describe("Complete State", () => {
    test("complete agent shows green checkmark", () => {
      const agents: AgentStatus[] = [
        { name: "supervisor", status: "complete" },
      ];
      render(<AgentThoughtStream agents={agents} />);

      const supervisor = screen.getByTestId("agent-supervisor");
      const checkmark = supervisor.querySelector(".text-green-500");
      expect(checkmark).toBeInTheDocument();
      expect(checkmark?.textContent).toBe("\u2713");
    });

    test("complete agent has fade-in animation", () => {
      const agents: AgentStatus[] = [
        { name: "supervisor", status: "complete" },
      ];
      render(<AgentThoughtStream agents={agents} />);

      const supervisor = screen.getByTestId("agent-supervisor");
      const checkmark = supervisor.querySelector(".animate-in");
      expect(checkmark).toBeInTheDocument();
    });

    test("complete agent has data-status=complete", () => {
      const agents: AgentStatus[] = [
        { name: "supervisor", status: "complete" },
      ];
      render(<AgentThoughtStream agents={agents} />);

      const supervisor = screen.getByTestId("agent-supervisor");
      expect(supervisor).toHaveAttribute("data-status", "complete");
    });
  });

  describe("Per-Agent Colors", () => {
    test("supervisor has purple color", () => {
      const agents: AgentStatus[] = [
        { name: "supervisor", status: "running" },
      ];
      render(<AgentThoughtStream agents={agents} />);

      const supervisor = screen.getByTestId("agent-supervisor");
      const label = supervisor.querySelector(".text-purple-500");
      expect(label).toBeInTheDocument();
    });

    test("drug_agent has blue color", () => {
      const agents: AgentStatus[] = [
        { name: "drug_agent", status: "running" },
      ];
      render(<AgentThoughtStream agents={agents} />);

      const agent = screen.getByTestId("agent-drug_agent");
      const label = agent.querySelector(".text-blue-500");
      expect(label).toBeInTheDocument();
    });

    test("pubmed_agent has green color", () => {
      const agents: AgentStatus[] = [
        { name: "pubmed_agent", status: "running" },
      ];
      render(<AgentThoughtStream agents={agents} />);

      const agent = screen.getByTestId("agent-pubmed_agent");
      const label = agent.querySelector(".text-green-500");
      expect(label).toBeInTheDocument();
    });

    test("guidelines_agent has orange color", () => {
      const agents: AgentStatus[] = [
        { name: "guidelines_agent", status: "running" },
      ];
      render(<AgentThoughtStream agents={agents} />);

      const agent = screen.getByTestId("agent-guidelines_agent");
      const label = agent.querySelector(".text-orange-500");
      expect(label).toBeInTheDocument();
    });

    test("synthesizer has pink color", () => {
      const agents: AgentStatus[] = [
        { name: "synthesizer", status: "running" },
      ];
      render(<AgentThoughtStream agents={agents} />);

      const agent = screen.getByTestId("agent-synthesizer");
      const label = agent.querySelector(".text-pink-500");
      expect(label).toBeInTheDocument();
    });
  });

  describe("Layout & Animation", () => {
    test("has slide-in animation", () => {
      const agents: AgentStatus[] = [
        { name: "supervisor", status: "running" },
      ];
      render(<AgentThoughtStream agents={agents} />);

      const container = screen.getByTestId("agent-thought-stream");
      expect(container.className).toContain("animate-in");
      expect(container.className).toContain("slide-in-from-top-4");
    });

    test("has fixed positioning", () => {
      const agents: AgentStatus[] = [
        { name: "supervisor", status: "running" },
      ];
      render(<AgentThoughtStream agents={agents} />);

      const container = screen.getByTestId("agent-thought-stream");
      expect(container.className).toContain("fixed");
      expect(container.className).toContain("top-20");
    });

    test("has backdrop blur", () => {
      const agents: AgentStatus[] = [
        { name: "supervisor", status: "running" },
      ];
      render(<AgentThoughtStream agents={agents} />);

      const container = screen.getByTestId("agent-thought-stream");
      const blurDiv = container.querySelector(".backdrop-blur-sm");
      expect(blurDiv).toBeInTheDocument();
    });

    test("has role=status for accessibility", () => {
      const agents: AgentStatus[] = [
        { name: "supervisor", status: "running" },
      ];
      render(<AgentThoughtStream agents={agents} />);

      const container = screen.getByTestId("agent-thought-stream");
      expect(container).toHaveAttribute("role", "status");
    });
  });

  describe("Mixed States", () => {
    test("renders mixed running/complete/idle states correctly", () => {
      const agents: AgentStatus[] = [
        { name: "supervisor", status: "complete" },
        { name: "drug_agent", status: "running" },
        { name: "pubmed_agent", status: "running" },
      ];
      render(<AgentThoughtStream agents={agents} />);

      expect(screen.getByTestId("agent-supervisor")).toHaveAttribute("data-status", "complete");
      expect(screen.getByTestId("agent-drug_agent")).toHaveAttribute("data-status", "running");
      expect(screen.getByTestId("agent-pubmed_agent")).toHaveAttribute("data-status", "running");
      expect(screen.getByTestId("agent-guidelines_agent")).toHaveAttribute("data-status", "idle");
      expect(screen.getByTestId("agent-synthesizer")).toHaveAttribute("data-status", "idle");
    });
  });

  describe("Snapshots", () => {
    test("single running agent", () => {
      const { container } = render(
        <AgentThoughtStream agents={[{ name: "supervisor", status: "running" }]} />
      );
      expect(container).toMatchSnapshot();
    });

    test("mixed states", () => {
      const { container } = render(
        <AgentThoughtStream
          agents={[
            { name: "supervisor", status: "complete" },
            { name: "drug_agent", status: "running" },
          ]}
        />
      );
      expect(container).toMatchSnapshot();
    });

    test("all complete", () => {
      const { container } = render(
        <AgentThoughtStream
          agents={[
            { name: "supervisor", status: "complete" },
            { name: "drug_agent", status: "complete" },
            { name: "pubmed_agent", status: "complete" },
            { name: "guidelines_agent", status: "complete" },
            { name: "synthesizer", status: "complete" },
          ]}
        />
      );
      expect(container).toMatchSnapshot();
    });
  });
});
