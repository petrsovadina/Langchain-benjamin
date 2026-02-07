import { test, expect } from "@playwright/test";

/**
 * Helper: builds a deterministic SSE body from an array of SSEEvent-shaped objects.
 */
function buildSSEBody(events: Record<string, unknown>[]): string {
  return events.map((e) => `data: ${JSON.stringify(e)}\n\n`).join("");
}

const MOCK_SSE_EVENTS = [
  { type: "agent_start", agent: "Supervisor" },
  { type: "agent_start", agent: "Drug Agent" },
  { type: "agent_complete", agent: "Drug Agent" },
  { type: "agent_complete", agent: "Supervisor" },
  {
    type: "final",
    answer: "**Metformin** je lék první volby u diabetu 2. typu [1].",
    retrieved_docs: [
      {
        page_content: "Metformin information...",
        metadata: { source: "PubMed", pmid: "12345678" },
      },
    ],
    confidence: 0.95,
    latency_ms: 1234,
  },
  { type: "done" },
];

test.describe("Component States Visual Regression", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/consult", (route) =>
      route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body: buildSSEBody(MOCK_SSE_EVENTS),
      })
    );
  });

  test.describe("Omnibox States", () => {
    test("default state", async ({ page }) => {
      await page.goto("/");
      const omnibox = page.locator('[data-testid="omnibox"]');
      await expect(omnibox).toBeVisible();
      await expect(omnibox).toHaveScreenshot("omnibox-default.png");
    });

    test("focus state", async ({ page }) => {
      await page.goto("/");
      const input = page.getByLabel("Zadejte lékařský dotaz");
      await input.focus();
      const omnibox = page.locator('[data-testid="omnibox"]');
      await expect(omnibox).toHaveScreenshot("omnibox-focus.png");
    });

    test("error state", async ({ page }) => {
      await page.route("**/api/consult", (route) =>
        route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({ error: "Internal server error" }),
        })
      );
      await page.goto("/");
      const input = page.getByLabel("Zadejte lékařský dotaz");
      await input.fill("test query");
      await input.press("Enter");
      // Wait for error to appear
      await page.waitForSelector('[role="alert"]', { timeout: 5000 });
      await expect(page.locator("form[role='search']")).toHaveScreenshot(
        "omnibox-error.png"
      );
    });
  });

  test.describe("AssistantMessage States", () => {
    test("with citations - border accent", async ({ page }) => {
      await page.goto("/");
      const input = page.getByLabel("Zadejte lékařský dotaz");
      await input.fill("Metformin kontraindikace");
      await input.press("Enter");
      // Wait for response
      await page.waitForSelector('[data-testid="assistant-message"]', {
        timeout: 10000,
      });
      const message = page.locator('[data-testid="assistant-message"]').last();
      await expect(message).toHaveScreenshot("assistant-with-citations.png");
    });
  });

  test.describe("CitationBadge States", () => {
    test.beforeEach(async ({ page }) => {
      await page.goto("/");
      const input = page.getByLabel("Zadejte lékařský dotaz");
      await input.fill("Metformin");
      await input.press("Enter");
      await page.waitForSelector('[data-testid="citation-badge"]', {
        timeout: 10000,
      });
    });

    test("default state", async ({ page }) => {
      const badge = page.locator('[data-testid="citation-badge"]').first();
      await expect(badge).toHaveScreenshot("citation-badge-default.png");
    });

    test("hover state", async ({ page }) => {
      const badge = page.locator('[data-testid="citation-badge"]').first();
      await badge.hover();
      await expect(badge).toHaveScreenshot("citation-badge-hover.png");
    });

    test("focus state", async ({ page }) => {
      const badge = page.locator('[data-testid="citation-badge"]').first();
      await badge.focus();
      await expect(badge).toHaveScreenshot("citation-badge-focus.png");
    });
  });

  test.describe("Responsive States", () => {
    test("mobile omnibox (375px)", async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto("/");
      const omnibox = page.locator('[data-testid="omnibox"]');
      await expect(omnibox).toBeVisible();
      await expect(omnibox).toHaveScreenshot("omnibox-mobile.png");
    });

    test("desktop omnibox (1440px)", async ({ page }) => {
      await page.setViewportSize({ width: 1440, height: 900 });
      await page.goto("/");
      const omnibox = page.locator('[data-testid="omnibox"]');
      await expect(omnibox).toBeVisible();
      await expect(omnibox).toHaveScreenshot("omnibox-desktop.png");
    });
  });

  test.describe("Dark Theme States", () => {
    test("omnibox dark mode", async ({ page }) => {
      await page.goto("/");
      await page.evaluate(() => {
        document.documentElement.classList.add("dark");
      });
      const omnibox = page.locator('[data-testid="omnibox"]');
      await expect(omnibox).toHaveScreenshot("omnibox-dark.png");
    });
  });
});
