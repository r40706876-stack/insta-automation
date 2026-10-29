"""Build the Earth colour texture from the bundled Natural Earth 1:50m land polygons.
Deterministic (fixed seed) so a GitHub run produces the identical image."""
import json, os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

R = Path(os.environ.get('DEMO_ROOT', Path(__file__).parent))
W, H = 2048, 1024
rng = np.random.default_rng(7)

mask = Image.new('L', (W, H), 0)
d = ImageDraw.Draw(mask)
def px(lon, lat): return ((lon + 180) / 360 * W, (90 - lat) / 180 * H)
for f in json.loads((R / 'land50m.geojson').read_text())['features']:
    g = f['geometry']
    polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    for poly in polys:
        d.polygon([px(*p[:2]) for p in poly[0]], fill=255)
        for hole in poly[1:]:
            d.polygon([px(*p[:2]) for p in hole], fill=0)
m = np.asarray(mask.filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255

def fbm(octaves=5, base=8):
    out = np.zeros((H, W), np.float32); amp = 1.0
    for o in range(octaves):
        n = base * 2 ** o
        small = rng.random((n // 2 + 1, n + 1)).astype(np.float32)
        out += amp * np.asarray(Image.fromarray(small).resize((W, H), Image.BICUBIC))
        amp *= .5
    out -= out.min(); return out / out.max()

lat = np.abs(np.linspace(90, -90, H))[:, None].repeat(W, 1)
n1, n2 = fbm(), fbm(base=16)
# land: green lowlands -> ochre deserts -> white poles
green = np.array([.13, .36, .16]); ochre = np.array([.62, .5, .3]); snow = np.array([.93, .95, .97])
dry = np.clip((n1 - .45) * 2.2 + (np.exp(-((lat - 25) / 9) ** 2) * .6), 0, 1)[..., None]
land = green * (1 - dry) + ochre * dry
land *= (.82 + .3 * n2[..., None])
polar = np.clip((lat - 66) / 8, 0, 1)[..., None]
land = land * (1 - polar) + snow * polar
# ocean: deep blue with shallow shelf near coast
coast = np.asarray(mask.filter(ImageFilter.GaussianBlur(9)), np.float32)[..., None] / 255
ocean = np.array([.02, .09, .25]) * (1 - coast) + np.array([.05, .3, .45]) * coast
ocean *= (.9 + .15 * n2[..., None])
ice = np.clip((lat - 76) / 8, 0, 1)[..., None] * .7
ocean = ocean * (1 - ice) + snow * ice
img = ocean * (1 - m[..., None]) + land * m[..., None]
Image.fromarray((np.clip(img, 0, 1) ** (1 / 1.0) * 255).astype(np.uint8)).save(R / 'earth_color.png')
# specular/roughness: oceans shiny, land matte
Image.fromarray(((1 - m) * 255).astype(np.uint8)).save(R / 'earth_water.png')
print('textures written', R)
