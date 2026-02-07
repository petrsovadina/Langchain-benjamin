import { test, expect } from "@playwright/test";

const BUTTON_VARIANTS = [
  "default",
  "destructive",
  "outline",
  "secondary",
  "ghost",
  "link",
] as const;

const BADGE_VARIANTS = [
  "default",
  "secondary",
  "destructive",
  "outline",
  "ghost",
  "link",
] as const;

test.describe("Design System Visual Regression", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/design-system");
    await page.waitForLoadState("networkidle");
  });

  test("full page screenshot - light theme", async ({ page }) => {
    // Ensure light theme
    await page.evaluate(() => {
      document.documentElement.classList.remove("dark");
    });
    await expect(page).toHaveScreenshot("design-system-light.png", {
      fullPage: true,
    });
  });

  test("full page screenshot - dark theme", async ({ page }) => {
    // Switch to dark theme
    await page.evaluate(() => {
      document.documentElement.classList.add("dark");
    });
    await expect(page).toHaveScreenshot("design-system-dark.png", {
      fullPage: true,
    });
  });

  BUTTON_VARIANTS.forEach((variant) => {
    test(`button ${variant} variant screenshot`, async ({ page }) => {
      const button = page.locator(`[data-variant="${variant}"][data-slot="button"]`).first();
      await expect(button).toHaveScreenshot(`button-${variant}.png`);
    });
  });

  BADGE_VARIANTS.forEach((variant) => {
    test(`badge ${variant} variant screenshot`, async ({ page }) => {
      const badge = page.locator(`[data-variant="${variant}"][data-slot="badge"]`).first();
      await expect(badge).toHaveScreenshot(`badge-${variant}.png`);
    });
  });

  test("button sizes comparison", async ({ page }) => {
    const sizesSection = page.locator("text=Button Sizes").locator("..");
    await expect(sizesSection).toHaveScreenshot("button-sizes.png");
  });

  test("icon buttons comparison", async ({ page }) => {
    const iconSection = page.locator("text=Icon Buttons").locator("..");
    await expect(iconSection).toHaveScreenshot("icon-buttons.png");
  });

  test("responsive - mobile viewport", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await expect(page).toHaveScreenshot("design-system-mobile.png", {
      fullPage: true,
    });
  });

  test("responsive - tablet viewport", async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page).toHaveScreenshot("design-system-tablet.png", {
      fullPage: true,
    });
  });
});
