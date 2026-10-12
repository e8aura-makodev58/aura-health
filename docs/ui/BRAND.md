# AURA Brand & Design System

*Headspace in feel, not in brand. Warm, bright, friendly, calm. Original AURA identity.*

## Palette

| Token | Hex | Use |
|---|---|---|
| `--surface` | `#fbfaf7` | Page background — warm off-white |
| `--surface-raised` | `#ffffff` | Cards, raised surfaces |
| `--ink` | `#2a2320` | Body text, headings — warm dark ink |
| `--ink-soft` | `#6b6258` | Secondary text, captions |
| `--line` | `#eee9e0` | Borders, dividers |
| `--accent-sunny` | `#f5a623` | Primary accent — sunny orange (fills, not text on white) |
| `--accent-coral` | `#f47e6b` | Warm secondary accent |
| `--accent-blue` | `#7bc4e4` | Cool secondary accent |
| `--accent-lilac` | `#c4b4e0` | Soft secondary accent |
| `--accent-leaf` | `#8cc499` | Calm green accent (continuity with prior sage) |
| `--accent` | `#e8950c` | Default interactive accent (darker sunny orange for AA on white) |
| `--accent-ink` | `#c2780a` | Hover / pressed accent |
| `--warning-bg` | `#fff4d6` | Safety panel background (retained) |
| `--warning-border` | `#d4a943` | Safety panel border (retained) |
| `--focus` | `#005c8a` | Focus outline — high-contrast blue |

### Dark-on-accent rule
Bright orange/yellow fail as text on white. Use them as **fills with `--ink` text on top**, or as decorative elements. Text links use `--accent` (darker orange, AA-compliant on white at 14px+).

## Type scale

Self-hosted **Nunito** (SIL OFL, variable or two weights: 400/700, `.woff2` under 150 KB).

| Role | Size | Weight | Line height |
|---|---|---|---|
| H1 (hero) | `clamp(2rem, 5vw, 2.6rem)` | 700 | 1.2 |
| H2 (section) | `1.2rem` | 700 | 1.35 |
| H3 (card) | `1rem` | 700 | 1.4 |
| Body | `1rem` | 400 | 1.6 |
| Small / fine | `0.8rem` | 400 | 1.6 |
| Eyebrow | `0.68rem` | 700, uppercase, tracking 0.12em | 1 |

## Radius scale (4 px grid)

| Token | Value | Use |
|---|---|---|
| `--radius-sm` | `8px` | Badges, chips, small inputs |
| `--radius-md` | `14px` | Inputs, small cards |
| `--radius-lg` | `20px` | Cards |
| `--radius-xl` | `28px` | Hero cards, big feature cards |
| `--radius-pill` | `999px` | Buttons, pills |

## Shadow scale

| Token | Value | Use |
|---|---|---|
| `--shadow-sm` | `0 1px 3px rgba(42,35,32,0.06)` | Cards default |
| `--shadow-md` | `0 4px 16px rgba(42,35,32,0.08)` | Raised cards, buttons on hover |
| `--shadow-lg` | `0 8px 32px rgba(42,35,32,0.10)` | Hero, modals, floating elements |
| `--shadow-pill` | `0 3px 12px rgba(232,149,12,0.18)` | Help dock pill |

## Spacing scale (4/8 px grid)

`4 · 8 · 12 · 16 · 20 · 24 · 32 · 40 · 48` — exposed as `--sp-1` through `--sp-8`.

## Illustration style

- **Flat vector, rounded organic shapes.** No outlines. Soft blob backgrounds.
- Palette: warm off-white base with sunny orange, soft blue, lilac, coral, leaf green fills.
- Simple, calm scenes — a sunrise, a cup of tea, a resting moon, a gentle hill.
- **No characters from other brands.** No faces that judge (no sad/worried expressions).
- Decorative only: `alt=""` or `aria-hidden="true"`.
- SVG preferred (under 60 KB); WebP acceptable (under 150 KB).
- One consistent style across the full set — use Miora style memory.

## Do / Don't

**Do:**
- Use warm accents as fills with dark ink text on top.
- Keep one clear main action per screen.
- Big rounded cards (20–28px), pill buttons, soft shadows, generous whitespace.
- Short, sentence-case headings in everyday words (patient side).
- Calm motion: 200–400ms ease-out fades, breathing shapes for loading.

**Don't:**
- Don't use bright orange/yellow as text on white — they fail AA.
- Don't add gamification (streaks, badges, points, counters, confetti).
- Don't show faces that judge — no sad, worried, or disappointed expressions.
- Don't theme the safety panel playfully — keep its warning colour, wording, and sticky position.
- Don't use Headspace name, logo, characters, fonts, or exact colour values.
- Don't add inline `style=""`, inline `<script>`, external fonts or CDNs (CSP blocks them).
- Don't create new `.css` or `.js` files — only `aura_ui/media/` accepts new files.
