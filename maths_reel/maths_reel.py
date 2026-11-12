"""MinuteMe_GS - Maths PYQ animated solution reel (1080x1920, 30fps).

Usage:
  python maths_reel/maths_reel.py maths_reel/demo_bells.json out.mp4          # full video
  python maths_reel/maths_reel.py maths_reel/demo_bells.json out.mp4 --stills  # sirf kuch frames (check ke liye)

Animation reel.html mein hai (HTML/CSS/JS, time-based seek). Har frame Playwright se screenshot hota hai
aur seedha ffmpeg mein pipe hota hai. Sound effects (ghanti, pop, success) ffmpeg se banaye jaate hain -
koi bahar ki file nahi chahiye. Optional voice: VOICE_FILE env (mp3/wav) ho to background mein mix hoti hai.
"""
import json, os, subprocess, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FPS = 30
END_HOLD = 2.2  # aakhri line ke baad CTA ke liye


def make_voice(spec, wav_path):
    """Poori script ki awaaz Gemini se EK baar me (auto_poster wala helper) -> (seconds, [har line ki shuruaat]).
    Gemini na chale to edge-tts (har line alag). Kuch na chale -> None (bina awaaz)."""
    lines = spec.get("voice") or []
    if not lines:
        return None
    sys.path.insert(0, ROOT)
    try:
        import numpy as np, wave
        import auto_poster as ap
    except Exception as exc:
        print("voice helper import nahi hua:", exc)
        return None
    arr, starts = None, None
    one = ap.gemini_voice_timed([ap.to_speech(x) for x in lines], int(spec.get("voice_rot", 0)))
    if one:
        arr, starts = one
    else:
        try:
            vs = [v[0] for v in ap.make_voices([{"segs": [(None, None, ap.to_speech(t))]} for t in lines], 0)]
            gap = int(ap.SR * 0.25)
            starts, chunks, pos = [], [], 0
            for v in vs:
                starts.append(pos / ap.SR); chunks += [v, np.zeros(gap, dtype=np.float32)]; pos += len(v) + gap
            arr = np.concatenate(chunks)
            print("Awaaz: edge-tts (Gemini nahi chala)")
        except Exception as exc:
            print("awaaz nahi bani:", str(exc)[:150])
            return None
    pcm = (np.clip(arr, -1, 1) * 32767).astype("<i2").tobytes()
    with wave.open(wav_path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(ap.SR); w.writeframes(pcm)
    return len(arr) / ap.SR, list(starts)


def time_map(ts, tmpl_total, real_starts, real_total):
    """Template scenes (ts) ko awaaz ki lines (real_starts) par bithana. Lambi line -> animation chal kar ruk jaata
    hai (hold), chhoti line -> animation thoda tez. Return f(rt) -> template time."""
    T = list(ts) + [tmpl_total]
    B = list(real_starts) + [real_total]
    FADE = 0.45

    def f(rt):
        i = max(k for k in range(len(B) - 1) if B[k] <= rt or k == 0)
        D, R, u = T[i + 1] - T[i], B[i + 1] - B[i], max(0.0, rt - B[i])
        if R >= D:
            if u < D - FADE:
                return T[i] + u
            if u > R - FADE:
                return T[i] + D - (R - u)
            return T[i] + D - FADE
        return T[i] + u * D / R
    return f


def sfx_track(path, total, events):
    """events: list of (time, kind). kind: bell | pop | whoosh | win"""
    parts, labels = [], []
    defs = {
        "bell": "sin(2*PI*1320*t)*exp(-3*t)*0.5+sin(2*PI*2640*t)*exp(-5*t)*0.2+sin(2*PI*880*t)*exp(-2.5*t)*0.25",
        "pop": "sin(2*PI*(600+2400*t)*t)*exp(-28*t)*0.6",
        "whoosh": "(random(0)*2-1)*exp(-pow((t-0.18)*9,2))*0.35",
        "win": "(sin(2*PI*784*t)*lt(t,0.12)+sin(2*PI*988*t)*gte(t,0.12)*lt(t,0.24)+sin(2*PI*1319*t)*gte(t,0.24))*exp(-2.2*max(t-0.24,0))*0.45",
    }
    dur = {"bell": 1.6, "pop": 0.25, "whoosh": 0.4, "win": 1.4}
    for i, (t0, kind) in enumerate(events):
        expr = defs[kind].replace(",", "\\,")  # lavfi option ke andar comma escape
        parts += ["-f", "lavfi", "-i", f"aevalsrc={expr}:s=44100:d={dur[kind]}"]
        labels.append(f"[{i}:a]adelay={int(t0 * 1000)}|{int(t0 * 1000)}[a{i}]")
    n = len(events)
    voice = os.environ.get("VOICE_FILE")
    vin = []
    if voice and os.path.exists(voice):
        vin = ["-i", voice]
        d = int(float(os.environ.get("VOICE_DELAY", "0")) * 1000)
        labels.append(f"[{n}:a]adelay={d}|{d},volume=1.15[v]")
    if vin:  # awaaz ke saath effects thode dheeme
        labels = [l.replace(f"[a{i}]", f",volume=0.55[a{i}]") if l.startswith(f"[{i}:a]") else l for i, l in enumerate(labels)]
    mix_in = "".join(f"[a{i}]" for i in range(n)) + ("[v]" if vin else "")
    fc = ";".join(labels) + f";{mix_in}amix=inputs={n + (1 if vin else 0)}:normalize=0,alimiter=limit=0.9,apad,atrim=0:{total}[out]"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *parts, *vin, "-filter_complex", fc, "-map", "[out]",
                    "-c:a", "aac", "-b:a", "160k", path], check=True)


