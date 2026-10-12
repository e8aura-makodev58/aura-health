# CodeBuddy SOW: UI/UX aesthetics and marketability

2026-10-12. Claude, for the user. Statement of work for CodeBuddy (or WorkBuddy). It narrows
section 3 of [`WORKBUDDY_HANDOFF.md`](WORKBUDDY_HANDOFF.md) to a visual redesign. The
boundaries in section 4 of that brief still apply in full. Where this SOW and the brief
disagree, the brief's section 4 wins.

## 0. Read first (in this order, then stop reading)
1. This SOW.
2. `docs/WORKBUDDY_HANDOFF.md` sections 4 (boundaries) and 10 (repo map).
3. `aura_ui/README.md`, `aura_ui/media/README.md`.
4. `docs/PATIENT_VOICE_SPEC.md` and `docs/PLAIN_LANGUAGE_SPEC.md` (skim: tone and banned terms).

You do not need anything else. The whole job is in `aura_ui/` (nine files, about 180 KB, plain
HTML/CSS/JS, no build step) plus `tests/browser/`.

## 1. Goal
Make AURA look like a product people would want to open every day and a clinic would want to
buy. The visual reference is the **Headspace app**: warm, bright, friendly, simple, calm.
Today's UI is a tidy, muted sage-green prototype. It should feel like a finished consumer
health product on the patient side and a calm, trustworthy tool on the clinician side.

**Target market (who must be convinced):**
- Adults aged 25–60 on stable antidepressant maintenance treatment. They use it on a phone,
  often tired or low. The app must feel gentle, never clinical or judging.
- Their clinicians (psychiatrists, GPs, nurses in Singapore and the wider APAC region). They
  use it on a laptop between appointments and need to see what changed and when in seconds.
- Buyers and judges (clinic groups, insurers/employers, the hackathon panel). They see a
  three-minute demo and decide whether it looks real and sellable.

## 2. "Like Headspace" means the feel, not the brand
**Take from Headspace (design language):**
- Warm, saturated accents on a soft off-white background: sunny orange/yellow, soft blue,
  lilac, coral, with a dark ink colour for text. Plenty of whitespace.
- A rounded, geometric, friendly sans-serif. Large, short, sentence-case headings.
- Big rounded cards (20–28 px corners), pill-shaped buttons, few borders, soft shadows.
- Simple flat illustrations: round shapes, organic blobs, simple characters or scenes.
  Illustration carries the mood and text stays short.
- One clear main action per screen. Calm, slow motion (a breathing circle, gentle fades).
- A time-of-day feel, such as a warm morning and a cooler evening palette (optional).

**Do not take (legal and integrity):**
- No Headspace name, logo (the orange dot), characters, illustrations, icons, screenshots,
  fonts (theirs are proprietary) or exact colour values. Do not trace or recreate their art.
  AURA keeps its own name and gets its own mark. The page must never look like a
  Headspace product.
- No gamification. That means no streaks, badges, points, "minutes" counters, levels or
  celebratory confetti. Section 4 of the brief bans streaks and scores. Praise is never tied
  to health data.
- No faces that judge. Characters must never look sad, worried or disappointed, for example
  after a "Rough" check-in or when data is missing. Missing data is never shown as bad.
- The **safety panel is not themed playful.** It may use the new font and spacing, but it
  keeps its warning colour, its wording and its sticky position. The patient help button
  ("I want to mention something") stays at least as prominent as now. Making it a bolder
  pill is welcome.

## 3. Two modes, one brand
| | Patient ("Calm" mode) | Clinician ("Clinic" mode) |
|---|---|---|
| Device | phone first (390 px), works at 1280 | laptop first (1280 px), works at 390 |
| Feel | Headspace-like: warm, illustrated, spacious | same tokens, cooler and quieter, denser, data first |
| Colour | warm accents, illustration backgrounds | neutral surfaces, accents only for highlights and chart series |
| Illustration | hero, empty states, loading | empty states only |
| Text | short, everyday words | exact values, units, dates and sources stay (plain-language spec) |

Clinicians must still trust the clinician view. The Headspace feel applies to the brand and
the patient side, and the clinician view borrows only the typography, shapes and palette.

