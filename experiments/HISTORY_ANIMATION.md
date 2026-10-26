# History animation: build and review

The public GitHub implementation is `cinematic_history_dandi_v2.py`. Reusable effects are in `gs_motion_fx.py`: perspective-projected Hindi cards with anti-aliased text and depth shadows, plus a coastline rim derived from the geographic mask. The renderer exports 720x1280 H.264/AAC at 30 FPS; it does not claim native 1080p or guaranteed engagement.

Run the **History cinematic preview - build only** Actions workflow, or install requirements.txt plus imageio-ffmpeg and run `python cinematic_history_dandi_v2.py` with the same existing environment configuration. Cloudflare is used only if the historical illustration is missing; Gemini Charon is preferred, with the previously authorized Swara fallback. No Instagram credentials are supplied by this workflow, and it has no publication step.

Output: `experiments/history_dandi_cinematic_v2/preview_notes_safe_v2.mp4`, `review_sheet.jpg`, and `review.json`. The notes/WhatsApp panel is integrated into the reviewed export. The historical illustration is marked as AI reconstruction. Natural Earth 10m supplies the geographic coastline; the march trace is explicitly schematic.

Editorial hypothesis: viewers preparing history can send the two-event revision card to a study partner and test whether the partner matches 12 March to departure and 6 April to breaking the salt law. This is a reason to experiment, not evidence of increased sharing. There is no fabricated '99% wrong' claim. Compare actual share rate, saves, skip rate and watch time at matched post ages after authorized publication.

Before publication inspect all scenes and the complete branded export. Do not treat build success as a quality rating or remove older publication holds. This module has not automatically replaced all scheduled subject renderers.
