// <video> elements that supply frames to the monitor. Each clip on screen (or starting soon) gets an element.
// While playing, drift against the timeline clock is corrected gently: a speed nudge when a little behind or ahead,
// a short wait when ahead, and a seek only past half a second, aimed ahead by what a seek takes in that file (the
// original recording has a keyframe only every 8 s, so a seek there can take a second). A seek in flight is never
// restarted while playing, or a slow one would never finish. While paused, seeks are latest-wins and the monitor
// redraws on `seeked`. Before any seek or new file the element's picture is copied, and the monitor draws the copy
// until the element has a picture again (2026-09-30, Jonathan: "on playback, sometimes the screen goes black").
import { FPS } from "../model/doc.js";

const MAX = 6;
const SNAP_MAX = 1920;       // longest side of the copied picture, px
const BEHIND_SEEK = 0.5;     // seconds behind the clock before a seek; below that the video speeds up to catch up
const AHEAD_SEEK = 1.0;      // seconds ahead before a seek; below that the video waits for the clock

export class VideoPool {
  constructor(host, onFrame) {
    this.host = host;              // hidden container (elements must stay in the DOM to keep decoding)
    this.onFrame = onFrame;
    this.items = [];
    this.stamp = 0;
    this.seekSecs = new Map();     // file url -> how long a seek takes there (running average, seconds)
  }

  el(item) { return item.v; }

  // steal: false for a clip that isn't on screen yet; it never takes an element another clip is using this frame
  acquire(key, url, steal = true) {
    let it = this.items.find((x) => x.key === key && x.url === url);
    if (it) { it.used = this.stamp; return it; }
    it = this.items.find((x) => x.key === key);
    if (!it) {
      if (this.items.length < MAX) {
        const v = document.createElement("video");
        v.muted = true; v.playsInline = true; v.preload = "auto"; v.crossOrigin = "anonymous";
        v.className = "pool-video";
        this.host.append(v);
        it = { v, key: null, url: null, used: 0, want: null, seeking: false, seekAt: 0, target: null, snap: null, snapKey: null, picKey: null };
        v.addEventListener("seeked", () => this.seeked(it));
        v.addEventListener("loadeddata", () => this.onFrame());
        this.items.push(it);
      } else {
        it = this.items.filter((x) => x.used < this.stamp).sort((a, b) => a.used - b.used)[0];
        if (!it && !steal) return null;
        it = it || this.items[0];
      }
    }
    if (it.url !== url) {
      this.snapshot(it);
      it.v.pause();
      it.url = url; it.want = null; it.seeking = false; it.seekAt = 0; it.target = null;
      it.v.src = url;
    }
    it.key = key;
    it.used = this.stamp;
    return it;
  }

  seeked(it) {
    const v = it.v;
    if (it.seekAt) this.learn(it.url, (performance.now() - it.seekAt) / 1000);
    it.seeking = false; it.seekAt = 0; it.target = null;
    it.picKey = it.key;
    // paused: latest-wins, so chase the newest spot asked for. Playing: sync() steers, and an old paused spot must
    // not pull the video back (it did: hundreds of seeks in a 12 s play, each one a moment with no picture)
    if (v.paused && it.want !== null && Math.abs(v.currentTime - it.want) > 0.5 / FPS) this.seek(it, it.want);
    else this.onFrame();
  }

  learn(url, secs) {
    if (!url || !(secs >= 0) || secs > 10) return;
    const old = this.seekSecs.get(url);
    this.seekSecs.set(url, old === undefined ? secs : old * 0.7 + secs * 0.3);
  }

  // how long a seek takes in this file, seconds (a guess until one has been timed)
  seekTime(url) { const s = this.seekSecs.get(url); return s === undefined ? 0.25 : s; }

  seek(it, t) {
    it.want = t;
    if (it.seeking) return;
    if (it.v.readyState < 1) {       // the file is still opening: seek once it knows its length (one listener, not one a frame)
      if (!it.metaWait) {
        it.metaWait = true;
        it.v.addEventListener("loadedmetadata", () => { it.metaWait = false; if (it.want !== null) this.seek(it, it.want); }, { once: true });
      }
      return;
    }
    this.snapshot(it);
    it.seeking = true; it.seekAt = performance.now(); it.target = t;
    it.v.currentTime = t;
  }

