"use client";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useTheme } from "next-themes";
import { Search, Plus, Trash2, ChevronRight, Sun, Moon } from "lucide-react";

const BUTTON_VARIANTS = [
  "default",
  "destructive",
  "outline",
  "secondary",
  "ghost",
  "link",
] as const;

const BUTTON_SIZES = ["xs", "sm", "default", "lg", "touch"] as const;

const ICON_SIZES = [
  "icon-xs",
  "icon-sm",
  "icon",
  "icon-lg",
  "icon-touch",
] as const;

const BADGE_VARIANTS = [
  "default",
  "secondary",
  "destructive",
  "outline",
  "ghost",
  "link",
] as const;

function ThemeSwitcher() {
  const { theme, setTheme } = useTheme();
  return (
    <Button
      variant="outline"
      size="sm"
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
    >
      {theme === "dark" ? <Sun className="size-4" /> : <Moon className="size-4" />}
      {theme === "dark" ? "Light" : "Dark"} Mode
    </Button>
  );
}

export default function DesignSystemPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="container mx-auto max-w-6xl p-8 space-y-16">
        {/* Header */}
        <header className="flex items-center justify-between border-b pb-6">
          <div>
            <h1 className="text-3xl font-bold">Design System</h1>
            <p className="text-muted-foreground mt-1">
              Czech MedAI - Pencil Compliance Documentation
            </p>
          </div>
          <ThemeSwitcher />
        </header>

        {/* Button Variants */}
        <section className="space-y-6">
          <h2 className="text-2xl font-bold">Button Variants</h2>
          <p className="text-muted-foreground">
            6 variant: default, destructive, outline, secondary, ghost, link
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
            {BUTTON_VARIANTS.map((variant) => (
              <div key={variant} className="space-y-3">
                <h3 className="text-sm font-medium capitalize text-muted-foreground">
                  {variant}
                </h3>
                <div className="space-y-2">
                  <Button variant={variant}>Button</Button>
                  <Button variant={variant} disabled>
                    Disabled
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Button Sizes */}
        <section className="space-y-6">
          <h2 className="text-2xl font-bold">Button Sizes</h2>
          <p className="text-muted-foreground">
            5 text sizes: xs, sm, default, lg, touch (min 44px)
          </p>
          <div className="flex items-end gap-4 flex-wrap">
            {BUTTON_SIZES.map((size) => (
              <div key={size} className="text-center space-y-2">
                <span className="text-xs text-muted-foreground block">
                  {size}
                </span>
                <Button size={size}>{size}</Button>
              </div>
            ))}
          </div>
        </section>

        {/* Icon Buttons */}
        <section className="space-y-6">
          <h2 className="text-2xl font-bold">Icon Buttons</h2>
          <p className="text-muted-foreground">
            5 icon sizes: icon-xs, icon-sm, icon, icon-lg, icon-touch
          </p>
          <div className="flex items-center gap-4 flex-wrap">
            {ICON_SIZES.map((size) => (
              <div key={size} className="text-center space-y-2">
                <span className="text-xs text-muted-foreground block">
                  {size}
                </span>
                <Button size={size} variant="outline">
                  <Search />
                </Button>
              </div>
            ))}
          </div>
        </section>

        {/* Button with Icons */}
        <section className="space-y-6">
          <h2 className="text-2xl font-bold">Buttons with Icons</h2>
          <div className="flex items-center gap-4 flex-wrap">
            <Button>
              <Plus /> Pridat
            </Button>
            <Button variant="destructive">
              <Trash2 /> Smazat
            </Button>
            <Button variant="outline">
              Dalsi <ChevronRight />
            </Button>
            <Button variant="ghost">
              <Search /> Hledat
            </Button>
          </div>
        </section>

        {/* Button States */}
        <section className="space-y-6">
          <h2 className="text-2xl font-bold">Button States</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-muted-foreground">
                Normal
              </h3>
              <Button>Normal</Button>
            </div>
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-muted-foreground">
                Disabled
              </h3>
              <Button disabled>Disabled</Button>
            </div>
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-muted-foreground">
                aria-invalid
              </h3>
              <Button aria-invalid="true">Invalid</Button>
            </div>
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-muted-foreground">
                asChild (link)
              </h3>
              <Button asChild>
                <a href="#">Link Button</a>
              </Button>
            </div>
          </div>
        </section>

        {/* Badge Variants */}
        <section className="space-y-6">
          <h2 className="text-2xl font-bold">Badge Variants</h2>
          <p className="text-muted-foreground">
            6 variant: default, secondary, destructive, outline, ghost, link
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
            {BADGE_VARIANTS.map((variant) => (
              <div key={variant} className="space-y-3">
                <h3 className="text-sm font-medium capitalize text-muted-foreground">
                  {variant}
                </h3>
                <div className="space-y-2">
                  <Badge variant={variant}>Badge</Badge>
                  <Badge variant={variant} asChild>
                    <a href="#">Link Badge</a>
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Badge States */}
        <section className="space-y-6">
          <h2 className="text-2xl font-bold">Badge States</h2>
          <div className="flex items-center gap-4 flex-wrap">
            <Badge>Normal</Badge>
            <Badge aria-invalid="true">Invalid</Badge>
            <Badge asChild>
              <a href="#">Focusable Link</a>
            </Badge>
          </div>
        </section>

        {/* Full Variant × Size Matrix */}
        <section className="space-y-6">
          <h2 className="text-2xl font-bold">
            Button Matrix (Variant x Size)
          </h2>
          <p className="text-muted-foreground">
            Complete 6x5 matrix = 30 text button combinations
          </p>
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className="text-left p-2 text-sm font-medium text-muted-foreground">
                    Variant \ Size
                  </th>
                  {BUTTON_SIZES.map((size) => (
                    <th
                      key={size}
                      className="p-2 text-sm font-medium text-muted-foreground"
                    >
                      {size}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {BUTTON_VARIANTS.map((variant) => (
                  <tr key={variant} className="border-t border-border">
                    <td className="p-2 text-sm font-medium capitalize">
                      {variant}
                    </td>
                    {BUTTON_SIZES.map((size) => (
                      <td key={size} className="p-2 text-center">
                        <Button variant={variant} size={size}>
                          Btn
                        </Button>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Color Palette */}
        <section className="space-y-6">
          <h2 className="text-2xl font-bold">Color Palette - Slate</h2>
          <p className="text-muted-foreground">
            OKLCH color space, auto-inverted for dark theme
          </p>
          <div className="grid grid-cols-5 md:grid-cols-11 gap-4">
            {[50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950].map((shade) => (
              <div key={shade} className="space-y-2">
                <div
                  className="h-16 rounded-lg border border-default"
                  style={{ backgroundColor: `var(--slate-${shade})` }}
                />
                <span className="text-xs text-muted-foreground block text-center">
                  {shade}
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* Semantic Colors */}
        <section className="space-y-6">
          <h2 className="text-2xl font-bold">Semantic Colors</h2>
          <p className="text-muted-foreground">
            Theme-aware semantic tokens for consistent UI
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <div className="h-16 rounded-lg bg-surface border border-default" />
              <h3 className="text-sm font-medium">surface</h3>
              <code className="text-xs text-muted-foreground">bg-surface</code>
            </div>
            <div className="space-y-2">
              <div className="h-16 rounded-lg bg-surface-elevated border border-default" />
              <h3 className="text-sm font-medium">surface-elevated</h3>
              <code className="text-xs text-muted-foreground">bg-surface-elevated</code>
            </div>
            <div className="space-y-2">
              <div className="h-16 rounded-lg bg-surface-muted border border-default" />
              <h3 className="text-sm font-medium">surface-muted</h3>
              <code className="text-xs text-muted-foreground">bg-surface-muted</code>
            </div>
            <div className="space-y-2">
              <div className="h-16 rounded-lg bg-background border border-default flex items-center justify-center">
                <span className="text-primary font-medium">Aa</span>
              </div>
              <h3 className="text-sm font-medium">text-primary</h3>
              <code className="text-xs text-muted-foreground">text-primary</code>
            </div>
            <div className="space-y-2">
              <div className="h-16 rounded-lg bg-background border border-default flex items-center justify-center">
                <span className="text-secondary font-medium">Aa</span>
              </div>
              <h3 className="text-sm font-medium">text-secondary</h3>
              <code className="text-xs text-muted-foreground">text-secondary</code>
            </div>
            <div className="space-y-2">
              <div className="h-16 rounded-lg bg-background border border-default flex items-center justify-center">
                <span className="text-tertiary font-medium">Aa</span>
              </div>
              <h3 className="text-sm font-medium">text-tertiary</h3>
              <code className="text-xs text-muted-foreground">text-tertiary</code>
            </div>
          </div>
        </section>

        {/* Border Tokens */}
        <section className="space-y-6">
          <h2 className="text-2xl font-bold">Border Tokens</h2>
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-2">
              <div className="h-16 rounded-lg border-2 border-default bg-background" />
              <h3 className="text-sm font-medium">border-default</h3>
              <code className="text-xs text-muted-foreground">border-default</code>
            </div>
            <div className="space-y-2">
              <div className="h-16 rounded-lg border-2 border-strong bg-background" />
              <h3 className="text-sm font-medium">border-strong</h3>
              <code className="text-xs text-muted-foreground">border-strong</code>
            </div>
          </div>
        </section>

        {/* Light/Dark Comparison */}
        <section className="space-y-6">
          <h2 className="text-2xl font-bold">Light/Dark Theme Comparison</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4 p-6 rounded-lg border border-default bg-background">
              <h3 className="text-lg font-semibold">Current Theme</h3>
              <div className="space-y-2">
                <div className="p-4 rounded bg-surface border border-default">
                  <p className="text-primary">Primary text</p>
                  <p className="text-secondary text-sm">Secondary text</p>
                  <p className="text-tertiary text-xs">Tertiary text</p>
                </div>
                <div className="p-4 rounded bg-surface-elevated border border-default">
                  <p className="text-primary">Elevated surface</p>
                </div>
                <div className="p-4 rounded bg-surface-muted border border-default">
                  <p className="text-primary">Muted surface</p>
                </div>
              </div>
            </div>

            <div className="space-y-4 p-6 rounded-lg border border-default bg-background">
              <h3 className="text-lg font-semibold">Token Mapping</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between p-2 rounded bg-surface-muted">
                  <code className="text-secondary">bg-surface</code>
                  <span className="text-tertiary">Page background</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-surface-muted">
                  <code className="text-secondary">bg-surface-elevated</code>
                  <span className="text-tertiary">Cards, modals</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-surface-muted">
                  <code className="text-secondary">bg-surface-muted</code>
                  <span className="text-tertiary">Disabled, skeleton</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-surface-muted">
                  <code className="text-secondary">text-primary</code>
                  <span className="text-tertiary">Headings, body</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-surface-muted">
                  <code className="text-secondary">text-secondary</code>
                  <span className="text-tertiary">Labels, captions</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-surface-muted">
                  <code className="text-secondary">text-tertiary</code>
                  <span className="text-tertiary">Placeholders</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-surface-muted">
                  <code className="text-secondary">border-default</code>
                  <span className="text-tertiary">Default borders</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-surface-muted">
                  <code className="text-secondary">border-strong</code>
                  <span className="text-tertiary">Emphasized borders</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t pt-6 text-sm text-muted-foreground">
          <p>
            Czech MedAI Design System | Pencil Compliance Audit |{" "}
            {new Date().toLocaleDateString("cs-CZ")}
          </p>
        </footer>
      </div>
    </div>
  );
}
