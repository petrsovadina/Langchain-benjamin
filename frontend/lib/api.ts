export interface ConsultRequest {
  query: string;
  mode: "quick" | "deep";
  user_id?: string;
}

export interface RetrievedDocument {
  page_content: string;
  metadata: {
    source: string;
    source_type?: string;
    [key: string]: unknown;
  };
}

export interface ConsultResponse {
  answer: string;
  retrieved_docs: RetrievedDocument[];
  confidence?: number;
  latency_ms: number;
}

export interface SSEEvent {
  type:
    | "agent_start"
    | "agent_complete"
    | "final"
    | "done"
    | "error"
    | "cache_hit";
  agent?: string;
  answer?: string;
  retrieved_docs?: RetrievedDocument[];
  confidence?: number;
  latency_ms?: number;
  error?: string;
  detail?: string;
}

export async function sendMessage(
  request: ConsultRequest,
  onEvent: (event: SSEEvent) => void,
  onError: (error: Error) => void,
  onComplete: () => void
): Promise<void> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  let completed = false;

  const finish = () => {
    if (!completed) {
      completed = true;
      onComplete();
    }
  };

  try {
    const response = await fetch(`${apiUrl}/api/v1/consult`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("Response body is not readable");
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split("\n\n");
      buffer = blocks.pop() || "";

      for (const block of blocks) {
        if (!block.trim()) continue;

        // Collect all data: lines to handle multiline data correctly
        const dataLines: string[] = [];
        for (const line of block.split("\n")) {
          if (line.startsWith("data: ")) {
            dataLines.push(line.slice(6));
          } else if (line.startsWith("data:")) {
            dataLines.push(line.slice(5));
          }
        }

        if (dataLines.length === 0) continue;

        const data = dataLines.join("\n");

        try {
          const eventData = JSON.parse(data) as SSEEvent;

          if (eventData.type === "done") {
            finish();
          } else if (eventData.type === "error") {
            onError(
              new Error(eventData.detail || eventData.error || "Unknown error")
            );
          } else {
            onEvent(eventData);
          }
        } catch {
          // Skip malformed JSON blocks
        }
      }
    }

    // Stream closed without explicit done event
    finish();
  } catch (error) {
    if (!completed) {
      onError(error instanceof Error ? error : new Error("Unknown error"));
    }
  }
}
