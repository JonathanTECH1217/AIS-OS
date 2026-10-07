"""Build the seeded media folder the Studio tests run against: tests/fixtures/seed/ (git-ignored output).

  python projects/studio/tests/fixtures/make.py

  inbox/src20.mp4   20 s, 1080x1920, 30 fps. The top 80 px carry the frame number as a 12-bit barcode (bit i is the
                    90-px band starting at x = 90*i, bright = 1), so a test can read which frame the monitor shows.
                    A 440 Hz beep for the first 0.2 s of every second.
  assets/broll5.mp4 5 s of ffmpeg's test pattern, 1080x1920
  assets/logo.png   a 400x160 badge with transparency
  sfx/pop.wav       0.25 s 880 Hz blip
  .studio/<id>/transcript.json and moments.json for src20.mp4: made-up words every 0.5 s, so captions and the
                    bin's moments work without running the speech model
  .studio/<id>/speakers.json and speaker-labels.json: three voices without running the voice split. Words 0-11
                    are Jonathan (two groups, S1 and S4, both labeled his), 12-23 a woman ("Dana", S2), 24-35 a man
                    (no name, role owner: "Owner", S3)
  .studio/<id>/listen-fake.json: what Generate captions' second listen "hears" under STUDIO_FAKE_LISTEN (no speech
                    model in the tests): the same words, but "is" heard as "was" (word 2) and "thing" as "ring"
                    (word 4), "really" added in the pause after word 5, word 8 ("the") missed, "okay" added in Dana's
                    pause after word 17
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = HERE / "seed"
SEED_VERSION = "2026-10-02 generate captions"   # bump when the seed changes; the runners rebuild an older seed


def seed_current():
    try:
        return (SEED / ".seed-version").read_text() == SEED_VERSION
    except OSError:
        return False
sys.path.insert(0, str(HERE.parents[3] / "scripts"))


def main():
    import studio_common as sc
    ff = sc.ffmpeg_exe()
    if SEED.exists():
        shutil.rmtree(SEED)
    for d in ("inbox", "assets", "sfx", "projects", "ready", ".studio"):
        (SEED / d).mkdir(parents=True, exist_ok=True)
    src = SEED / "inbox" / "src20.mp4"
    bars = ("geq=lum='if(lt(Y,80),if(bitand(floor(N/pow(2,floor(X/90))),1),235,16),lum(X,Y))':"
            "cb='if(lt(Y,80),128,cb(X,Y))':cr='if(lt(Y,80),128,cr(X,Y))'")
    subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error",
                    "-f", "lavfi", "-i", "testsrc2=s=1080x1920:r=30:d=20",
                    "-f", "lavfi", "-i", "sine=f=440:r=48000:d=20",
                    "-filter_complex", f"[0:v]format=yuv420p,{bars}[v];[1:a]volume='if(lt(mod(t,1),0.2),0.5,0)':eval=frame[a]",
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-g", "30",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(src)], check=True)
    subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=s=1080x1920:r=30:d=5",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", str(SEED / "assets" / "broll5.mp4")], check=True)
    subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "sine=f=880:r=48000:d=0.25",
                    str(SEED / "sfx" / "pop.wav")], check=True)
    # a riser for Make trailer: a tone sweeping up over 1.5 s
    subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i",
                    "aevalsrc=0.4*sin(2*PI*(200+600*t)*t):s=48000:d=1.5", str(SEED / "sfx" / "Riser.wav")], check=True)
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (400, 160), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, 399, 159), radius=40, fill=(11, 87, 208, 255))
    d.ellipse((30, 30, 130, 130), fill=(255, 212, 0, 255))
    img.save(SEED / "assets" / "logo.png")

    aid = sc.asset_id(src)
    ad = SEED / ".studio" / aid
    ad.mkdir(parents=True, exist_ok=True)
    vocab = "so here is the thing most integrators lose the lead before the first call we fix that with one page".split()
    words, segments = [], []
    t = 0.3
    for i in range(36):
        w = vocab[i % len(vocab)] + ("." if i % 6 == 5 else "")
        words.append([round(t, 3), round(t + 0.4, 3), w])
        t += 0.5
        if i % 6 == 5:
            t += 0.6          # a pause: the next caption group starts fresh
    for s in range(0, 36, 6):
        segments.append([words[s][0], words[s + 5][1], s, s + 5])
    (ad / "transcript.json").write_text(json.dumps({"v": 1, "asset": aid, "rev": "fixture", "model": "fixture",
                                                    "duration": 20.0, "segments": segments, "words": words}))
    fake = []
    for i, w in enumerate(words):
        if i == 8:
            continue
        fake.append([w[0], w[1], {2: "was", 4: "ring"}.get(i, w[2])])
        if i == 5:
            fake.append([3.4, 3.75, "really"])
        if i == 17:
            fake.append([10.5, 10.95, "okay"])
    (ad / "listen-fake.json").write_text(json.dumps({"words": fake}))
    # the calls view (2026-10-01): a gatekeeper call holding m01, a booking holding m02 (Dana speaks from 7.5 s), a
    # stretch that isn't a call (hidden), and one between calls with a best bit of its own (shown, B22)
    (ad / "moments.json").write_text(json.dumps({
        "v": 1, "asset": aid, "model": "fixture", "created": "2026-09-29T00:00:00", "transcriptRev": "fixture",
        "calls": [
            {"id": "c01", "start": 0.0, "end": 7.2, "label": "Front desk, Fixture Electric", "outcome": "gatekeeper",
             "summary": "Asks for the owner"},
            {"id": "c02", "start": 7.2, "end": 16.5, "label": "Dana, Fixture Electric", "outcome": "booked",
             "summary": "Books a call"},
            {"id": "c03", "start": 16.5, "end": 18.0, "label": "Between dials", "outcome": "not_a_call", "summary": ""},
            {"id": "c04", "start": 18.0, "end": 20.0, "label": "Talking to the camera", "outcome": "not_a_call",
             "summary": ""}],
        "moments": [
            {"id": "m01", "call": "c01", "type": "objection", "start": 1.0, "end": 7.0, "title": "First six words",
             "reason": "Fixture", "strength": 5, "state": "new"},
            {"id": "m02", "call": "c02", "type": "booking", "start": 8.0, "end": 16.0, "title": "Second stretch",
             "reason": "Fixture", "strength": 3, "state": "new"},
            {"id": "m03", "call": "c04", "type": "best_line", "start": 18.2, "end": 19.8, "title": "To the camera",
             "reason": "Fixture", "strength": 4, "state": "new"}],
        "usage": {}, "cost": 0, "seconds": 0}))
    # voices: turns on word edges (words sit 0.5 s apart, 0.4 s long); voiceprints are small made-up unit vectors
    def turn(a, b, key):
        return [round(words[a][0] - 0.05, 3), round(words[b][1] + 0.05, 3), key]
    turns = [turn(0, 2, "S1"), turn(3, 5, "S4"), turn(6, 11, "S1"), turn(12, 23, "S2"), turn(24, 35, "S3")]
    emb = {"S1": [1, 0, 0, 0], "S4": [0.96, 0.28, 0, 0], "S2": [0, 1, 0, 0], "S3": [0, 0, 1, 0]}
    f0 = {"S1": 121.0, "S4": 126.0, "S2": 212.0, "S3": 109.0}
    groups = {k: {"win": 0, "sec": round(sum(t[1] - t[0] for t in turns if t[2] == k), 2),
                  "turns": sum(1 for t in turns if t[2] == k), "f0": f0[k], "emb": emb[k]} for k in emb}
    (ad / "speakers.json").write_text(json.dumps({
        "v": 1, "asset": aid, "rev": "fixture1", "model": "pyannote-seg-3.0+wespeaker-resnet34-LM", "threshold": 0.5,
        "created": "2026-09-30T00:00:00", "duration": 20.0, "windows": [[0.0, 20.0]], "turns": turns, "groups": groups}))
    (ad / "speaker-labels.json").write_text(json.dumps({
        "v": 1, "rev": "fixture1", "model": "fixture", "created": "2026-09-30T00:00:00", "jonathan": ["S1", "S4"],
        "voices": {"S2": {"gender": "woman", "name": "Dana", "role": "gatekeeper", "same_as": ""},
                   "S3": {"gender": "man", "name": "", "role": "owner", "same_as": ""}}}))
    (SEED / ".seed-version").write_text(SEED_VERSION)
    print(f"seed ready: {SEED} (src20 asset {aid})")
    return aid


if __name__ == "__main__":
    main()