  // a seek while playing, aimed ahead by what a seek takes in this file so the video lands in step with the clock
  jump(it, t) {
    if (it.v.readyState < 1) return;
    const to = t + Math.min(2, this.seekTime(it.url));
    this.snapshot(it);
    it.want = null;
    it.seeking = true; it.seekAt = performance.now(); it.target = to;
    it.v.currentTime = to;
  }

  // mediaTime: seconds in the file; playing: whether the timeline is running at 1x
  sync(key, url, mediaTime, playing) {
    const it = this.acquire(key, url);
    const v = it.v;
    if (it.seeking && performance.now() - it.seekAt > 5000) { it.seeking = false; it.seekAt = 0; it.target = null; }   // never reported back
    if (playing) {
      if (it.seeking || v.seeking) {
        // let it land; only a real jump of the playhead (a click while playing) is worth starting over
        if (it.target !== null && Math.abs(it.target - mediaTime) > 3) this.jump(it, mediaTime);
        if (v.paused) v.play().catch(() => {});
        return it;
      }
      const drift = v.currentTime - mediaTime;
      if (drift < -BEHIND_SEEK || drift > AHEAD_SEEK) {
        this.jump(it, mediaTime);
        v.playbackRate = 1;
        if (v.paused) v.play().catch(() => {});
        return it;
      }
      if (drift > 3 / FPS) { if (!v.paused) v.pause(); return it; }     // ahead (a seek landed early): wait for the clock
      v.playbackRate = drift < -1 / FPS ? 1 + Math.min(0.5, Math.max(0.1, -drift * 2)) : drift > 1 / FPS ? 0.9 : 1;
      if (v.paused) v.play().catch(() => {});
    } else {
      if (!v.paused) v.pause();
      if (Math.abs(v.currentTime - mediaTime) > 0.5 / FPS || it.seeking) this.seek(it, mediaTime);
    }
    if (!it.seeking && !v.seeking && v.readyState >= 2 && Math.abs(v.currentTime - mediaTime) < 0.5) it.picKey = key;
    return it;
  }

  // pre-seek an element for a clip about to start
  prepare(key, url, mediaTime) {
    const it = this.acquire(key, url, false);
    if (!it || !it.v.paused) return it;
    if (Math.abs(it.v.currentTime - mediaTime) > 0.5 / FPS) this.seek(it, mediaTime);
    return it;
  }

  // copy the element's picture before it seeks or changes file; the copy stands in until it has a new one
  snapshot(it) {
    const v = it.v;
    if (v.readyState < 2 || v.seeking || !v.videoWidth) return;
    const k = Math.min(1, SNAP_MAX / Math.max(v.videoWidth, v.videoHeight));
    const w = Math.round(v.videoWidth * k), h = Math.round(v.videoHeight * k);
    if (!it.snap) it.snap = document.createElement("canvas");
    if (it.snap.width !== w || it.snap.height !== h) { it.snap.width = w; it.snap.height = h; }
    it.snap.getContext("2d", { alpha: false }).drawImage(v, 0, 0, w, h);
    it.snapKey = it.picKey;        // whose picture it is: an element just handed to another clip still shows the old one
  }

  // what the monitor draws for this element: the video, else the copy of its last picture, else nothing yet
  picture(it) {
    if (!it) return null;
    if (this.live(it)) return it.v;
    if (it.snap && it.snapKey === it.key) return it.snap;
    return null;
  }

  live(it) { return it.v.readyState >= 2 && !it.v.seeking; }

  beginFrame() { this.stamp += 1; }
  endFrame() {
    for (const it of this.items) if (it.used < this.stamp && !it.v.paused) it.v.pause();
  }

  ready(it) { return it && it.v.readyState >= 2 && !it.seeking; }
  drawable(it) { return it && it.v.readyState >= 2; }
  pauseAll() { for (const it of this.items) it.v.pause(); }
}
