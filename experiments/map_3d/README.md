# Map / Timeline 3D PYQ reels (template, no AI visuals)

AI kuch tay nahi karta ki screen par kya dikhe. Har cheez PYQ + `facts.json` + asli map data se aati hai.

| Template | Kis sawaal ke liye | Kya dikhta hai |
|---|---|---|
| `river_place` | "X bandh/pariyojana kis nadi par?" | 3D India, pin girta hai, 4 option nadiyan alag rang me behti hain, sahi nadi chamakti hai, udgam se muhane tak safar + jin rajyon se behti hai wo jalte hain |
| `state_place` | "X kis rajya me hai?" | pin, option rajya apne rang me uthte hain, sahi rajya sona ban kar upar uthta hai, rajdhani ka pin |
| `timeline` | saal wale sawaal | 3D tower par 4 saal, sahi saal aage aata hai, phir aas-paas ki do badi ghatnaon ke beech fit hota hai (yaad rakhne ki trick) |

Data: `india_states.json` (datameet/maps 2020, MIT — J&K, Ladakh, Telangana sahi), `rivers.json` (Natural Earth, public domain),
`facts.json` (udgam/muhana, jagahon ke coordinates, rajdhaniyan, mashhoor saal). `make_plan.py` har jagah ko map par check karta hai
(pin sahi rajya me? nadi pin se guzarti hai?) — mismatch par plan banta hi nahi.

Workflow: Actions → "Map/Timeline 3D PYQ reel" (sirf banata hai, post nahi karta). Output `downloads/map3d/`.

## Roz ka chakr (calendar)
- `month_plan.py build` → `calendar.json`: har din 20:00 = नक्शा reel (nadi/rajya), 22:00 = टाइमलाइन reel.
  Sirf wahi PYQ jo map/facts check pass karein; purane-samay wale (sarkar, yojana, 2010+ saal) aur toote text wale hataye.
- Timer 13:00 IST par `map3d_daily.yml` chalata hai → aaj ke reels render → `experiments/slot_override.json` me slot set.
- 20:00 / 22:00 ka normal run pehle ye 3D reel post karta hai; render fail ho to normal reel (7 PYQ) jaata hai.
- `lakes.json` (Natural Earth): bade jalashay asli shape me; samudra/padosi desh ke naam map par.
