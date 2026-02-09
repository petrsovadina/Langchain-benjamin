import { test, expect } from "@playwright/test";

function buildSSEBody(events: Array<{ type: string; [key: string]: unknown }>) {
  return events.map((e) => `data: ${JSON.stringify(e)}\n\n`).join("");
}

const MOCK_CITATION_EVENTS = [
  { type: "agent_start", agent: "drug_agent" },
  { type: "agent_complete", agent: "drug_agent" },
  {
    type: "final",
    answer:
      "Metformin je lek prvni volby pro diabetes mellitus 2. typu [1]. Studie potvrzuji jeho ucinnost [2].",
    retrieved_docs: [
      {
        page_content: "SUKL informace o metforminu",
        metadata: {
          source: "sukl",
          source_type: "drug_search",
          registration_number: "0012345",
          atc_code: "A10BA02",
        },
      },
      {
        page_content: "PubMed article about metformin efficacy",
        metadata: {
          source: "PubMed",
          pmid: "12345678",
          url: "https://pubmed.ncbi.nlm.nih.gov/12345678",
          title: "Efficacy of Metformin in T2DM",
          authors: "Smith, John; Doe, Jane",
          journal: "NEJM",
          publication_date: "2024-06-15",
          doi: "10.1056/NEJMoa2401234",
        },
      },
    ],
    confidence: 0.92,
    latency_ms: 3200,
  },
  { type: "done" },
];

async function mockConsultEndpoint(page: import("@playwright/test").Page) {
  await page.route("**/api/v1/consult", async (route) => {
    const body = buildSSEBody(MOCK_CITATION_EVENTS);
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      body,
    });
  });
}

test.describe("Citation Rendering", () => {
  test.beforeEach(async ({ page }) => {
    await mockConsultEndpoint(page);
    await page.goto("http://localhost:3000");
  });

  test("displays inline citation badges and references section", async ({
    page,
  }) => {
    await page.fill("textarea, input", "Jaké jsou kontraindikace metforminu?");
    await page.click('button[type="submit"]');

    await page.waitForSelector('[data-testid="assistant-message"]');

    const citationBadges = page.locator('[data-testid="citation-badge"]');
    await expect(citationBadges).toHaveCount(2);

    await expect(page.locator("text=Reference")).toBeVisible();
    await expect(page.locator("text=SUKL Reg. 0012345")).toBeVisible();
  });

  test("citation popup opens on click", async ({ page }) => {
    await page.fill("textarea, input", "Test dotaz");
    await page.click('button[type="submit"]');

    await page.waitForSelector('[data-testid="citation-badge"]');

    await page.locator('[data-testid="citation-badge"]').first().click();

    await expect(page.locator('[role="dialog"]')).toBeVisible();
    await expect(page.locator("text=Citace [1]")).toBeVisible();
  });

  test("references section shows all citations", async ({ page }) => {
    await page.fill("textarea, input", "Test dotaz");
    await page.click('button[type="submit"]');

    await page.waitForSelector("text=Reference");

    await expect(page.locator("text=[1]")).toBeVisible();
    await expect(page.locator("text=[2]")).toBeVisible();
    await expect(page.locator("text=Otevrit zdroj")).toHaveCount(1); // Only PubMed has url
  });
});
