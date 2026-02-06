import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test.describe("Accessibility", () => {
  test("should not have WCAG 2.1 AA violations", async ({ page }) => {
    await page.goto("/");

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("should support keyboard navigation", async ({ page }) => {
    await page.goto("/");

    // Tab to skip link first, then to input
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");
    const input = page.locator('input[aria-label*="dotaz"]');
    await expect(input).toBeFocused();

    // Type query
    await page.keyboard.type("Test query");

    // Tab through buttons to send
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");
    await page.keyboard.press("Tab");
    const sendButton = page.locator('button[type="submit"]');
    await expect(sendButton).toBeFocused();

    // Submit with Enter
    await page.keyboard.press("Enter");
    await expect(page.locator("text=Test query")).toBeVisible();
  });

  test("should have proper ARIA labels", async ({ page }) => {
    await page.goto("/");

    const input = page.locator('input[aria-label*="dotaz"]');
    await expect(input).toBeVisible();

    const sendButton = page.locator('button[aria-label*="Odeslat"]');
    await expect(sendButton).toBeVisible();
  });

  test("should announce loading state to screen readers", async ({ page }) => {
    await page.goto("/");

    const input = page.locator('input[aria-label*="dotaz"]');
    await input.fill("Test");
    await page.locator('button[type="submit"]').click();

    const liveRegion = page.locator('[aria-live="polite"]');
    await expect(liveRegion).toHaveAttribute("aria-busy", "true");
  });
});
