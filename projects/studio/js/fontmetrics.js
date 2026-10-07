// TTF metrics for the caption font, so the canvas draws captions at the size libass burns them.
// libass mimics GDI: it sets the face's ascender/descender from OS/2 winAscent/winDescent and asks FreeType for a
// "real dimension" size, so the line box (winAscent + winDescent) equals the ASS font size. One function owns that
// rule (assEmPx); scripts/studio_captions.py reads the same table.
let M = null;

export async function loadFontMetrics(url) {
  const buf = await (await fetch(url)).arrayBuffer();
  const dv = new DataView(buf);
  const n = dv.getUint16(4);
  const tables = {};
  for (let i = 0; i < n; i += 1) {
    const o = 12 + i * 16;
    const tag = String.fromCharCode(dv.getUint8(o), dv.getUint8(o + 1), dv.getUint8(o + 2), dv.getUint8(o + 3));
    tables[tag] = dv.getUint32(o + 8);
  }
  const upm = dv.getUint16(tables.head + 18);
  let asc, desc;
  if (tables["OS/2"] !== undefined) {
    asc = dv.getUint16(tables["OS/2"] + 74);
    desc = dv.getUint16(tables["OS/2"] + 76);
  } else {
    asc = dv.getInt16(tables.hhea + 4);
    desc = -dv.getInt16(tables.hhea + 6);
  }
  M = { upm, asc, desc };
  return M;
}

export function metrics() { return M || { upm: 1000, asc: 968, desc: 251 }; }

// font-size in canvas px for an ASS Fontsize (PlayRes px)
export function assEmPx(size) { const m = metrics(); return (size * m.upm) / (m.asc + m.desc); }

// baseline offset from the vertical center of an \an5 line of this size
export function baselineFromCenter(size) {
  const m = metrics();
  const em = assEmPx(size);
  return -size / 2 + (m.asc / m.upm) * em;
}
