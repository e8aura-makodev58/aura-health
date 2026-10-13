# AURA Health deck

The submission deck `docs/submission/assets/aura-health-deck.pptx` (also the required
"Architecture Diagram PPT"). 18 slides, 16:9, built from `../SCRIPT.md` v2.

- `build.py` writes one 1920×1080 HTML page per slide to `slides/` and `slides.json` with the
  speaker notes, taken verbatim from the script's scene narration (stage directions in brackets).
- `render.cjs` renders `slides/*.html` to `png/slide-NN.png` with Playwright.
- `make_pptx.py` puts each PNG full-bleed on a slide (as JPEG, to stay under 10 MB) and adds the notes.

Inputs: live, unedited screenshots in `../screenshots/v2/`, Codex's diagrams in `../diagrams/`,
and the app's own art and Nunito font in `aura_ui/media/`. Slide 15 has a marked slot for the
genuine CodeBuddy and Miora session screenshots, to be added by the user.

## Rebuild

```sh
python3 docs/presentation/deck/build.py
LD_LIBRARY_PATH=/home/makodev58/rendertest/libs/usr/lib/x86_64-linux-gnu \
NODE_PATH=<dir with node_modules/playwright> node docs/presentation/deck/render.cjs
# python-pptx in a separate venv (not the app's .venv):
UV_CACHE_DIR=/tmp/aura-uv-cache uv venv /tmp/deckvenv && \
UV_CACHE_DIR=/tmp/aura-uv-cache uv pip install --python /tmp/deckvenv/bin/python python-pptx
/tmp/deckvenv/bin/python docs/presentation/deck/make_pptx.py
```

Change wording in `build.py` (slide text) or `../SCRIPT.md` (notes), then rerun all three steps
and look at every PNG before committing.
