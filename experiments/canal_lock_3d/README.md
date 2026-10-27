# Panama Canal: genuinely animated 3D lock

42-second Hindi teaching reel. Every visual element is procedural Blender geometry; no stock stills, photo pans, image billboards or generative-image assets.

Motion: ship enters the chamber, two hinged gate leaves close, supply valve rotates, flow tracers move along a cutaway culvert, chamber water rises, floating ship follows, upper gates open only after water levels equalize, ship exits. The fixed camera during filling lets the viewer see the actual rise.

This is one schematic teaching chamber, not a scale replica of the whole canal. Model height units are not metres. Panama uses multiple lock chambers; never describe a single chamber as a 26-metre lift. Water flows from the higher reservoir by gravity.

The editable Blender scene is included as `canal_lock.blend.xz` (run `xz -dk canal_lock.blend.xz` to open it).

## Rebuild
Blender 4.2.0, FFmpeg, Python 3 with Pillow and numpy.
```
export CANAL_ROOT="$PWD/experiments/canal_lock_3d"
ffmpeg -y -i "$CANAL_ROOT/voice.flac" "$CANAL_ROOT/voice.wav"
blender -b -t 6 --python "$CANAL_ROOT/canal_lock_blender.py"
python "$CANAL_ROOT/compose.py"
```
`CANAL_STILL=1` makes a single proof instead. The GitHub workflow supports manual runs and runs when its own workflow file changes. It deletes the checked-in MP4 before rendering, builds the complete scene on the GitHub runner, verifies the decoded output, and saves an artifact plus a separate `github_build/` output folder with run/commit provenance. It does not publish a reel or alter posting schedules.

Audio is the existing approved female fallback, Edge hi-IN-SwaraNeural. It is not represented as Gemini or a male voice. Narration is retained in FLAC for a reproducible build without fresh TTS API calls. No music or filler humming.

WhatsApp notes banner is above the main scene and away from Instagram's username, caption and right-side actions. No AR Publications name in the visual.

Sources:
- https://pancanal.com/en/history-of-the-panama-canal/
- https://pancanal.com/en/design-of-the-locks/
- https://canalrivertrust.org.uk/canals-and-rivers/how-does-a-canal-lock-work

## Published original and GitHub builds
The explicitly approved original was published at https://www.instagram.com/reel/DfAQn7yifHt/ . Its receipt and reviewed SHA remain in `published.json`. The independent GitHub rebuild uses `canal_lock_3d_demo.yml`; its outputs are stored under `github_build/`, so they never replace the approved original or trigger a second publication.

This renderer models this specific canal-lock lesson. A new topic requires its own explanatory geometry, motions and narration; the workflow is the reusable rendering path, not an automatic generator of arbitrary topics.

## Verification
Per-frame mechanical invariants in `canal_lock_blender.py`: chamber cannot fill with either end open; upper gate opens only at equal levels; ship cannot depart through a closed upper gate. `scene_checks.json` records those checks. Contact sheet and finished-file checks are stored with the reel. Those checks establish mechanical consistency and file health, not guaranteed engagement.
