// Transport: play, pause, J/K/L shuttle, frame steps and seeks. The audio engine keeps the clock; while playing,
// a requestAnimationFrame loop moves the playhead and the monitor draws each frame.
import { S, emit } from "./store.js";
import { audio } from "./media/audio.js";
import { seqEnd, FPS } from "./model/doc.js";

let raf = 0;
let shuttleRate = 0;

function end() { return S.doc ? seqEnd(S.doc) : 0; }

function loop() {
  cancelAnimationFrame(raf);
  const tick = () => {
    if (!S.playing) return;
    const f = audio.now();
    const e = end();
    if (shuttleRate > 0 && f >= e) { pb.pause(e); return; }
    if (shuttleRate < 0 && f <= 0) { pb.pause(0); return; }
    S.playhead = f;
    emit("playhead", true);
    raf = requestAnimationFrame(tick);
  };
  raf = requestAnimationFrame(tick);
}

export const pb = {
  play(rate = 1) {
    if (!S.doc) return;
    if (rate > 0 && S.playhead >= end() - 1) S.playhead = 0;
    shuttleRate = rate;
    audio.start(S.playhead, rate);
    S.playing = true;
    emit("play");
    loop();
  },
  pause(at) {
    if (!S.playing) return;
    S.playhead = at !== undefined ? at : Math.max(0, Math.round(audio.now()));
    audio.stop();
    S.playing = false;
    shuttleRate = 0;
    emit("play");
    emit("playhead", true);
  },
  toggle() { if (S.playing) pb.pause(); else pb.play(1); },
  // J / K / L: each extra L doubles forward speed (1, 2, 4); J does the same backwards; K stops
  shuttle(dir) {
    if (!S.doc) return;
    let r = shuttleRate;
    if (dir === 0) { pb.pause(); return; }
    if (dir > 0) r = r > 0 ? Math.min(4, r * 2) : 1;
    else r = r < 0 ? Math.max(-4, r * 2) : -1;
    const from = S.playing ? audio.now() : S.playhead;
    S.playhead = from;
    audio.stop();
    S.playing = false;
    shuttleRate = r;
    audio.start(from, r);
    S.playing = true;
    emit("play");
    loop();
  },
  seek(f) {
    const max = Math.max(end(), 0);
    f = Math.max(0, Math.min(max, Math.round(f)));
    S.playhead = f;
    if (S.playing) audio.start(f, shuttleRate || 1);
    else audio.prefetch(S.doc, f, f + 3 * FPS);
    emit("playhead", true);
  },
  step(n) { if (S.playing) pb.pause(); pb.seek(Math.round(S.playhead) + n); },
  t() { return S.playing ? audio.now() : S.playhead; },
  rate() { return S.playing ? shuttleRate : 0; },
};
