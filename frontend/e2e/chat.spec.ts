import { test, expect } from "@playwright/test";

/**
 * Helper: builds a deterministic SSE body from an array of SSEEvent-shaped objects.
 * Each object is sent as a `data:` line followed by a blank line (standard SSE framing).
 */
function buildSSEBody(events: Record<string, unknown>[]): string {
  return events.map((e) => `data: ${JSON.stringify(e)}\n\n`).join("");
}

/** Deterministic SSE events returned by the mock backend. */
const MOCK_SSE_EVENTS = [
  { type: "agent_start", agent: "Supervisor" },
  { type: "agent_start", agent: "Drug Agent" },
  { type: "agent_complete", agent: "Drug Agent" },
  { type: "agent_complete", agent: "Supervisor" },
  {
    type: "final",
    answer:
      "**Metformin** je kontraindikován u pacientů s těžkou renální insuficiencí [1].",
    retrieved_docs: [
      {
        page_content: "Metformin contraindications...",
        metadata: { source: "SÚKL", source_type: "drug" },
      },
    ],
    confidence: 0.95,
    latency_ms: 1234,
  },
  { type: "done" },
];

/**
 * Intercepts POST /api/v1/consult and responds with a deterministic SSE stream.
 * All tests run fully offline against this mock.
 */
async function mockConsultEndpoint(page: import("@playwright/test").Page) {
  await page.route("**/api/v1/consult", (route) => {
    route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      headers: {
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
      body: buildSSEBody(MOCK_SSE_EVENTS),
    });
  });
}

test.describe("Chat Interface", () => {
  test("should display Zen Mode on initial load", async ({ page }) => {
    await page.goto("http://localhost:3000");

    const omnibox = page.locator(
      'input[placeholder*="Zadejte lékařský dotaz"]'
    );
    await expect(omnibox).toBeVisible();
    await expect(omnibox).toBeFocused();
  });

  test("should transition to Active Consultation after sending message", async ({
    page,
  }) => {
    await mockConsultEndpoint(page);
    await page.goto("http://localhost:3000");

    const omnibox = page.locator(
      'input[placeholder*="Zadejte lékařský dotaz"]'
    );
    await omnibox.fill("Jaké jsou kontraindikace metforminu?");
    await page.locator('button[type="submit"]').click();

    await expect(
      page.locator("text=Jaké jsou kontraindikace metforminu?")
    ).toBeVisible();

    const omniboxContainer = page.locator("form").first();
    await expect(omniboxContainer).toHaveClass(/fixed bottom-/);
  });

  test("should display Agent Thought Stream during processing", async ({
    page,
  }) => {
    await mockConsultEndpoint(page);
    await page.goto("http://localhost:3000");

    const omnibox = page.locator(
      'input[placeholder*="Zadejte lékařský dotaz"]'
    );
    await omnibox.fill("Test query");
    await page.locator('button[type="submit"]').click();

    await expect(
      page.locator("text=/Supervisor|Drug Agent|PubMed Agent/")
    ).toBeVisible({ timeout: 5000 });
  });

  test("should render markdown in assistant response", async ({ page }) => {
    await mockConsultEndpoint(page);
    await page.goto("http://localhost:3000");

    const omnibox = page.locator(
      'input[placeholder*="Zadejte lékařský dotaz"]'
    );
    await omnibox.fill("Test markdown");
    await page.locator('button[type="submit"]').click();

    await page.waitForSelector(".prose", { timeout: 10000 });

    const prose = page.locator(".prose");
    await expect(prose).toBeVisible();
  });
});
