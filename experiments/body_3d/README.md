# Human Body 3D template — MinuteMe GS

Ek baar setup, phir **har topic sirf ek JSON** (ya Hindi me topic likho, Gemini JSON bana dega) → GitHub pe 3D reel.

## Kaise kaam karta hai
1. `fetch_za.sh` — Z-Anatomy ke asli 3D anatomy models (GitHub, pinned commit) download.
2. `prepare_assets.py` + `organs.json` — models ko 43 organ groups me jodta hai (हृदय, फेफड़े, यकृत, मस्तिष्क, फीमर, स्टेपीज़…), har group ke Hindi naam, rang aur effects wala material. Output `body_assets.blend` (GitHub cache me rehta hai, har baar nahi banta).
3. `planner.py` — Hindi topic → Gemini → topic JSON (sakht validation; galti ho to Gemini ko wapas sudharne bhejta hai, 3 baar tak).
4. `body_scene.py` — JSON padh ke Blender Cycles me render: camera apne aap organ pe focus, dil ki dhadkan, saans, khoon/nerve/bhojan ka chamakta bahav, organ ek-ek karke chamakna, baaki ang dhundhle.
5. `compose.py` — Hindi title, organ ke saath chipke labels, step-bar, quiz card, dhadkan ki awaaz → `reel.mp4`.

## Topic JSON me kya likhte hain (topics/heart_blood.json dekho)
- `camera`: `focus` (organ keys), `angle` (front / three_quarter / side / back…), `move` (push / pull / orbit / rise), `zoom`
- `layers`: skin, visceral, cardio, nervous, skeletal
- `solid`: jo ang saaf dikhne chahiye; baaki dhundhle
- `effects`: `beat`, `breathe`, `flow:arteries`, `flow:veins`, `flow:nerves`, `sequence:oesophagus,stomach,small_intestine,large_intestine`
- `labels`: max 3 organ keys (Hindi naam apne aap)
- aakhri scene me `quiz`

## GitHub pe chalana
- Folder → `experiments/body_3d/`, workflow → `.github/workflows/body_reel.yml`
- Actions → "Human Body 3D reel" → `topic_text` me topic likho (jaise "पाचन तंत्र में भोजन का सफ़र") ya khaali chhodo (heart demo chalega)
- Secret `GEMINI_API_KEY` repo me pehle se hai.
- Result: artifact **body-reel** (reel.mp4 + contact_sheet.jpg + plan.json)

## Time (andaza)
- Pehli baar assets banna: ~5 min (phir cache).
- Ek frame: ~30-60 sec (4 CPU). 30 sec reel = ~750 frames → 20 machines par ~25-40 min.

## License (zaroori)
Models: Z-Anatomy (CC BY-SA 4.0), BodyParts3D (CC BY-SA 2.1 JP). Video me credit line apne aap aati hai — use mat hatana. Is wajah se ye reels bhi CC BY-SA ke andar aati hain (koi bhi credit dekar share/use kar sakta hai).
