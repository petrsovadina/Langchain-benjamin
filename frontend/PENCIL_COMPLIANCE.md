# Pencil Design Compliance Checklist

## Button Component

### Variants
- [x] `default` - bg-primary text-primary-foreground hover:bg-primary/90
- [x] `destructive` - bg-destructive text-white hover:bg-destructive/90
- [x] `outline` - border bg-background hover:bg-accent
- [x] `secondary` - bg-secondary text-secondary-foreground hover:bg-secondary/80
- [x] `ghost` - hover:bg-accent hover:text-accent-foreground
- [x] `link` - text-primary underline-offset-4 hover:underline

### Sizes
- [x] `xs` - h-6 (24px)
- [x] `sm` - h-8 (32px)
- [x] `default` - h-9 (36px)
- [x] `lg` - h-10 (40px)
- [x] `touch` - h-11 (44px, WCAG 2.1 AA minimum)
- [x] `icon` - size-9 (36px)
- [x] `icon-xs` - size-6 (24px)
- [x] `icon-sm` - size-8 (32px)
- [x] `icon-lg` - size-10 (40px)
- [x] `icon-touch` - size-11 (44px, WCAG 2.1 AA minimum)

### States
- [x] Hover state (all variants)
- [x] Focus-visible state (ring-ring/50, ring-[3px])
- [x] Disabled state (opacity-50, pointer-events-none)
- [x] Active state (native browser)
- [x] Invalid state (aria-invalid:ring-destructive/20)

### Architecture
- [x] Uses cva() for variant management
- [x] Uses design tokens (CSS variables via OKLCH)
- [x] Light/dark theme support
- [x] data-variant attribute for testing
- [x] data-size attribute for testing
- [x] data-slot="button" for styling hooks
- [x] asChild support via Radix Slot

### Quality
- [x] Unit test coverage (button.test.tsx)
- [x] Snapshot tests for visual regression
- [x] Accessibility tests (axe-core)
- [x] Keyboard navigation tests
- [x] Visual documentation (/design-system)

## Badge Component

### Variants
- [x] `default` - bg-primary text-primary-foreground [a&]:hover:bg-primary/90
- [x] `secondary` - bg-secondary text-secondary-foreground [a&]:hover:bg-secondary/90
- [x] `destructive` - bg-destructive text-white [a&]:hover:bg-destructive/90
- [x] `outline` - border-border text-foreground [a&]:hover:bg-accent
- [x] `ghost` - [a&]:hover:bg-accent [a&]:hover:text-accent-foreground
- [x] `link` - text-primary [a&]:hover:underline

### States
- [x] Hover state (anchor-scoped via [a&])
- [x] Focus-visible state (ring-ring/50, ring-[3px])
- [x] Invalid state (aria-invalid:ring-destructive/20)

### Architecture
- [x] Uses cva() for variant management
- [x] Uses design tokens (CSS variables via OKLCH)
- [x] Light/dark theme support
- [x] data-variant attribute for testing
- [x] data-slot="badge" for styling hooks
- [x] Pill shape (rounded-full)
- [x] asChild support via Radix Slot

### Quality
- [x] Unit test coverage (badge.test.tsx)
- [x] Snapshot tests for visual regression
- [x] Accessibility tests (axe-core)
- [x] Keyboard navigation tests
- [x] Visual documentation (/design-system)

## CitationBadge Component

### Design Token Integration
- [x] hover: bg-citation-badge-hover (was: bg-blue-50 / dark:bg-blue-900)
- [x] active: bg-citation-badge-active (was: bg-blue-100 / dark:bg-blue-800)
- [x] text: text-citation-badge-text (was: text-blue-600 / dark:text-blue-400)
- [x] link: text-citation-link (was: text-blue-600)
- [x] description: text-muted-foreground (was: text-slate-600 / dark:text-slate-400)

### Features
- [x] HoverCard integration (hover/focus trigger)
- [x] Click handler for full dialog
- [x] Keyboard accessible (Enter/Space)
- [x] Touch-friendly (min 44x44px)
- [x] Responsive sizing (text-xs / md:text-sm)
- [x] ARIA label with citation number and short text
- [x] aria-haspopup="dialog"

## Design Token System

### Color Tokens
- [x] OKLCH color space for perceptual uniformity
- [x] Light theme (:root) - 11 slate shades + semantic tokens
- [x] Dark theme (.dark) - inverted slate shades + semantic tokens
- [x] Semantic surface tokens (surface, surface-elevated, surface-muted)
- [x] Semantic text tokens (text-primary, text-secondary, text-tertiary)
- [x] Semantic border tokens (border-default, border-strong)
- [x] Citation-specific tokens (4 variables)

### Spacing Tokens
- [x] Tailwind default spacing scale (0-96)
- [x] Safe-area padding support (pb-safe)
- [x] WCAG touch target minimum (44px = spacing-11)

### Font Size Tokens
- [x] 8 font sizes (xs to 4xl)
- [x] Line height tokens (none, tight, snug, normal, relaxed, loose)

### Border Radius Tokens
- [x] 7 radius sizes (sm to 4xl)
- [x] Based on --radius CSS variable (0.625rem)

### Component Compliance
- [x] All components use semantic tokens (no hardcoded colors)
- [x] Full light/dark theme support
- [x] No bg-white, bg-slate-*, text-slate-* hardcoded classes
- [x] Backwards compatible (bg-slate-200 still works via CSS variables)

## Design System Infrastructure

### CSS Variables
- [x] OKLCH color space for perceptual uniformity
- [x] Light theme (:root)
- [x] Dark theme (.dark)
- [x] Citation-specific tokens (4 variables)
- [x] @theme inline mapping for Tailwind v4

### Tailwind Configuration
- [x] Custom breakpoints (xs: 375px)
- [x] Safe-area padding support
- [x] Citation color tokens in theme.extend.colors
- [x] Semantic color tokens (surface, text, border)
- [x] Slate palette via CSS variables
- [x] Font size tokens with line heights
- [x] Border radius tokens

### Testing Infrastructure
- [x] Vitest + React Testing Library
- [x] jest-axe for accessibility auditing
- [x] Snapshot testing for visual regression
- [x] userEvent for keyboard interaction testing
- [x] Theme switching E2E tests (light/dark)

### Documentation
- [x] components/ui/README.md - Component reference
- [x] PENCIL_COMPLIANCE.md - This compliance checklist
- [x] DESIGN_TOKENS.md - Design tokens cheat sheet
- [x] /design-system page - Interactive visual documentation with color palette
- [x] Visual regression tests (Playwright)
