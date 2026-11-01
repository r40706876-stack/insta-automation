# GS learning and publication changes — 1 November 2026

## Connected behavior

- Existing subject slots rotate Exam Trap, Visual Mystery and Map/PYQ Challenge with a deterministic three-day cycle. The first seven days are an experiment; this does not create extra posts or change the Current Affairs hold.
- Six scene roles require a question, thinking interval, reveal, mechanism, transfer and revision. The planner still uses the grounded bank and existing independent factual/visual audit.
- After rendering, Gemini receives the actual MP4 including audio. It must report six scene observations and explicitly pass answer correctness, relevance, Hindi readability, pronunciation, synchronization, reveal timing and revision readability. A quota/network failure leaves publication blocked. This is an automated review, not a human audit or accuracy guarantee.
- Publication also requires a video-hash-bound review, matching narration, decoded output, per-scene measured motion, acceptable audio and at least two seconds per scene. Existing 720×1280 exports remain valid; 1080×1920 is accepted by the release gate but is not yet an implemented export comparison.
- A failed subject reel no longer publishes a list fallback that bypasses its gate.
- Seven-PYQ keeps its original slot and seven questions. Questions appear progressively, each answer follows a reading/thinking interval; the complete revision card appears last. It is a music-backed revision format, not synthesized narration.
- Explainer captions contain the title, one primary objective and five hashtags. Existing notes/contact and collaborator policy remains in the shared publisher; its banner already reserves teaching space.
- Upload journals retain container identity before media_publish and media ID immediately after success. Ambiguous requests are not blindly repeated. Existing slot/account guards remain. Recovery requires account/container reconciliation; no automated guess at a missing media ID is made.

## Analytics and learning

Hourly Actions collect real Instagram media timestamps and available views, reach, likes, comments, saves, shares and account follower count using existing Instagram secrets. Unavailable API metrics remain null. A collection failure fails the workflow; it is not reported as a successful empty observation. Existing weekly reporting remains enabled. Direct-API insights were unavailable in the first live test, so 58 matched Metricool observations were imported with cache-freshness limitations preserved. A separate seven-day connected-Metricool bridge updates eligible observations every three hours; it writes analytics data only. No missing analytics permission was silently treated as zero. Direct-API insight calls are limited to eligible age windows to reduce request load.

Additional Metricool observations can be imported as `experiments/learning/import.json`, a JSON array. Required fields: media_id, published_at, observed_at (both ISO timestamps with timezone), source, topic and format. Optional fields include subject, duration, views, reach, likes, comments, shares, saves, average_watch_time (seconds), three_second_rate (percent), retention (percent), followers_gained, followers_lost and total_followers. Export units must be verified before importing. Do not convert 3-sec rate to retention.

`python gs_learning.py --import-json experiments/learning/import.json` imports idempotently. `python gs_learning.py` writes `reports/gs_learning.json`.

Snapshots are timestamped observations; 24h±3h, 72h±6h and 7d±12h are separate comparison cohorts. The closest observation per media ID/window is used once. Shares/saves per 1,000 views and missing metrics are explicit. Followers gained/lost are separate from account total. Weekly best/weakest and prior-week differences use 24-hour share/save rates, not views alone. No legacy aggregate in the request has been relabeled as a per-reel baseline or fabricated 24-hour snapshot.

Topic priority no longer rewards water/bank/vote keywords. It uses grounded eligibility and observed 72-hour subject/topic cohorts, requiring at least three usable reels (100 views each) and available share/save metrics, plus 3-sec rate when available. Until those metrics exist, priority stays neutral. It recommends observation/review rather than automatically scaling a format from one result.

## Validation and remaining evidence

Local regression tests cover age windows, missing metrics, invalid observations, deduplication, sample-size safeguards, balanced formats, stale QA and audio mismatch. Existing Studio topic and visual tests were also run. GitHub's existing quality workflow renders its six-set smoke preview after a push. These tests do not prove improved audience retention.

Still required in production: successful live API collection with actual permissions; a real new-topic render and multimodal review; seven-PYQ visual playback QA; seven days of age-matched experimental results. Average watch time, 3-second rate, actual retention and attributed follower gains/losses are unavailable until a verified export supplies them. No skip-rate or follower-growth guarantee is claimed. Share/save/follow objectives rotate with the three formats. A follow invitation names an unused next question from the same grounded subject bank; the next published-subject selection honors that stored question hash. If no next question is available, it uses a save objective. No exact publication date is promised.

## Model availability

The complete preview exposed provider 404/429/503 errors in the old planner configuration. Gemini model availability is now discovered from the provider's models endpoint and limited to a configurable Flash shortlist; retired unavailable model IDs are filtered. `GS_GEMINI_MODELS` and `GS_GROQ_MODELS` allow explicit deployment overrides. Quota/service failures still block an unreviewed publication. Reference: https://ai.google.dev/gemini-api/docs/models and https://ai.google.dev/gemini-api/docs/video-understanding . A static sourced map plus one causal traced route is allowed; decorative extra moving props are no longer required merely to meet a count.

## Integration verification

The integration branch includes a consistent final revision-card exception: only scene six with role revision and explicit revision_card may remain still, for 2–6 measured seconds. Other scenes must show actual teaching motion. Planner validation, renderer validation, exported motion receipts and the publication gate apply the same rule; tests reject earlier-scene bypasses and long static cards.

Provider generation uses a compact six-scene structure and a separate factual-audit schema. The current Gemini REST responseFormat is used for new models, with legacy request fields kept only for legacy models. Internal object IDs are normalized without changing the lesson; ambiguous interaction targets are rejected. Existing Cloudflare text credentials are a bounded fallback after provider failures.

A single sourced map with its geographic route can constitute a complete causal teaching scene. The Narmada preview samples the repository's existing geographic polyline instead of inventing a river route. Production progress and analytics histories are preserved when reconciling the integration branch with main. Full new-format MP4/audio validation remains the release condition; source correctness, readability and actual audiovisual review are never waived to make a run green.