## 4. Work packages (do them in this order; one or more commits each)
**D0. Audit (short).** Take before screenshots of the empty/welcome state, patient home,
clinician view, review page and demo guide at 1280 and 390 px. Write `docs/ui/BRAND.md`
(at most one page) covering the palette, type scale, radii, shadows, spacing, the illustration
style and a do/don't list. If you use Miora for a moodboard, export 3–6 images to
`docs/ui/moodboard/` (not served).

**D1. Design tokens and type.** Rebuild the `:root` tokens in `styles.css`: colour (surfaces,
ink, muted, 4–5 accents, warning, focus), radius scale, shadow scale, spacing scale (4/8 px
grid), type scale. Replace hard-coded colours in `styles.css` and `evidence.css` with tokens.
Self-host one open-licence rounded sans (for example Nunito, Quicksand or DM Sans; SIL OFL)
as `.woff2` in `aura_ui/media/`, with its licence file next to it. Use at most two weights
or one variable file, under 150 KB total.
*Done when:* no hex colour outside `:root` (chart series may use tokens via CSS variables),
fonts load from `/assets/media/`, and nothing regresses at 390 px.

**D2. Brand mark and illustrations.** Make a new original AURA mark that replaces the "A in a
circle" SVG in the masthead. Then make an illustration set in one consistent style, as SVG
(preferred) or WebP:
- welcome / first screen
- patient home hero, optionally in morning / afternoon / evening variants
- "nothing new to note" calm state
- loading (an animatable shape, such as a breathing circle)
- appointment note / review page
- an empty clinician state

Keep each illustration under 500 KB (user-approved budget, 2026-10-12). Illustrations are decorative and use
`alt=""` or `aria-hidden="true"`. Miora is a good tool for this (see section 7).
The placeholder `calm-sun.svg` was replaced by CodeBuddy's set.

**D3. First impression and demo entry.** Turn the welcome state (`#empty-state`) into a
confident landing. It needs a one-line value proposition, the hero illustration, and two
clear tiles: "See the patient's day" and "See what the clinician sees". Add a visible "Play
the 3-minute story" entry into the existing demo guide. Developer tools stay tucked away.
Synthetic-data honesty stays visible but small.

**D4. Patient home (Calm mode).** Add a time-of-day greeting using everyday words. Make the
AI recap sentence the hero, on a soft illustrated card. While it generates, show a calm
placeholder (breathing shape plus a short line, not a spinner) and swap it in without
flicker. Restyle the check-in as large rounded choices; the "Good / Okay / Rough" icons must
not be judging faces. Show "See what changed", "Why this summary?" and the appointment note
as soft secondary tiles. The help dock is a bold, friendly pill, always visible. The page
has no charts (DECISIONS §43).

**D5. Clinician view (Clinic mode).** Order the page as: headline → finding cards →
what-changed-when strip → charts. Restyle the cards and charts with the tokens and keep one
colour per signal across the whole page. Use a two-column layout at ≥1100 px if it helps.
Collapse secondary sections so the first screen answers "what changed and when". Keep every
value, unit, date and source. Keep the HRV and skin-temperature icons consistent with the
other icons.

**D6. Motion and states.** Use gentle transitions (200–400 ms, ease-out). Highlight what
changed after a simulator event; a soft glow or an "Updated" chip is enough. Make empty
states friendly and loading states calm. Respect `prefers-reduced-motion`: no animation
when it is set.

**D7. Accessibility and QA.** WCAG AA contrast. Bright orange and yellow usually fail as
text on white, so use them as fills with dark ink on top. Keep visible focus outlines,
44 px touch targets, labels and logical heading order. Run all browser suites. Take after
screenshots at 1280 and 390 px for every screen from D0 and add them to your Log entry in
`HANDOVER.md`.

**D8 (optional). Submission visuals.** A 16:9 cover image (at least 380×216; make it
1520×864 and scale it down) in the same style, plus a few key frames for the demo video.
These are not code; put them in `docs/submission/`.

## 5. Technical constraints you will hit
- **Security policy:** the page's CSP allows only same-origin scripts, styles, fonts and
  images (`data:` images too). Google Fonts and other CDNs, inline `<script>`, inline
  `<style>` and `style="..."` attributes are blocked. Put CSS in `styles.css` or
  `evidence.css`. Setting `element.style.x` from JS works.
- **New files:** only `aura_ui/media/` accepts new files, served at `/assets/media/<name>`
  (`.svg .png .webp .jpg .woff2`, lowercase flat names, no subfolders). Do not add new
  `.css` or `.js` files: the server serves only the existing seven and cannot be changed by
  you (`aura_app/` is protected). If you really need more, ask in `HANDOVER.md`.
