import { test, wait } from "./harness.js";

test("boot", async (t, st) => {
  t.eq("title", document.title, "Monarc Studio");
  const cs = getComputedStyle(document.documentElement);
  t.eq("dark background token", cs.getPropertyValue("--bg").trim(), "#131314");
  t.eq("color scheme dark", cs.colorScheme || cs.getPropertyValue("color-scheme").trim(), "dark");
  t.ok("Google Sans loaded", document.fonts.check('14px "Google Sans Text"'));
  t.ok("Montserrat Black loaded", document.fonts.check('56px "Montserrat Black"'));
  t.ok("Material Symbols loaded", document.fonts.check('20px "Material Symbols Outlined"'));
  // an icon that spills its name would be much wider than 1em
  const ic = document.querySelector(".tool .ms");
  t.ok("icons render as glyphs", ic && ic.getBoundingClientRect().width <= 22, ic && String(ic.getBoundingClientRect().width));
  t.eq("ten tools in the strip", document.querySelectorAll(".tools .tool").length, 10);
  t.near("tool strip is 48 px", document.getElementById("tools").getBoundingClientRect().width, 48, 1);
  for (const id of ["bin", "monitor", "side", "timeline", "topbar"]) t.ok(`panel ${id} present`, document.getElementById(id).getBoundingClientRect().height > 30);
  t.ok("bin lists the fixture recording", !!t.asset("src20.mp4"));
  t.ok("bin lists the sound", !!t.asset("pop.wav"));
  t.ok("bin lists the logo", !!t.asset("logo.png"));
  const h = await st.api.health();
  t.eq("server says Monarc Studio", h.app, "Monarc Studio");
  t.ok("menus File Edit Clip Sequence", [...document.querySelectorAll(".tb-menu")].map((b) => b.textContent).join(",") === "File,Edit,Clip,Sequence");
  await wait(100);
});
