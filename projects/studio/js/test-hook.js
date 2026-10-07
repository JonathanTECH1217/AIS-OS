// window.__studio: the test hook (the Dictation Sheet's window.__ds convention). Tests in projects/studio/tests
// drive the editor through it and print PASS / FAIL lines into <pre id="__out">.
import { S, emit, selectOnly } from "./store.js";
import * as history from "./history.js";
import * as ops from "./model/ops.js";
import * as kf from "./model/keyframes.js";
import * as doc from "./model/doc.js";
import * as captions from "./model/captions.js";
import * as voices from "./model/voices.js";
import * as trailer from "./model/trailer.js";
import { all, get, run, openShort } from "./actions.js";
import { keyMap, comboOf } from "./keys.js";
import { lib } from "./media/library.js";
import { audio } from "./media/audio.js";
import { pb } from "./playback.js";
import { timelineApi } from "./timeline/timeline.js";
import { monitorApi } from "./panels/monitor.js";
import { layersAt, transformOf, renderFrame } from "./compositor.js";
import { api } from "./api.js";
import * as save from "./save.js";
import { layoutSizes, resetLayout } from "./components/split.js";
import { browseApi } from "./panels/browse.js";

export function installHook() {
  window.__studio = {
    S, emit, selectOnly, history, ops, kf, doc, captions, voices, trailer, actions: { all, get, run }, openShort, keys: { map: keyMap, comboOf },
    lib, audio, pb, tl: timelineApi(), mon: monitorApi(), comp: { layersAt, transformOf, renderFrame }, api, save,
    layout: { sizes: layoutSizes, reset: resetLayout }, browse: browseApi(),
    ready: true,
  };
}