- **No new dependencies,** frameworks or build steps. Stay with plain CSS and JS.
- **Visible text** still goes through `window.auraPlain` or `node()`, and the plain-language
  lint must keep passing. New greetings and labels must use everyday words.
- **Tests that check headings or classes** (`impression.cjs`, `final_dash.cjs`,
  `dual_view.cjs`, etc.) may need their assertions updated when you rename something on
  purpose. Say which ones in the commit message. Never weaken safety, help-button or
  "Not sent" assertions.
- **Local preview:** run the app as in brief section 5. Without an AI provider key the app
  shows its built-in fallback summaries. That is fine for visual work. The live DeepSeek
  text only appears on the hosted demo after the user deploys.

## 6. Branch, review and acceptance
- Branch `codebuddy/ui` from the tag `pre-workbuddy`. Use small commits. Do not force push,
  push to `main` or deploy.
- `git diff pre-workbuddy --stat` may only show `aura_ui/`, `tests/browser/`, `docs/ui/`,
  `docs/submission/` and `HANDOVER.md`.
- Claude reviews the diff against brief section 4 and this SOW. The user accepts, merges and
  deploys.

**Accepted when:**
1. A first-time viewer can say what AURA is from the first screen.
2. The patient home on a phone looks like a finished, warm consumer app, with no charts and
   no technical words.
3. The clinician first screen shows what changed and when, with exact values, without
   scrolling at 1280 px.
4. The safety panel, the help button and "Not sent" are unchanged in wording and at least as
   visible.
5. All tests and browser suites pass, or you say plainly that you could not run them.
6. The before and after screenshots are in the Log.
7. No third-party brand assets are used.

## 7. Miora: useful, but not through MCP
- **Useful for:** the moodboard (D0), the brand mark and illustration set (D2), the cover
  image and video frames (D8). Miora is Tencent's AI creative studio. It produces images,
  UI mockups, short video and 3D in one consistent style and remembers brand colours.
  Miora is also listed in the hackathon brief as a development tool, so genuine Miora
  session screenshots strengthen the submission evidence.
- **Not useful for:** writing the HTML/CSS. Miora's UI mockups are pictures, not code. Use
  them as references for CodeBuddy.
- **MCP:** as of 2026-10-12 we found no public Miora MCP server or API, so CodeBuddy cannot
  call it directly. The workflow is manual:
  1. Generate in Miora.
  2. Export the image.
  3. Save it to `aura_ui/media/`, optimised: SVG where possible, otherwise WebP under 150 KB.
  4. CodeBuddy wires it in.

  CodeBuddy does support MCP and Figma import. If a design ends up in Figma, CodeBuddy's
  Figma route can be used. Re-check Miora's own docs before relying on any integration.
- **Prompt hint for Miora:** "Original flat illustration set for a calm mental-wellbeing
  companion app called AURA: warm off-white background, soft orange, sunny yellow, soft
  blue and lilac accents, rounded organic shapes, simple friendly scene, no text, no logos,
  no characters from existing brands, no sad or worried faces." Then ask for each scene in
  D2 with the same style memory.

## 8. Kickoff prompt (paste into CodeBuddy)
> You are redesigning the UI of a hackathon demo called aura-health so it looks warm,
> friendly and sellable, in the spirit of the Headspace app but with its own original brand.
> Read `docs/CODEBUDDY_UI_SOW.md` first and follow it, and also follow sections 4 and 10 of
> `docs/WORKBUDDY_HANDOFF.md`. Do not read the Python code. Create the branch
> `codebuddy/ui` from the tag `pre-workbuddy`. Work through D0 to D7 in order, with small
> commits. Change only `aura_ui/`, `tests/browser/`, `docs/ui/`, `docs/submission/` and
> `HANDOVER.md`. The safety panel wording and position, the patient help button and "Not
> sent" must stay at least as visible as now. Use no gamification, no Headspace assets,
> no external fonts or CDNs, and no new JS/CSS files (new art and fonts go in
> `aura_ui/media/`). Run the tests in brief section 5 and say honestly if you cannot. Add
> before/after screenshots at 1280 and 390 px to your Log entry in `HANDOVER.md`. Do not
> merge or deploy.
