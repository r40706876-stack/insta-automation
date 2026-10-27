# GS Animation Studio: manual runs and recovery

Actions → GS Animation Studio → Run workflow → select a supported topic and voice.
Default mode prefers Gemini Charon male; when unavailable it uses the approved female fallback. This workflow builds a review video; it does not publish to Instagram.

## Automatic recovery

- Network package requests and verified official Blender downloads have bounded retries.
- Voice generation retries; if providers fail, the exact matching reviewed narration can be restored. A changed script never gets an unrelated older recording.
- Renderer syntax/crashes retry with a hash-verified reviewed renderer for the exact same recipe and a software rendering profile. Composition retries use reviewed code.
- Missing/silent audio is remuxed from the matching narration. Full video decoding, black-screen checks, duration, dimensions, audio and actual motion checks run again without relaxed thresholds.
- A failed video check can regenerate the lesson once with the reviewed renderer. Unresolved failures stop, quarantine the export and retain diagnostics. No infinite retry and no arbitrary AI-written repair.
- Reports and verified exports are persisted with bounded Git push retries. Concurrent repository updates do not rerender or republish.

`verify_recovery` optionally introduces syntax damage to a staged scene and silent audio to the new export, then requires both repair paths and all original checks to pass. The repository source and reviewed snapshots are never damaged.

Recovery currently supports the two reviewed recipes (dam_pressure and canal_lock). New topics need their own reviewed scene, narration and checks. It cannot certify factual/storytelling quality or repair every unknown bug.

Diagnostics: Actions artifact `GS-Studio-diagnostics-<run>-<attempt>` and `studio_diagnostics/`. Passing reels remain under `experiments/gs_animation_studio/<topic>/<run>/`.
