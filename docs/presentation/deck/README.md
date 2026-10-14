# AURA Health deck

The submission deck `docs/submission/assets/aura-health-deck.pptx` (also the required
"Architecture Diagram PPT"). 18 slides, 16:9, built from `../SCRIPT.md` (v4, story order: medication, appointment, clinician + agent, flu, safety).

- `build.py` writes one 1920×1080 HTML page per slide to `slides/` and `slides.json` with the
  speaker notes, taken verbatim from the script's scene narration (stage directions in brackets).
- `render.cjs` renders `slides/*.html` to `png/slide-NN.png` with Playwright.
- `hybrid.cjs` records every text block of each rendered slide (position, font size, weight, colour,
  letter spacing, line height, alignment, bold runs) into `hybrid/text.json` and renders the same page with
  the text hidden into `hybrid/bg-NN.png`.
- `make_hybrid_pptx.py` builds the deck (canonical): background picture per slide (art, cards,
  screenshots, diagrams) plus **every piece of text as an editable PowerPoint text box** in the app's font,
  Nunito, and the speaker notes. Install Nunito (free, fonts.google.com/specimen/Nunito) on the computer
  that opens the deck; PowerPoint substitutes a similar font otherwise.
- `preview_pptx.py` redraws the saved PPTX as HTML for a visual check (approximation, not PowerPoint).
- `make_pptx.py` is the older all-image variant (each slide one picture); kept for the video frames.
- Slides 11–13 are native editable diagrams from `native_diagrams.py`, with attached
  connector arrows. The SVGs in `../diagrams/` are historical, not current sources.

Inputs: live, unedited screenshots in `../screenshots/v2/`, Codex's diagrams in `../diagrams/`,
and the app's own art and Nunito font in `aura_ui/media/`. Slide 16 has a marked slot for the
genuine CodeBuddy and Miora session screenshots, to be added by the user.

## Rebuild

```sh
python3 docs/presentation/deck/build.py
LD_LIBRARY_PATH=/home/makodev58/rendertest/libs/usr/lib/x86_64-linux-gnu \
NODE_PATH=<dir with node_modules/playwright> node docs/presentation/deck/render.cjs
# python-pptx in a separate venv (not the app's .venv):
UV_CACHE_DIR=/tmp/aura-uv-cache uv venv /tmp/deckvenv && \
UV_CACHE_DIR=/tmp/aura-uv-cache uv pip install --python /tmp/deckvenv/bin/python python-pptx
node docs/presentation/deck/hybrid.cjs
/tmp/deckvenv/bin/python docs/presentation/deck/make_hybrid_pptx.py
```

Change wording in `build.py` (slide text) or `../SCRIPT.md` (notes), then rerun all three steps
and look at every PNG before committing.

For architecture-only changes, edit `native_diagrams.py`, then use a tooling venv
containing `python-pptx`, `reportlab`, `fonttools`, `brotli` and `pymupdf`:

```sh
python docs/presentation/deck/reconcile_architecture.py
# First export: --bookends /absolute/path/to/the/original/architecture.pdf
```

This updates only slides 11–13 in the existing PPTX, their PNGs and the reviewed
five-page architecture PDF. The original first/last PDF pages are preserved.
The PDF/PNGs are ReportLab drawings of the shared native shapes, with embedded
Nunito; this is not a PowerPoint/LibreOffice render. Text bounds are checked.
Review in PowerPoint before final upload; rebuild videos separately if they embed
these frames. See `../../submission/ARCHITECTURE_REVIEW.md` for the source audit.
