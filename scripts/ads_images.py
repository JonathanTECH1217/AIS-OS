"""Generated renders for the service pages (Style Guide Media 1; landing-page skill, "images" mode).

Usage:
  python scripts/ads_images.py download <jobs.json> <results.json>
  python scripts/ads_images.py pick <slug> hero <n>
  python scripts/ads_images.py pick <slug> card <k> <n>
  python scripts/ads_images.py contact <slug>
  python scripts/ads_images.py thumbs

download  Fetches every job in results.json (index -> file name under "base") and saves it as a compressed JPEG
          at projects/Landing Page Build/candidates/<file> from jobs.json (heroes 1600 px wide, cards 800 px).
          A file already on disk is skipped, so a rerun only fetches what is missing.
pick      Exports Jonathan's pick into the site mirror: a hero to public_html/assets/generated/<slug>/hero.jpg
          (1600 wide) and hero-800.jpg (800 wide for srcset), each squeezed under 300 KB; a card render to
          card-<k>.jpg (320 px square) under 60 KB. Writes nothing else and pushes nothing.
contact   Writes one contact sheet per page (all candidates in a grid, numbered) to
          projects/Landing Page Build/renders/<today>/candidates-<slug>.jpg for review in chat.
thumbs    The homepage's small pictures (the search-page homepage, 2026-09-26): each service page's hero at 240x180 as
          assets/generated/<slug>/thumb.jpg (the automation sticker set on its dark ground), and the three proof
          jobs as 180px squares in assets/projects/thumbs/ (the Georgian from its exterior photo, the waterfront from
          the ceiling and glass wall crop, the penthouse from the harbor tower).
"""
import datetime as dt
import io
import json
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES = ROOT / "projects" / "Landing Page Build" / "candidates"
RENDERS = ROOT / "projects" / "Landing Page Build" / "renders"
GENERATED = ROOT / "projects" / "monarcbuild-site" / "public_html" / "assets" / "generated"
HERO_W, CARD_W = 1600, 800


def save_jpeg(img, path, width, max_kb=None, quality=84):
    img = img.convert("RGB")
    if img.width > width:
        img = img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    q = quality
    while True:
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
        if max_kb is None or buf.tell() <= max_kb * 1024 or q <= 50:
            break
        q -= 4
    path.write_bytes(buf.getvalue())
    return buf.tell() // 1024, q


def tight(img, pad=0.10):
    """Crop a card render to its object: find what differs from the flat background (sampled at the corners), keep a
    square around it with a 10% margin, so the object fills a small card tile instead of floating in empty ground
    (2026-09-26: the SEO pin with the trade tools read as specks at 88px)."""
    w, h = img.size
    corners = [img.getpixel((4, 4)), img.getpixel((w - 5, 4)), img.getpixel((4, h - 5)), img.getpixel((w - 5, h - 5))]
    bg = tuple(sum(c[i] for c in corners) // 4 for i in range(3))
    diff = img.point(lambda v: v).convert("RGB")
    mask = Image.new("L", img.size, 0)
    px, mp = diff.load(), mask.load()
    step = max(1, w // 512)
    for y in range(0, h, step):
        for x in range(0, w, step):
            r, g, b = px[x, y]
            if abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2]) > 60:
                mp[x, y] = 255
    box = mask.getbbox()
    if not box:
        return img
    x0, y0, x1, y1 = box
    side = max(x1 - x0, y1 - y0) * (1 + 2 * pad)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    left, top = max(0, cx - side / 2), max(0, cy - side / 2)
    right, bottom = min(w, left + side), min(h, top + side)
    return img.crop((int(left), int(top), int(right), int(bottom)))


def download(jobs_path, results_path):
    jobs = json.loads(Path(jobs_path).read_text(encoding="utf-8"))["jobs"]
    results = json.loads(Path(results_path).read_text(encoding="utf-8"))
    base = results["base"]
    urls = results["urls"]
    done = skipped = missing = 0
    for job in jobs:
        out = CANDIDATES / job["file"]
        name = urls.get(str(job["index"]))
        if not name:
            print(f"  {job['index']:>2} {job['file']}: no result url yet")
            missing += 1
            continue
        if out.exists():
            skipped += 1
            continue
        with urllib.request.urlopen(base + name, timeout=120) as r:
            data = r.read()
        img = Image.open(io.BytesIO(data))
        width = HERO_W if "/hero-" in job["file"] else CARD_W
        kb, q = save_jpeg(img, out, width)
        print(f"  {job['index']:>2} {job['file']}: {img.width}x{img.height} source, saved {kb} KB (q{q})")
        done += 1
    print(f"{done} downloaded, {skipped} already on disk, {missing} without a url")


def pick(slug, kind, *nums):
    if kind == "hero":
        n = int(nums[0])
        src = CANDIDATES / slug / f"hero-{n}.jpg"
        img = Image.open(src)
        kb1, q1 = save_jpeg(img, GENERATED / slug / "hero.jpg", 1600, max_kb=300)
        kb2, q2 = save_jpeg(img, GENERATED / slug / "hero-800.jpg", 800, max_kb=120)
        print(f"{slug}: hero {n} -> hero.jpg {kb1} KB (q{q1}), hero-800.jpg {kb2} KB (q{q2})")
    elif kind == "card":
        k, n = int(nums[0]), int(nums[1])
        src = CANDIDATES / slug / f"card-{k}-{n}.jpg"
        img = tight(Image.open(src).convert("RGB"))
        kb, q = save_jpeg(img, GENERATED / slug / f"card-{k}.jpg", 320, max_kb=60)
        print(f"{slug}: card {k} candidate {n} -> card-{k}.jpg {kb} KB (q{q})")
    else:
        sys.exit("kind is hero or card")