def main():
    spec_path, out = sys.argv[1], sys.argv[2]
    stills = "--stills" in sys.argv
    spec = json.load(open(spec_path, encoding="utf-8"))
    with sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception:
            b = p.chromium.launch(channel="chrome")
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.add_init_script("window.SPEC = " + json.dumps(spec, ensure_ascii=False) + ";")
        pg.goto("file://" + os.path.join(HERE, "reel.html"))
        pg.evaluate("document.fonts.ready.then(() => 1)")
        pg.wait_for_timeout(400)
        total = pg.evaluate("window.TOTAL")
        ts = pg.evaluate("window.SCENE_STARTS")
        wav = out + ".voice.wav"
        v = None if "--stills" in sys.argv else make_voice(spec, wav)
        if v:
            vdur, vst = v
            lead = 0.3
            real_starts = [0.0] + [lead + x for x in vst[1:]]
            real_total = lead + vdur + END_HOLD
            os.environ["VOICE_FILE"] = wav
            os.environ["VOICE_DELAY"] = str(lead)
        else:
            real_starts, real_total = ts, total
        fmap = time_map(ts, total, real_starts, real_total)
        pg.evaluate(f"window.RTOTAL = {real_total}")
        if stills:
            base = os.path.splitext(out)[0]
            for t in (1.6, 6.5, 15.0, 19.0, 21.4, 25.2, 30.0):
                pg.evaluate(f"seek({t})")
                pg.screenshot(path=f"{base}_{t:05.1f}.jpg", type="jpeg", quality=88)
            b.close()
            return
        tmp = out + ".video.mp4"
        enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS),
                                "-c:v", "mjpeg", "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                                "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
        n = int(real_total * FPS)
        for i in range(n):
            rt = i / FPS
            pg.evaluate(f"seek({fmap(rt):.4f}, {rt:.4f})")
            enc.stdin.write(pg.screenshot(type="jpeg", quality=92))
        enc.stdin.close()
        if enc.wait() != 0:
            sys.exit("video encode fail")
        b.close()
    finish(out, tmp, real_total, lambda te: next((k / FPS for k in range(n) if fmap(k / FPS) >= te), te))


def events():
    ev = [(0.15, "bell"), (0.4, "bell"), (0.65, "bell"), (0.7, "whoosh"), (3.3, "whoosh")]
    ev += [(4.3 + i * 0.22, "pop") for i in range(4)]
    ev += [(9.5, "whoosh")] + [(10.7 + i * 0.55, "pop") for i in range(3)] + [(12.6, "whoosh"), (14.5, "pop")]
    ev += [(16.7, "whoosh"), (17.4, "bell"), (19.9, "bell"), (22.1, "bell"), (24.2, "win"), (27.3, "whoosh"), (29.2, "pop")]
    return ev


def finish(out, tmp, total, to_real=lambda x: x):
    aud = out + ".audio.m4a"
    sfx_track(aud, total, [(to_real(t), k) for t, k in events()])
    tmp_out = out + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-i", aud, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "copy", "-shortest", "-movflags", "+faststart", tmp_out], check=True)
    os.replace(tmp_out, out)
    for f in (tmp, aud, out + ".voice.wav"):
        if os.path.exists(f):
            os.remove(f)
    print("REEL:", out)


if __name__ == "__main__":
    main()
