// Keyboard: Premiere's defaults (G4), each key mapped to an action. While typing in a field only Ctrl+S and
// Ctrl+M go through; Ctrl+Z there is the field's own undo.
import { inField } from "./util.js";
import { menuOpen } from "./components/menu.js";
import { all, run } from "./actions.js";
import { browseKey } from "./panels/browse.js";

const alias = { " ": "Space", ArrowLeft: "Left", ArrowRight: "Right", ArrowUp: "Up", ArrowDown: "Down", Delete: "Delete", Backspace: "Backspace", Escape: "Escape" };

export function comboOf(e) {
  let k = alias[e.key] || (e.key.length === 1 ? e.key.toUpperCase() : e.key);
  if (k === "+") k = "=";
  if (k === "_") k = "-";
  if (k === "|") k = "\\";
  if (k === ":") k = ";";
  if (k === '"') k = "'";
  const mods = [];
  if (e.ctrlKey || e.metaKey) mods.push("Ctrl");
  if (e.shiftKey && !(k === "?" )) mods.push("Shift");
  if (e.altKey) mods.push("Alt");
  return [...mods, k].join("+");
}

let map = null;
export function keyMap() {
  if (map) return map;
  map = new Map();
  for (const a of all()) {
    if (!a.keys) continue;
    map.set(a.keys, a.id);
  }
  // Premiere extras
  map.set("Backspace", "clear");
  map.set("Ctrl+Y", "redo");
  map.set("Shift+Backspace", "rippleDelete");
  return map;
}

export function initKeys() {
  document.addEventListener("keydown", (e) => {
    if (document.body.classList.contains("modal-open") || menuOpen()) return;
    const combo = comboOf(e);
    if (inField(e)) {
      if (combo === "Ctrl+S" || combo === "Ctrl+M") { e.preventDefault(); run(keyMap().get(combo)); }
      return;
    }
    // a recording's calls view with focus takes Space, Up, Down, I and O (2026-10-01); preventDefault so Space never
    // also clicks a focused button there
    if (browseKey(e, combo)) { e.preventDefault(); e.stopPropagation(); return; }
    if (e.key === "Alt") { e.preventDefault(); return; }
    const id = keyMap().get(combo);
    if (!id) return;
    e.preventDefault();
    e.stopPropagation();
    run(id);
  });
}
