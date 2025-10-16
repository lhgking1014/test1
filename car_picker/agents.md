# AGENTS.md

## Project overview
- Streamlit-based 10-question car identification quiz.
- Uses `index.json` (~40 MB) for metadata and `thumbs/` for pre-generated thumbnails backing the UI.
- UI styling lives in `app/streamlit_app.py` and targets Streamlit >= 1.38 (fragments, callback buttons, `st.container(..., border=True)`).

## Environment & setup
- Target Python 3.10+ (developed against 3.11).
- Install dependencies: `pip install -r car_picker/requirements.txt`.
- Local run: `streamlit run car_picker/app/streamlit_app.py`.

## Data & assets
- Source images reside under `data/`; thumbnails under `thumbs/`.
- `index.json` is generated, not hand-edited. Regenerate via `python car_picker/scripts/build_index.py` (requires Pillow).
- Thumbnails: `python car_picker/scripts/make_thumbs.py`.
- When adding images, run `make_thumbs.py` first, then `build_index.py`.
- Keep large binaries out of diffs unless explicitly required; prefer scripts for regeneration.

## Package layout
- `app/` - Streamlit app code (state management, question generation, store/parser).
- `scripts/` - maintenance utilities for metadata and thumbnails.
- `data/` & `thumbs/` - assets (do not commit new large files without coordination).
- `DESIGN.md` - UX doc with original quiz flow rationale.

## Coding guidelines
- Follow PEP 8 with 88-char soft limit.
- Prefer `pathlib.Path`, typed dataclasses, and pure functions (matches existing style).
- Keep Streamlit callbacks side-effect free; manipulate shared state via helper functions (`get_state`, `record_choice`, etc.).
- Maintain translated UI text (currently Korean copy in some legacy strings); update consistently if editing.

## Streamlit patterns
- Use `st.fragment` for interactive sections to avoid global reruns.
- Reuse existing CSS injection instead of adding inline HTML; extend `inject_styles()` when styling is required.
- Buttons should use `on_click` callbacks rather than manual `st.rerun()` calls.
- Use `st.toast`, `st.progress`, and bordered containers for feedback to match the refreshed design.

## Testing & QA
- Manual smoke test: `streamlit run ...`, answer quiz ensuring progress indicator, toasts, summary table, and restart button behave.
- Scripts: run `python car_picker/scripts/build_index.py --help` (no CLI yet) before/after changes touching metadata parsing.
- If parser logic changes, test against a sample of filenames in `data/` to ensure `CarMeta.display_label` and filtering still work.

## Deployment notes
- Streamlit Cloud is the default target; ensure `requirements.txt` stays minimal.
- When adding dependencies, confirm they are compatible with Streamlit sharing (pure Python preferred).
- Store secrets via Streamlit sharing UI (none currently required).

## Communication
- Document significant workflow changes in `DESIGN.md` plus commit messages.
- Mention if scripts must be re-run or assets regenerated in PR descriptions.
