# Shared animation quality rules

The Studio new-topic planner and scheduled/daily explainers use the same planner,
scene_dynamic renderer, rich_assets library and exported-file verifier. Existing
7-PYQ and mega question layouts keep their separate formats. No publishing times,
account targets, collaborator settings, phone banner or voice fallback are changed.

## Implemented visuals

- `planet`: filled land surfaces tessellated from the bundled Natural Earth physical
  coastlines and projected onto the sphere, plus coastline edges. Not a plate
  reconstruction or an administrative map.
- `mountain`: connected ridges/foothills and altitude-based snow, replacing cones.
- `rock_layers` + `compress`: five continuous connected strata shorten, buckle and
  rise using Blender shape keys. A qualitative cross-section, not a geodynamic
  simulation, exact Himalayan geometry or a substitute for a moving plate map.
- Articulated people, waves, map routes and machine assets retain their existing
  supported operations. Unsupported historical likenesses/mechanisms need assets.

## Readable staging

Optional `animation_window: [0.4, 1]` delays a causal movement until 40% of its
scene; at least 45% of scene duration must remain. Default `[0, 1]` preserves
existing recipes. Applies to object travel, growth, rotation, route tracing,
folding and character poses; ocean background waves remain continuous.
`camera_view` accepts `front`, `top` and `oblique` (default), while maps retain
their frontal projection.

New plans must explain one question with a cause before its effect, advance the
story between scenes, explain necessary terms in simple Hindi, and provide a
useful takeaway before a topic-specific sharing invitation. Generic boxes named
India/Asia/Himalaya/organs are rejected. The AI factual/visual audit also checks
comprehension and causal ordering. This is a fallible review, not proof that a
viewer will understand or share.

## Verification

Unit tests cover valid/invalid timing, unsupported compression/cameras and fake
country boxes. CI renders six actual sets including continuous folds, terrain,
filled globe, sourced map, people and voting. It checks changed pixels inside
the visual region and saves a contact sheet. A motion check only proves pixels
changed; inspect narration and the visual explanation before approving a new
custom lesson. Export checks retain audio/decode/black-frame checks and report
which models were actually used instead of unconditionally claiming maps/people.

Previously rendered videos and approved hashes are not rewritten. Dedicated
reviewed renderers remain separate; these improvements do not turn their old
simplified silhouettes into accurate geography. Unsupported content stops with
an actionable diagnosis rather than publishing a substitute model. No guarantee
of views, shares, universal self-repair or 10/10 output is made.
