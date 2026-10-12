# UI media

Flat folder for static UI art and fonts, served at `/assets/media/<name>`.

- Allowed types: `.svg`, `.png`, `.webp`, `.jpg`, `.woff2`. Anything else returns 404.
- Names: lowercase letters, digits, `-` and `_`, one extension (for example `home-hero.svg`,
  `nunito-600.woff2`). No subfolders.
- Fonts must be self-hosted under an open licence (for example SIL OFL); add the licence
  text as `<font>-LICENSE.txt` next to it (text files are kept in git but not served).
- The page's security policy blocks external fonts, images and scripts, and inline
  `<style>`/`style=""`; reference media from `styles.css` or `<img src="/assets/media/...">`.
- `calm-sun.svg` is a placeholder example; replace or delete it freely.
- Illustrations (`welcome-hero`, `home-hero`, `breathing-circle`, `empty-clinician`,
  `appointment-note`) are Miora-generated artwork, converted to WebP under 60 KB each.
- Original or properly licensed art only. No third-party brand assets (logos, characters,
  mascots) from any other app.
