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
