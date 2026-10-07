var d = window.__ds, s = d.S();
s.time = '4/4'; s.view = 'vocals'; s.lines = d.normalize({ lines: [{ kind: 'line', bars: 2, syllables: [{ text: 'one', pos: 0 }, { text: 'two', pos: 4 }, { text: 'three', pos: 16 }, { text: 'four', pos: 28 }] }, { kind: 'line', bars: 1, syllables: [{ text: 'five', pos: 0 }] }] }).lines;
[200, 100].forEach(function (z) {
  d.state.prefs.zoom = z; d.renderAll();
  var sy = d.editor.systems.filter(function (o) { return o.geo; });
  sy.forEach(function (o, si) {
    var svg = o.el ? o.el.querySelector('svg') : null;
    console.log('zoom ' + z + ' system ' + si + ' cells: ' + o.geo.cells.map(function (c, k) { var nx = o.geo.cells[k + 1]; return 'bar' + (c.b + 1) + '[' + c.x0.toFixed(1) + '..' + c.x1.toFixed(1) + ' w ' + (c.x1 - c.x0).toFixed(1) + (nx ? ' gap ' + (nx.x0 - c.x1).toFixed(1) : '') + ']'; }).join(' '));
  });
  var heads = Array.prototype.slice.call(document.querySelectorAll('#work svg .vf-notehead path, #work svg path')).map(function (p) { try { var b = p.getBBox(); return b; } catch (e) { return null; } }).filter(function (b) { return b && b.width > 6 && b.width < 14 && b.height > 4 && b.height < 12; }).map(function (b) { return b.x.toFixed(1); });
  console.log('zoom ' + z + ' head-like glyph left edges: ' + heads.slice(0, 12).join(' '));
});
