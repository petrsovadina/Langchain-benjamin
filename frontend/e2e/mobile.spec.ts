import { test, expect } from "@playwright/test";

test.describe("Mobile Experience", () => {
  test.use({ viewport: { width: 375, height: 667 } }); // iPhone SE

  test("should have touch-friendly buttons (min 44px)", async ({ page }) => {
    await page.goto("/");

    const sendButton = page.locator('button[type="submit"]');
    const box = await sendButton.boundingBox();

    expect(box?.width).toBeGreaterThanOrEqual(44);
    expect(box?.height).toBeGreaterThanOrEqual(44);
  });

  test("should not have horizontal scroll", async ({ page }) => {
    await page.goto("/");

    const scrollWidth = await page.evaluate(
      () => document.documentElement.scrollWidth
    );
    const clientWidth = await page.evaluate(
      () => document.documentElement.clientWidth
    );

    expect(scrollWidth).toBeLessThanOrEqual(clientWidth);
  });

  test("should display omnibox correctly on mobile", async ({ page }) => {
    await page.goto("/");

    const omnibox = page.locator('form[role="search"]');
    await expect(omnibox).toBeVisible();

    const box = await omnibox.boundingBox();
    expect(box?.width).toBeLessThanOrEqual(375);
  });

  test("should handle swipe down to focus omnibox", async ({ page }) => {
    await page.goto("/");

    await page.evaluate(() => {
      const container = document.querySelector('[data-testid="chat-container"]');
      if (!container) return;

      container.dispatchEvent(
        new PointerEvent("pointerdown", {
          clientX: 187,
          clientY: 100,
          bubbles: true,
        })
      );
      container.dispatchEvent(
        new PointerEvent("pointerup", {
          clientX: 187,
          clientY: 300,
          bubbles: true,
        })
      );
    });

    const input = page.locator('input[aria-label="Zadejte lékařský dotaz"]');
    await expect(input).toBeFocused();
  });
});
