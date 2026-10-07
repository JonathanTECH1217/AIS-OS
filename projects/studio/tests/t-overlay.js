import { test, wait, until } from "./harness.js";

test("overlay", async (t, st) => {
  await t.fresh();
  st.pb.seek(30);
  await t.settle();
  const under = t.pixel(540, 960);
  // text title on V2 (T tool on the timeline)
  t.key("T");
  await t.tlClick(10, "V2");
  t.key("V");
  const txt = t.clip("V2")[0];
  t.ok("the Type tool adds a text clip on V2 (G23)", txt && txt.type === "text", JSON.stringify(txt));
  t.eq("3 seconds long", txt.out - txt.in, 90);
  // shapes: a box at the center, 50 % opacity blends with the video
  st.selectOnly([]);
  st.actions.run("newBox");
  await wait(30);
  const box = t.clip("V2").find((c) => c.type === "shape");
  t.ok("New shape > Box adds a shape clip", !!box);
  st.history.commit("paint", (d) => { const c = d.clips.find((x) => x.id === box.id); c.shape.fill = "#FFFFFF"; c.fx.posY = { v: 960 }; c.fx.opacity = { v: 50 }; });
  st.pb.seek(31); st.pb.seek(30);
  await t.settle();
  const mix = t.pixel(540, 960);
  const want = under.slice(0, 3).map((u) => (u + 255) / 2);
  t.ok("50 % white box blends half and half with the video", mix.slice(0, 3).every((c, i) => Math.abs(c - want[i]) < 18), `${mix} vs ${want} (under ${under})`);
  // circle and arrow (each placed at the playhead on V2 overwrites what was there, as in Premiere)
  st.actions.run("newCircle"); await wait(20);
  t.ok("New shape > Circle adds an ellipse", t.clip("V2").some((c) => c.type === "shape" && c.shape.kind === "ellipse"));
  st.actions.run("newArrow"); await wait(20);
  t.ok("New shape > Arrow adds an arrow", t.clip("V2").some((c) => c.type === "shape" && c.shape.kind === "arrow"));
  t.eq("placing over it replaced the one before (overwrite)", t.clip("V2").filter((c) => c.type === "shape").length, 1);
  // image overlay from the bin: the logo (blue #0B57D0) centered
  st.history.commit("clear V2", (d) => { d.clips = d.clips.filter((c) => c.track !== "V2"); });
  st.actions.run("placeAsset", { item: { kind: "asset", id: t.asset("logo.png").id }, f: 0, track: "V2" });
  await until(() => st.lib.bitmap(t.asset("logo.png").id), 4000);
  st.pb.seek(31); st.pb.seek(30);
  await t.settle();
  const px = t.pixel(540 + 150, 960);
  t.ok("the logo draws on top of the video", Math.abs(px[0] - 11) < 30 && Math.abs(px[2] - 208) < 30, String(px));
  const img = t.clip("V2")[0];
  t.eq("image keeps its own size (400x160 at 100 %)", st.doc.baseSize(img, st.lib), { w: 400, h: 160 });
  // B-roll video on V2
  st.history.commit("clear V2", (d) => { d.clips = d.clips.filter((c) => c.track !== "V2"); });
  st.actions.run("placeAsset", { item: { kind: "asset", id: t.asset("broll5.mp4").id }, f: 0, track: "V2" });
  await wait(30);
  const b = t.clip("V2")[0];
  t.ok("a video from Assets goes on V2 as B-roll", b && b.type === "video" && b.out - b.in === 150);
});