def contact(slug):
    folder = CANDIDATES / slug
    heroes = sorted(folder.glob("hero-*.jpg"))
    cards = sorted(folder.glob("card-*-*.jpg"))
    tiles = [(p, 480, 360) for p in heroes] + [(p, 240, 240) for p in cards]
    if not tiles:
        sys.exit(f"no candidates in {folder}")
    pad, label_h = 16, 28
    rows = []
    if heroes:
        rows.append([(p, 480, 360) for p in heroes])
    for k in sorted({p.stem.split("-")[1] for p in cards}):
        rows.append([(p, 240, 240) for p in cards if p.stem.split("-")[1] == k])
    width = max(sum(w for _, w, _ in r) + pad * (len(r) + 1) for r in rows)
    height = sum(max(h for _, _, h in r) + label_h + pad for r in rows) + pad
    sheet = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(sheet)
    y = pad
    for r in rows:
        x = pad
        rh = max(h for _, _, h in r)
        for p, w, h in r:
            im = Image.open(p).convert("RGB")
            im.thumbnail((w, h), Image.LANCZOS)
            sheet.paste(im, (x, y + label_h))
            draw.text((x, y + 6), p.stem, fill=(20, 20, 20))
            x += w + pad
        y += rh + label_h + pad
    outdir = RENDERS / dt.date.today().isoformat()
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"candidates-{slug}.jpg"
    sheet.save(out, "JPEG", quality=82)
    print(out)


SERVICE_SLUGS = ["google-ads", "website-build", "seo", "email-marketing", "facebook-ads", "ai-automation"]
PROOF_THUMBS = [  # (source under assets/, output name, vertical position of the square crop, 0 top to 1 bottom)
    ("georgian/exterior-01.jpg", "georgian.jpg", 0.5),
    ("projects/waterfront-great-room.jpg", "waterfront.jpg", 0.38),
    ("projects/baltimore-penthouse.jpg", "penthouse.jpg", 0.5),
]
PROOF_CARDS = [  # the homepage's 4:3 proof cards (source, output name, vertical position of the crop)
    # Jonathan, 2026-09-27: the Georgian card shows the interior (the rough-in), cropped high like the Google Ads page
    # (center 20%) so the PHA shirt at the bottom of the frame stays out (Style Guide Media 1 and 4)
    ("georgian/rough-in-01.jpg", "georgian.jpg", 0.2),
    ("projects/waterfront-great-room.jpg", "waterfront.jpg", 0.38),
    ("projects/baltimore-penthouse.jpg", "penthouse.jpg", 0.5),
]


def square(img, ypos=0.5):
    w, h = img.size
    s = min(w, h)
    left = (w - s) // 2
    top = round((h - s) * ypos)
    return img.crop((left, top, left + s, top + s))


def thumbs():
    assets = GENERATED.parent
    # thumb.jpg 240x180 (the round 1 results list) and tile.jpg 600x450 (the homepage's service cards, round 3, 2026-09-27)
    for slug in SERVICE_SLUGS:
        folder = GENERATED / slug
        for name, (tw, th), max_kb in [("thumb.jpg", (240, 180), 20), ("tile.jpg", (600, 450), 70)]:
            if (folder / "hero-sticker.png").exists():
                sticker = Image.open(folder / "hero-sticker.png").convert("RGBA")
                sticker.thumbnail((round(tw * 0.88), round(th * 0.83)), Image.LANCZOS)
                ground = Image.new("RGBA", (tw, th), (11, 18, 32, 255))  # the time theme's ground, #0B1220
                ground.alpha_composite(sticker, ((tw - sticker.width) // 2, (th - sticker.height) // 2))
                img = ground
            else:
                img = Image.open(folder / "hero.jpg").convert("RGB")
                w, h = img.size
                want = h * 4 // 3
                if w > want:  # keep 4:3
                    img = img.crop(((w - want) // 2, 0, (w - want) // 2 + want, h))
                img = img.resize((tw, th), Image.LANCZOS)
            kb, q = save_jpeg(img, folder / name, tw, max_kb=max_kb)
            print(f"{slug}/{name} {kb} KB (q{q})")
    for src, out, ypos in PROOF_THUMBS:
        img = square(Image.open(assets / src).convert("RGB"), ypos).resize((180, 180), Image.LANCZOS)
        kb, q = save_jpeg(img, assets / "projects" / "thumbs" / out, 180, max_kb=16)
        print(f"projects/thumbs/{out} {kb} KB (q{q})")
    for src, out, ypos in PROOF_CARDS:
        # the homepage's proof cards (round 3): 4:3 at up to 800 wide, never upscaled
        img = Image.open(assets / src).convert("RGB")
        w, h = img.size
        if w * 3 > h * 4:  # wider than 4:3: trim the sides
            nw = h * 4 // 3
            img = img.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
        else:  # taller: keep the band at ypos
            nh = w * 3 // 4
            top = round((h - nh) * ypos)
            img = img.crop((0, top, w, top + nh))
        kb, q = save_jpeg(img, assets / "projects" / "cards" / out, 800, max_kb=90)
        print(f"projects/cards/{out} {img.width}x{img.height} source crop, {kb} KB (q{q})")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "download" and len(sys.argv) == 4:
        download(sys.argv[2], sys.argv[3])
    elif cmd == "pick" and len(sys.argv) >= 5:
        pick(sys.argv[2], sys.argv[3], *sys.argv[4:])
    elif cmd == "contact" and len(sys.argv) == 3:
        contact(sys.argv[2])
    elif cmd == "thumbs":
        thumbs()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
