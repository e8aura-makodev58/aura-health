# UI media

Flat folder for static UI art and fonts, served at `/assets/media/<name>`.

- Allowed types: `.svg`, `.png`, `.webp`, `.jpg`, `.woff2`. Anything else returns 404.
- Names: lowercase letters, digits, `-` and `_`, one extension (for example `home-hero.svg`,
  `nunito-600.woff2`). No subfolders.
- Fonts must be self-hosted under an open licence (for example SIL OFL); add the licence
  text as `<font>-LICENSE.txt` next to it (text files are kept in git but not served).
- The page's security policy blocks external fonts, images and scripts, and inline
  `<style>`/`style=""`; reference media from `styles.css` or `<img src="/assets/media/...">`.
- `aura-zh.woff2` and `aura-ta.woff2` are tiny subsets (about 1 KB each) of Noto Sans SC and
  Noto Sans Tamil, regular weight, containing only the characters of the language names
  "中文" and "தமிழ்" shown in the Language card, so they render even where no Chinese or Tamil
  system font is installed. Rebuild with fontTools (`varLib.instancer` wght=400, then
  `pyftsubset --text=… --layout-features='*' --flavor=woff2`) if those labels change.
- Illustrations (`welcome-hero`, `home-hero`, `breathing-circle`, `empty-clinician`,
  `calm-state`, `aura-mark`) are Miora-generated true vector SVGs (4–10 KB each).
  `aura_health_app_icon.svg` is also available for PWA/favicons.
- Original or properly licensed art only. No third-party brand assets (logos, characters,
  mascots) from any other app.
