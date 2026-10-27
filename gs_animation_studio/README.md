# GS Animation Studio

Separate manual workflow: **Actions → GS Animation Studio → Run workflow → topic → Run workflow**.

- `dam_pressure`: why a concrete gravity dam has a broad base. New voice, actual 3D caps opening, two ballistic water streams, equal-area pressure/force arrows, and a base that becomes wider while the crest stays narrow.
- `canal_lock`: the validated Panama lock scene, rebuilt with its retained reviewed narration.
- Voice `auto`: prefer Gemini Charon male; if unavailable use one consistent Swara female fallback throughout. `female_fallback` selects the fallback directly. Voice provider is recorded in `audio.json`.

Outputs: `final.mp4`, `contact_sheet.jpg`, `voice.flac`, `scene.blend.xz`, `file_checks.json`, `scene_checks.json`, `build_receipt.json`, saved in the run artifact and `experiments/gs_animation_studio/<topic>/<run_id>/`.

**This workflow builds a video for review. It does not publish to Instagram, send messages, or change the regular posting schedule.** It has no Instagram secrets. Every manual run creates a separate folder; it does not overwrite a published original.

Known topics are explicit animation recipes, not automatic images. To add a new topic, add a reviewed script, its own procedural Blender scene and matching narration/labels, then expose it in the topic choices. Choosing a topic does not change its scientific story randomly.

The Notes/WhatsApp banner is preserved in the upper safe region; AR Publications branding is not placed in the video.

## Physics of the dam lesson

Gauge pressure grows with depth in a static fluid. Equal-area arrows illustrate the force exerted by that pressure. Outlet speeds use the ideal small-orifice Torricelli relation; each moving parcel follows a ballistic curve after exiting. The large-reservoir/small-outlet approximation makes free-surface motion very small during the short demonstration. The lowest outlet does **not always** give the greatest horizontal range; the script teaches exit speed, not that incorrect generalization. Water markers are deliberately spaced at 12 per jet: at 24 fps this avoids the apparent reverse flow caused by a dense, regular moving pattern. The opening shot also widens the actual 3D base within its first second.

The dam is a cutaway schematic of a concrete gravity dam. This is not a universal shape for all dams or an engineering construction design. Front walls are removed to show the mechanism. Base growth is an explanatory transformation, not a claim about construction in water.

Sources:
- https://openstax.org/books/university-physics-volume-1/pages/14-2-measuring-pressure
- https://openstax.org/books/college-physics-2e/pages/12-3-the-most-general-applications-of-bernoullis-equation

Font: existing Mukta from `experiments/canal_lock_3d/`, its OFL license is retained there. No photographs, stock imagery or image billboards are used.
