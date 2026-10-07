"""Build three alignment variations of the monarcbuild.com homepage for approval.

Usage: python build_variants.py
Writes variant-a.html, variant-b.html, variant-c.html next to this script.

Content follows Section Spec.md; palette, type, and layout follow Style Guide.md.
Pending rules use the render placeholders named in the Style Guide. These files are
for review only. The deploy path is projects/monarcbuild-site/public_html/.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ASSETS = (HERE / "../../monarcbuild-site/public_html/assets").resolve()


def asset(rel):
    return (ASSETS / rel).as_uri()


VARIANTS = {
    "a": "Variant A. Centered headings, split bodies. About 50/50, steps as a numbered list, results and portfolio in thirds, two tier cards.",
    "b": "Variant B. Everything centered on one axis. Photo above text, steps centered, tiles with centered text.",
    "c": "Variant C. Alternating 50/50. Headings left inside the text half, media side alternates down the page. Hero and final ask stay centered.",
}

PLACEHOLDER_NOTE = "Placeholders in this render: faces (Cormorant Garamond, Inter), ground (#F6F3EF with Sand bands), 96px rhythm, founder photo, portfolio screenshots, VSL stills, calendar link."

CSS = """
:root{--oak:#61534E;--blue:#2F334D;--charcoal:#4B4C5C;--stone:#6E6E78;--sand:#C2B3A9;--paper:#F6F3EF;--white:#FFFFFF;
--serif:'Cormorant Garamond',Georgia,'Times New Roman',serif;--sans:Inter,system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
--col:960px;--pad:96px;--gap:56px;--stack:24px}
*{box-sizing:border-box;margin:0;padding:0}
html{color-scheme:light}
body{background:var(--paper);color:var(--charcoal);font:400 18px/1.6 var(--sans)}
img{display:block;width:100%;height:100%;object-fit:cover}
a{color:inherit;text-decoration:none}
h1,h2,h3{font-family:var(--serif);font-weight:400;color:var(--blue);text-wrap:balance}
h1{font-size:56px;line-height:1.1;letter-spacing:-0.01em}
h2{font-size:40px;line-height:1.15}
h3{font-size:24px;line-height:1.25}
.sub{font-family:var(--serif);font-size:22px;line-height:1.4;color:var(--charcoal);max-width:34em}
.label{font-family:var(--sans);font-size:13px;letter-spacing:0.12em;text-transform:uppercase;color:var(--stone)}
.col{max-width:var(--col);margin:0 auto;padding:0 24px}
section{padding:var(--pad) 0}
section.band{background:var(--sand)}
.head{display:grid;gap:var(--stack);margin-bottom:var(--gap)}
.stack{display:grid;gap:var(--stack)}
.btn{display:inline-block;background:var(--oak);color:var(--white);font-family:var(--sans);font-size:16px;padding:16px 28px;border-radius:999px;letter-spacing:0.01em}
.nav{position:sticky;top:0;background:var(--paper);border-bottom:1px solid var(--sand);z-index:2}
.nav .col{display:flex;align-items:center;justify-content:space-between;height:80px;max-width:1200px}
.nav .brand{font-family:var(--serif);font-size:22px;letter-spacing:0.18em;text-transform:uppercase;color:var(--blue)}
.nav nav{display:flex;gap:28px;font-size:14px;color:var(--stone)}
.banner{background:var(--blue);color:var(--white);font-size:13px;padding:10px 24px;text-align:center}
.banner small{display:block;opacity:.75;margin-top:4px}
.media{background:var(--sand);overflow:hidden;position:relative}
.media.r169{aspect-ratio:16/9}.media.r43{aspect-ratio:4/3}.media.r45{aspect-ratio:4/5}.media.r1610{aspect-ratio:16/10}
.media .tag{position:absolute;left:12px;bottom:12px;background:rgba(246,243,239,.92);color:var(--charcoal);font-size:12px;padding:6px 10px}
.placeholder{display:flex;align-items:center;justify-content:center;color:var(--stone);font-size:14px;text-align:center;padding:16px;background:rgba(255,255,255,.5);border:1px dashed var(--stone)}
.hero .col{text-align:center;display:grid;gap:var(--stack);justify-items:center}
.hero .sub{margin:0 auto}
.vsl{width:100%;display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.vsl .media{aspect-ratio:16/9}
.vsl-caption{font-size:14px;color:var(--stone)}
.split{display:grid;grid-template-columns:1fr 1fr;gap:var(--gap);align-items:start}
.split.flip>.text{order:2}.split.flip>.visual{order:1}
.thirds{display:grid;grid-template-columns:repeat(3,1fr);gap:32px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:32px}
.tile{display:grid;gap:12px}
.tile .num{font-family:var(--serif);font-size:40px;color:var(--blue);line-height:1}
.tile p{font-size:16px}
ol.steps{list-style:none;display:grid;gap:28px;counter-reset:s}
ol.steps li{display:grid;grid-template-columns:56px 1fr;gap:16px;align-items:start}
ol.steps li::before{counter-increment:s;content:counter(s);font-family:var(--serif);font-size:40px;line-height:1;color:var(--blue)}
ol.steps li.loop::before{content:"\\21BB";font-size:40px}
ol.steps h3{font-size:22px}
ol.steps p{font-size:16px}
.tier{background:var(--white);padding:32px;display:grid;gap:16px}
.tier ul{list-style:none;display:grid;gap:8px;font-size:16px;border-top:1px solid var(--sand);padding-top:16px}
.tier ul li::before{content:"\\00B7\\00A0";color:var(--stone)}
.final .col{text-align:center;display:grid;gap:var(--stack);justify-items:center}
footer{padding:40px 0;border-top:1px solid var(--sand);font-size:14px;color:var(--stone)}
footer .col{display:flex;justify-content:space-between;flex-wrap:wrap;gap:16px}
footer nav{display:flex;gap:20px}
.center{text-align:center}
.center .sub{margin:0 auto}
.center .stack{justify-items:center}
.center .stack p{max-width:60ch}
.center .split{grid-template-columns:1fr;justify-items:center}
.center .split .visual{width:min(420px,100%)}
.center ol.steps{width:min(640px,100%);margin:0 auto;text-align:left}
.center .tile{text-align:center}
.center .tier{text-align:center}
.center .tier ul{text-align:left}
.left{text-align:left}
.left .head{margin-bottom:var(--stack)}
@media (max-width:767px){
:root{--pad:64px;--gap:32px;--stack:16px}
h1{font-size:36px}h2{font-size:30px}h3{font-size:22px}.sub{font-size:19px}
body{font-size:17px}
.nav nav{display:none}.nav .col{height:64px}.nav .brand{font-size:18px}.nav .btn{padding:10px 16px;font-size:14px}
.split,.split.flip,.thirds,.two,.vsl{grid-template-columns:1fr}
.split.flip>.text{order:1}.split.flip>.visual{order:2}
.center .split .visual{width:100%}
ol.steps li{grid-template-columns:40px 1fr}
ol.steps li::before{font-size:30px}
}
"""

STEPS = [
    ("Onboarding.", "New landing pages mapped to your service area and the brands you spec.", ""),
    ("Targeting and offering.", "Which searches each page is built for, and the offer on it. Copy pending.", ""),
    ("Managed Google Ads on every page.", "Each landing page gets its own campaign pointing at it.", ""),
    ("The phone starts ringing.", "Buyers already searching land on the page built for that search.", ""),
    ("5 minute response, meeting booked (Level 2).", "A person calls the lead and books your calendar.", ""),
    ("You close the meetings.", "You show up to the appointment. That is the whole job.", ""),
    ("The loop.", "Optimize the pages and the messaging. More revenue, more ad spend, repeat.", "loop"),
]

TILES = [
    ("hero/hero-rough-in.jpg", "$70k", "Georgian Colonial restoration. Whole home audio, James Loudspeaker indoors and out, wired from rough-in. Found the #1 page for \"whole home audio in Annapolis.\"", "Rough-in of a Georgian Colonial with low voltage wire runs"),
    ("hero/hero-waterfront.jpg", "$91k", "Waterfront great room. Lutron Ketra lighting, from $2.5k of Google Ads.", "Waterfront great room at sunset with recessed lighting"),
    ("projects/baltimore-penthouse-frame-01.jpg", "$50k", "Baltimore penthouse. Control4 and Lutron retrofit.", "Baltimore penthouse at night, lighting scene"),
]

LOREM = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Body copy is not written yet. It will be short, specific, and in the register of references/voice.md."


def steps_html():
    out = ['<ol class="steps">']
    for title, body, cls in STEPS:
        out.append(f'<li class="{cls}"><div class="stack" style="gap:6px"><h3>{title}</h3><p>{body}</p></div></li>')
    out.append("</ol>")
    return "".join(out)


def tiles_html(stacked=False):
    cls = "stack" if stacked else "thirds"
    out = [f'<div class="{cls}">']
    for img, num, line, alt in TILES:
        out.append(f'<div class="tile"><div class="media r43"><img src="{asset(img)}" alt="{alt}"></div><div class="num">{num}</div><p>{line}</p></div>')
    out.append("</div>")
    return "".join(out)


def portfolio_html(stacked=False):
    cls = "stack" if stacked else "thirds"
    items = "".join(f'<div class="media r1610 placeholder">Portfolio screenshot pending<br>{t}</div>' for t in ("Client site", "Landing page per service and area", "The ad and the #1 ranking"))
    return f'<div class="{cls}">{items}</div>'


def tiers_html(stacked=False):
    cls = "stack" if stacked else "two"
    l1 = '<div class="tier"><span class="label">Level 1</span><h3>Site, search, and ads. Reported weekly.</h3><ul><li>Website: new build, or takeover of yours</li><li>One landing page per service and per service area</li><li>Managed Google Ads behind those pages</li><li>SEO: local, Google Business Profile, content, technical</li><li>Weekly PDF report. One 15 minute meeting a month</li><li>Ad spend paid on top. $1,000 a month minimum recommended</li></ul></div>'
    l2 = '<div class="tier"><span class="label">Level 2</span><h3>Everything in Level 1, plus First Responder.</h3><ul><li>A person calls every lead within 5 minutes</li><li>9am to 7pm Eastern, Monday to Friday</li><li>Qualified on your pricing floor and service area</li><li>Booked into your calendar, email follow-up after</li><li>Month to month. Add it or drop it any time</li></ul></div>'
    return f'<div class="{cls}">{l1}{l2}</div>'


def head(h2, sub, label=None, cls="head"):
    lab = f'<span class="label">{label}</span>' if label else ""
    return f'<div class="{cls}">{lab}<h2>{h2}</h2><p class="sub">{sub}</p></div>'


def founder():
    return '<div class="media r45 placeholder">Founder photo pending</div>'


def section(sid, mode, band, h2, sub, body_visual, body_text, label, flip=False, stacked_visual=None):
    """mode a: centered head, body as given. mode b: everything centered. mode c: split text|visual."""
    band_cls = " band" if band else ""
    if mode == "a":
        inner = f'<div class="col">{head(h2, sub, label, cls="head center")}{body_text or ""}{body_visual}</div>'
    elif mode == "b":
        inner = f'<div class="col center">{head(h2, sub, label)}{stacked_visual if stacked_visual is not None else body_visual}{body_text or ""}</div>'
    else:
        flip_cls = " flip" if flip else ""
        inner = f'<div class="col left"><div class="split{flip_cls}"><div class="text stack">{head(h2, sub, label)}{body_text or ""}</div><div class="visual">{stacked_visual if stacked_visual is not None else body_visual}</div></div></div>'
    return f'<section id="{sid}" class="{band_cls.strip()}">{inner}</section>'


def page(mode):
    hero_imgs = "".join(
        f'<div class="media"><img src="{asset(p)}" alt="{a}"></div>'
        for p, a in (("hero/hero-rough-in.jpg", "Rough-in wiring in a Georgian Colonial"), ("hero/hero-waterfront.jpg", "Waterfront great room at sunset"), ("hero/hero-exterior.jpg", "Front elevation of a Georgian Colonial"))
    )
    hero = f'''<section id="hero" class="hero"><div class="col">
<h1>Booked appointments with high ticket prospects.</h1>
<p class="sub">You run the marketing, the sales calls, the appointments, and the installs. Monarc runs top of funnel so high ticket work keeps coming.</p>
<a class="btn" href="#book">Book a 15 minute call</a>
<div class="vsl">{hero_imgs}</div>
<p class="vsl-caption">Video coming. The VSL slot is 16:9 and centered; these stills hold it until Jonathan records it.</p>
</div></section>'''

    about_text = f'<div class="stack"><p>{LOREM}</p><p>Lutron certified. AIA presentations to architects. CEDIA workshops.</p></div>'
    about = section("about", mode, True, "Sold and installed before we marketed.",
                    "Lutron certified. AIA presentations to architects. CEDIA workshops. Monarc was built by someone who has wired the rough-in and closed the six figure proposal.",
                    body_visual=(f'<div class="split"><div class="visual">{founder()}</div><div class="text">{about_text}</div></div>' if mode == "a" else founder()),
                    body_text=(about_text if mode in ("b", "c") else ""), label="About")

    how = section("how", mode, False, "How it works. Seven steps, one loop.",
                  "One kickoff meeting, then the pages, the ads, and the phone. Step seven runs every month.",
                  body_visual=steps_html(), body_text="", label="Our process", flip=True)

    results_line = '<p class="sub" style="font-size:18px">That one contractor is now over $500k in lifetime value.</p>'
    results = section("results", mode, True, "One search term. $500k and counting.",
                      "Three jobs from one ranked page and $2.5k of ads. Numbers from the winning proposals.",
                      body_visual=tiles_html(), body_text=(results_line if mode == "c" else ""), label="Similar results",
                      stacked_visual=(tiles_html(stacked=True) if mode == "c" else None))
    if mode in ("a", "b"):
        results = results.replace("</div></section>", f"{results_line}</div></section>")

    portfolio = section("portfolio", mode, False, "What we build.",
                        "Sites, landing pages per service and area, and the ads behind them.",
                        body_visual=portfolio_html(), body_text="", label="Portfolio", flip=True,
                        stacked_visual=(portfolio_html(stacked=True) if mode == "c" else None))

    pilot = '<p style="font-size:16px;margin-top:24px">60 day pilot. No setup fee. $1,000 of ad spend matched. Day 60: continue on a 6 month term, or walk with the site, the pages, and the data.</p>'
    offer = section("offer", mode, True, "Two tiers. Both start with a pilot.",
                    "Start on Level 1 for 60 days, no setup fee, $1,000 of ad spend matched. Day 60: continue or walk and keep the site.",
                    body_visual=tiers_html(), body_text=(pilot if mode == "c" else ""), label="The offer",
                    stacked_visual=(tiers_html(stacked=True) if mode == "c" else None))
    if mode in ("a", "b"):
        offer = offer.replace("</div></section>", f"{pilot}</div></section>")

    final = '''<section id="book" class="final"><div class="col">
<span class="label">Next step</span>
<h2>Your next high ticket job is searching now.</h2>
<p class="sub">Fifteen minutes. Bring nothing.</p>
<a class="btn" href="#book">Book a 15 minute call</a>
<p class="vsl-caption">Calendar link pending. Button goes to the Google Calendar appointment schedule.</p>
</div></section>'''

    footer = '''<footer><div class="col">
<div>Monarc Build, LLC &middot; Annapolis, Maryland<br><a href="mailto:jonathan@monarcbuild.com">jonathan@monarcbuild.com</a> &middot; phone pending</div>
<nav><a href="#about">About</a><a href="#how">How it works</a><a href="#results">Results</a><a href="#portfolio">Portfolio</a><a href="#offer">The offer</a></nav>
</div></footer>'''

    nav = '''<header class="nav"><div class="col"><a class="brand" href="#hero">Monarc Build</a>
<nav><a href="#about">About</a><a href="#how">How it works</a><a href="#results">Results</a><a href="#portfolio">Portfolio</a><a href="#offer">The offer</a></nav>
<a class="btn" href="#book">Book a 15 minute call</a></div></header>'''

    banner = f'<div class="banner">{VARIANTS[mode]}<small>{PLACEHOLDER_NOTE}</small></div>'

    return f'''<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Monarc Build: booked appointments with high ticket prospects</title>
<meta name="description" content="Monarc runs top of funnel for custom home integrators: the site, landing pages per service and area, managed Google Ads, SEO, and a person who calls every lead within five minutes.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;1,400&family=Inter:ital,wght@0,400;1,400&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head><body>
{banner}
{nav}
<main>
{hero}
{about}
{how}
{results}
{portfolio}
{offer}
{final}
</main>
{footer}
</body></html>'''


def main():
    for mode in VARIANTS:
        out = HERE / f"variant-{mode}.html"
        out.write_text(page(mode), encoding="utf-8")
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
