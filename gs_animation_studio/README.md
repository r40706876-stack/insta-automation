# GS Animation Studio: manual runs and recovery

Actions → GS Animation Studio → Run workflow → select a supported topic and voice.
Choose `new_topic` (default). Enter any GS topic in `topic_text`, e.g. `दांडी मार्च में नमक क्यों चुना गया?` or `चुनाव में बहुमत कैसे बनता है?`. Leave the text blank to select a fresh topic automatically; choose a subject if wanted. `reference_text` is optional source text; otherwise the planner fetches readable sources. Previous generated topics are supplied to selection to discourage repetitions. Explicitly requesting an older topic is allowed.

Default mode prefers Gemini Charon male; when unavailable it uses the approved female fallback. This workflow builds a review video; it does not publish to Instagram.

## Automatic recovery

- Network package requests and verified official Blender downloads have bounded retries.
- Voice generation retries; if providers fail, the exact matching reviewed narration can be restored. A changed script never gets an unrelated older recording.
- Renderer syntax/crashes retry with a hash-verified reviewed renderer for the exact same recipe and a software rendering profile. Composition retries use reviewed code.
- Missing/silent audio is remuxed from the matching narration. Full video decoding, black-screen checks, duration, dimensions, audio and actual motion checks run again without relaxed thresholds.
- A failed video check can regenerate the lesson once with the reviewed renderer. Unresolved failures stop, quarantine the export and retain diagnostics. No infinite retry and no arbitrary AI-written repair.
- Reports and verified exports are persisted with bounded Git push retries. Concurrent repository updates do not rerender or republish.

`verify_recovery` optionally introduces syntax damage to a staged scene and silent audio to the new export, then requires both repair paths and all original checks to pass. The repository source and reviewed snapshots are never damaged.

New topics use a bounded JSON scene planner, source-based AI audit, and a procedural 3D actor engine. Six different compositions animate people/vehicles/mechanisms, with animated Hindi labels and narration. The AI never executes generated Python. Available 3D assets/actions are a reusable toolkit, not a fixed topic list. All six scenes must show actual pixel motion, in addition to the original decode/audio/black-screen checks.

New topics require a working Gemini or Groq text API and a working voice service. Service/source/audit failures stop visibly rather than substituting an unrelated old lesson. Voice cache recovery is allowed only for matching existing reviewed scripts. AI fact/visual audits are not human certification: inspect the preview before publication. Complex custom simulations outside this actor toolkit may need a dedicated renderer. Number of topics is open-ended; API quotas and rendering time still apply.

Diagnostics: Actions artifact `GS-Studio-diagnostics-<run>-<attempt>` and `studio_diagnostics/`. Passing reels remain under `experiments/gs_animation_studio/<topic>/<run>/`.

Source lookup first tries fetched links, then live Gemini/Bing search, then a transparently labelled encyclopedia fallback. A pasted reference can be supplied when sites block requests. The source record and AI audits accompany a successful build. Automatic topic selection checks both previous keys and an AI novelty audit; explicit repeated requests are allowed. The engine supplies safe object layouts and keeps the full narration when shortening screen labels.

## Shared rich 3D engine (rich_3d_v1)

All new-topic Studio builds and the daily/regular **subject explainers** now use the same Blender builder (`gs_animation_bridge.py`). The regular 07:00 seven-PYQ and 17:00 mega question formats retain the user's existing layout and times. No additional posts or schedule slots are added. Current-affairs publication hold, MinuteMe_GS account check, collaborator invitation and duplicate/late-slot guards stay active.

- Articulated people with hips, knees, elbows, head and identifiable supported clothing; Gandhi has the reviewed bald head, round spectacles, dhoti, shawl and staff. Walking, pointing and the supported salt pickup are animated. This does not implement every historical likeness or every grasp action.
- Topic-appropriate settings: coastline with a deforming ocean and traveling foam, institution, village, laboratory, space or neutral teaching set. Unrelated lessons are not forced into a Gandhi/sea/globe scene.
- Bundled sourced Gujarat outline and Natural Earth physical coastlines for world/India maps and globes. Geographic route points are bounded and audited; the on-screen disclaimer identifies schematic routes. Physical coastlines do not provide arbitrary state/district borders.
- A visible causal action is mandatory in each scene. Decorative pulsing, zooming or moving captions alone is rejected. Unsupported custom models fail clearly rather than silently substituting irrelevant objects.
- The existing safe-area Notes/WhatsApp banner and colored Hindi captions are shared. Hash-verified Studio exports skip the publisher's second banner, preventing duplicated text and unnecessary shrinking.
- Old 2D exports cannot pass the new version gate. The original 3D reviewed demos stay separate; manual `new_topic` uses the new engine automatically.
- `GS rich animation quality checks` runs the unit/integration suite plus actual Blender rendering of six sets and pixel-motion checks. The check workflow has no Instagram or voice API credentials and never publishes. Its artifact contains a contact sheet and motion report.

These are reusable supported assets and stronger checks, not a promise that every possible topic has a perfect custom simulation. Text/voice API access and factual/visual audits can still fail; render failures retain diagnostics. A human preview and native Instagram metrics remain necessary for judging clarity and engagement.
