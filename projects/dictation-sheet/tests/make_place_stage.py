"""Experiment copy: stage.html -> place-stage.html with step 6 of autoPlaceWords changed so that a timed line that
starts inside a bar the line before still uses JOINS that line at its true slots (instead of waiting for the next
barline and being packed as sixteenths). Nothing outside the scratchpad is touched."""
import os

SP = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(SP, "stage.html"), encoding="utf-8").read()
old = """    var prev = null, between = 0, squeezed = 0;
    s.lines.forEach(function (line, li) {
      if (line.kind !== 'line') return;
      var rec = placed[li];
      if (!rec) { line.bars = minBars(line, spb); between += line.bars; return; }
      var startBar = Math.floor(rec.q[0].slot / spb), ord = between;
      if (prev) {
        var want = startBar - prev.ord - between;
        if (want >= 1) trimAtBar(prev.line, want * spb);
        prev.line.bars = Math.max(1, minBars(prev.line, spb), want);
        ord = prev.ord + lineBars(prev.line, spb) + between;
      }
      if (ord > startBar) squeezed++;
      // gaps draw as rests by themselves, so old rest syllables go
      for (var r = line.syllables.length - 1; r >= 0; r--) if (line.syllables[r].rest) line.syllables.splice(r, 1);
      var base = ord * spb, poss = [], c = 0, n = rec.q.length;
      rec.q.forEach(function (e) { var pos = Math.max(c, e.slot - base); poss.push(pos); c = pos + 1; });
      rec.q.forEach(function (e, i) {
        var y = rec.syls[i], room = i + 1 < n ? poss[i + 1] - poss[i] : MAX_SLOTS, len = Math.min(e.lenSlots, room);
        if (i + 1 < n && room - len === 1) len = room;
        y.pos = poss[i]; y.rest = false; setSlotsRaw(y, Math.max(1, len));
      });
      rec.ord = ord; prev = rec; between = 0;
    });
    if (prev) prev.line.bars = Math.max(1, minBars(prev.line, spb));
"""
new = """    var prev = null, between = 0, squeezed = 0, merged = [];
    s.lines.forEach(function (line, li) {
      if (line.kind !== 'line') return;
      var rec = placed[li];
      if (!rec) { line.bars = minBars(line, spb); between += line.bars; return; }
      var startBar = Math.floor(rec.q[0].slot / spb), ord = between;
      if (prev) {
        var want = startBar - prev.ord - between;
        if (want >= 1) trimAtBar(prev.line, want * spb);
        prev.line.bars = Math.max(1, minBars(prev.line, spb), want);
        ord = prev.ord + lineBars(prev.line, spb) + between;
      }
      for (var r = line.syllables.length - 1; r >= 0; r--) if (line.syllables[r].rest) line.syllables.splice(r, 1);
      // EXPERIMENT: a line that starts inside a bar the line before still uses joins that line at its true slots
      var target = line, base = ord * spb, c = 0;
      if (prev && ord > startBar && between === 0) { squeezed++; target = prev.line; base = prev.ord * spb; target.syllables.forEach(function (y) { c = Math.max(c, y.pos + lenSlots(y)); }); merged.push(li); }
      var poss = [], n = rec.q.length;
      rec.q.forEach(function (e) { var pos = Math.max(c, e.slot - base); poss.push(pos); c = pos + 1; });
      rec.q.forEach(function (e, i) {
        var y = rec.syls[i], room = i + 1 < n ? poss[i + 1] - poss[i] : MAX_SLOTS, len = Math.min(e.lenSlots, room);
        if (i + 1 < n && room - len === 1) len = room;
        y.pos = poss[i]; y.rest = false; setSlotsRaw(y, Math.max(1, len));
        if (target !== line) target.syllables.push(y);
      });
      if (target !== line) { target.bars = Math.max(1, minBars(target, spb)); return; }
      rec.ord = ord; prev = rec; between = 0;
    });
    if (prev) prev.line.bars = Math.max(1, minBars(prev.line, spb));
    for (var mi = merged.length - 1; mi >= 0; mi--) s.lines.splice(merged[mi], 1);
"""
assert src.count(old) == 1, "step 6 block not found exactly once: %d" % src.count(old)
open(os.path.join(SP, "place-stage.html"), "w", encoding="utf-8").write(src.replace(old, new))
print("wrote place-stage.html")
