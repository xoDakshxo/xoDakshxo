# Banner generator

Generates the animated profile banner (`assets/banner-v7.gif`).

```bash
pip install Pillow
python scripts/generate_banner.py
```

- `name_ansi.txt` — the ANSI Shadow ASCII art for the name (edit to change the name).
- `generate_banner.py` — rasterizes the name with a real monospace font (Menlo on
  macOS; set `FONT_PATH` to override) so the block glyphs stay aligned, then renders
  a terminal typewriter cycling the titles in `ROLES`.

To change the cycling titles, edit `ROLES` in `generate_banner.py`.

**Cache note:** GitHub's image proxy caches by URL. After regenerating, bump
`OUTPUT_NAME` (e.g. `banner-v7.gif` → `banner-v8.gif`) and update the `<img>` in the
root `README.md`, otherwise the old cached image keeps showing.
