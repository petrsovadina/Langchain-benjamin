# UI Components - Pencil Compliance

## Button Component

### Variants (6)
- `default` - Primary action button (`bg-primary text-primary-foreground`)
- `destructive` - Dangerous actions (`bg-destructive text-white`)
- `outline` - Secondary actions with border (`border bg-background`)
- `secondary` - Tertiary actions (`bg-secondary text-secondary-foreground`)
- `ghost` - Minimal styling (`hover:bg-accent`)
- `link` - Text link styled as button (`text-primary underline-offset-4`)

### Sizes (10)
- `xs` - Extra small (h-6, text-xs)
- `sm` - Small (h-8)
- `default` - Default (h-9)
- `lg` - Large (h-10)
- `touch` - Touch-friendly (h-11, min 44px WCAG 2.1 AA)
- `icon` - Icon only (size-9)
- `icon-xs` - Icon extra small (size-6)
- `icon-sm` - Icon small (size-8)
- `icon-lg` - Icon large (size-10)
- `icon-touch` - Icon touch-friendly (size-11, min 44px)

### States
- Hover - `hover:bg-primary/90` (varies per variant)
- Focus - `focus-visible:ring-ring/50 focus-visible:ring-[3px]`
- Disabled - `disabled:opacity-50 disabled:pointer-events-none`
- Active - Native browser active state
- Invalid - `aria-invalid:ring-destructive/20 aria-invalid:border-destructive`

### Implementation
- Uses `cva()` (class-variance-authority) for variant management
- Uses `data-variant` and `data-size` attributes for testing/styling hooks
- Supports `asChild` prop via Radix `Slot.Root` for polymorphic rendering
- SVG icons auto-sized via `[&_svg:not([class*='size-'])]:size-4`

## Badge Component

### Variants (6)
- `default` - Primary badge (`bg-primary text-primary-foreground`)
- `secondary` - Secondary badge (`bg-secondary text-secondary-foreground`)
- `destructive` - Error/warning badge (`bg-destructive text-white`)
- `outline` - Bordered badge (`border-border text-foreground`)
- `ghost` - Minimal badge (transparent background)
- `link` - Link-styled badge (`text-primary underline-offset-4`)

### States
- Hover (anchor) - `[a&]:hover:bg-primary/90` (varies per variant)
- Focus - `focus-visible:ring-ring/50 focus-visible:ring-[3px]`
- Invalid - `aria-invalid:ring-destructive/20 aria-invalid:border-destructive`

### Implementation
- Uses `cva()` for variant management
- Pill shape via `rounded-full`
- Supports `asChild` prop for anchor links
- Hover styles scoped to anchor elements via `[a&]:hover`

## CitationBadge Component

### Design Tokens
- Hover - `bg-citation-badge-hover` (CSS variable)
- Active - `bg-citation-badge-active` (CSS variable)
- Text - `text-citation-badge-text` (CSS variable)
- Link - `text-citation-link` (CSS variable)

### Features
- HoverCard preview on hover/focus
- Click opens full citation dialog
- Keyboard accessible (Enter/Space)
- Touch-friendly (min 44x44px)
- Responsive text size (text-xs / md:text-sm)

## Design Tokens

All colors use OKLCH color space defined in `globals.css`:
- Light theme: `:root` block
- Dark theme: `.dark` block
- Tailwind mapping: `@theme inline` block

### Using Semantic Colors

**Prefer semantic tokens over hardcoded colors:**

```tsx
// BAD - Hardcoded colors
<div className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white">

// GOOD - Semantic tokens
<div className="bg-surface-elevated text-primary">
```

### Available Semantic Tokens

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `bg-surface` | slate-50 | slate-950 | Page background |
| `bg-surface-elevated` | white | slate-900 | Cards, modals |
| `bg-surface-muted` | slate-100 | slate-800 | Disabled, skeleton |
| `text-primary` | slate-900 | slate-50 | Headings, body text |
| `text-secondary` | slate-600 | slate-400 | Labels, captions |
| `text-tertiary` | slate-500 | slate-500 | Placeholders, hints |
| `border-default` | slate-200 | white/10% | Default borders |
| `border-strong` | slate-300 | white/15% | Emphasized borders |

### Citation-specific tokens
| Token | Light | Dark |
|-------|-------|------|
| `--citation-badge-hover` | `oklch(0.95 0.02 240)` | `oklch(0.20 0.08 240)` |
| `--citation-badge-active` | `oklch(0.90 0.04 240)` | `oklch(0.25 0.10 240)` |
| `--citation-badge-text` | `oklch(0.45 0.15 240)` | `oklch(0.65 0.12 240)` |
| `--citation-link` | `oklch(0.45 0.15 240)` | `oklch(0.65 0.12 240)` |

### Slate Palette

The slate palette auto-inverts in dark theme via CSS variables:

```tsx
// Slate palette auto-inverts in dark theme
<div className="bg-slate-100 text-slate-900">
  {/* Light: bg=#f1f5f9, text=#0f172a */}
  {/* Dark: bg=#0f172a, text=#f1f5f9 */}
</div>
```

## Testing

```bash
# Run all UI tests
npm run test -- __tests__/ui/

# Run with coverage
npm run test -- --coverage __tests__/ui/

# Run accessibility tests only
npm run test -- __tests__/ui/accessibility.test.tsx

# Run theme switching E2E tests
npm run test:e2e -- component-states.spec.ts
```

## Visual Documentation

Visit `/design-system` route for interactive component showcase with theme switcher, color palette, semantic tokens, and border tokens.
