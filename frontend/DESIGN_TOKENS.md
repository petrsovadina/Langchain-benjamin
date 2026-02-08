# Design Tokens Cheat Sheet

## Quick Reference

### Surface Colors
```tsx
bg-surface           // Page background
bg-surface-elevated  // Cards, modals, elevated UI
bg-surface-muted     // Disabled states, skeleton loaders
```

### Text Colors
```tsx
text-primary    // Headings, body text (high contrast)
text-secondary  // Labels, captions (medium contrast)
text-tertiary   // Placeholders, hints (low contrast)
```

### Border Colors
```tsx
border-default  // Default borders
border-strong   // Emphasized borders
```

## Migration Guide

**Replace hardcoded colors:**

| Old (Hardcoded) | New (Semantic) |
|-----------------|----------------|
| `bg-white dark:bg-slate-900` | `bg-surface-elevated` |
| `bg-slate-50 dark:bg-slate-950` | `bg-surface` |
| `bg-slate-100 dark:bg-slate-800` | `bg-surface-muted` |
| `bg-slate-200 dark:bg-slate-700` | `bg-surface-muted` |
| `text-slate-900 dark:text-white` | `text-primary` |
| `text-slate-900 dark:text-slate-100` | `text-primary` |
| `text-slate-600 dark:text-slate-400` | `text-secondary` |
| `text-slate-700 dark:text-slate-300` | `text-secondary` |
| `text-slate-500 dark:text-slate-400` | `text-tertiary` |
| `text-slate-500` | `text-tertiary` |
| `text-slate-400` | `text-tertiary` |
| `border-slate-200 dark:border-slate-700` | `border-default` |
| `border-slate-200 dark:border-slate-800` | `border-default` |

## Color Values (OKLCH)

**Light Theme:**
- surface: `oklch(0.984 0.003 247.858)` (#f8fafc)
- surface-elevated: `oklch(1 0 0)` (white)
- surface-muted: `oklch(0.968 0.007 247.896)` (#f1f5f9)
- text-primary: `oklch(0.208 0.042 265.755)` (#0f172a)
- text-secondary: `oklch(0.446 0.043 257.281)` (#475569)
- text-tertiary: `oklch(0.554 0.046 257.417)` (#64748b)

**Dark Theme:**
- surface: `oklch(0.129 0.042 264.695)` (#020617)
- surface-elevated: `oklch(0.208 0.042 265.755)` (#0f172a)
- surface-muted: `oklch(0.279 0.041 260.031)` (#1e293b)
- text-primary: `oklch(0.984 0.003 247.858)` (#f8fafc)
- text-secondary: `oklch(0.704 0.040 256.788)` (#94a3b8)
- text-tertiary: `oklch(0.554 0.046 257.417)` (#64748b)

## Best Practices

1. **Always use semantic tokens** for surfaces, text, borders
2. **Use slate palette** only for specific shades (e.g., agent idle dots)
3. **Test in both themes** before committing
4. **Avoid hardcoded colors** (bg-white, bg-slate-*, text-slate-*)
5. **Use design system page** (`/design-system`) for visual reference
