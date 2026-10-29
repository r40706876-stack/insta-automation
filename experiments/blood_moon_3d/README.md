# Blood Moon 3D demo — MinuteMe GS

Topic: **चंद्र ग्रहण में चाँद लाल क्यों होता है?** (32.5 sec, 780 frames, 720×1280, 24 fps)

## Folder me kya hai
| File | Kaam |
|---|---|
| `timeline.json` | 6 scene, har scene ka time, Hindi title/sub, quiz |
| `make_textures.py` | repo ke Natural Earth data se Earth ka texture (koi download nahi) |
| `scene.py` | poora Blender scene: Sun, Earth (clouds + atmosphere glow), Moon (craters), Earth ki chhaya, light rays, camera moves, DOF, motion blur. Render engine **Cycles** |
| `render_missing.sh` | sirf bache hue frames render karta hai (beech me ruke to wahi se chalega) |
| `compose.py` | Hindi text, labels (3D object ke saath chipke), step-bar, quiz card + apna banaya sound → MP4 |
| `blood_moon_3d.yml` | GitHub Actions workflow (parallel render) |
| `land50m.geojson`, `Mukta.ttf`, `OFL.txt` | repo me pehle se maujood data/font |

## GitHub pe kaise chalayein (cross-check)
1. Ye folder repo me `experiments/blood_moon_3d/` naam se rakho.
2. `blood_moon_3d.yml` ko `.github/workflows/` me rakho.
3. Actions → "Blood Moon 3D demo" → Run workflow (chunks = 10, samples = 12).
4. Khatam hone par run ke neeche artifact **blood-moon-reel** me MP4 + contact sheet milega.

Instagram pe kuch post nahi hota, repo me kuch commit nahi hota.

## Same result kyun aayega
- Wahi Blender build (UPBGE 0.44 = Blender 4.4.3), sha256 se verify.
- Wahi samples, wahi seed, wahi texture code (fixed random seed).
- Pixel-level par CPU ke hisaab se bahut halka sa farak ho sakta hai (aankh se nahi dikhega), isliye video ka sha256 alag aa sakta hai.

## Speed / GitHub ki capacity
- Ek frame: ~25-30 sec (2 CPU) → GitHub runner (4 CPU) par ~12-15 sec.
- 1 runner par poori reel: ~3 ghante. **10 runners parallel: ~20-25 min.** Public repo me 20 tak runner ek saath chal sakte hain (free).
- Job ki limit 6 ghante hai — matrix ki wajah se isse kahin lambi/bhaari reels bhi ban sakti hain.
