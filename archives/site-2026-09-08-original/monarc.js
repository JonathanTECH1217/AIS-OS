(function () {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    document.querySelectorAll(".mb-reveal").forEach(function (el) { el.classList.add("is-in"); });
    return;
  }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) { e.target.classList.toggle("is-in", e.isIntersecting); });
  }, { threshold: 0.3 });
  document.querySelectorAll(".mb-reveal").forEach(function (el) { io.observe(el); });
  var mq = window.matchMedia("(min-width: 1024px)");
  var el = document.querySelector(".mb-snap");
  if (!el) return;
  var animating = false;
  function cardTops() {
    var base = el.getBoundingClientRect().top;
    return Array.prototype.map.call(el.querySelectorAll(":scope > .mb-card"), function (c) {
      return c.getBoundingClientRect().top - base + el.scrollTop;
    });
  }
  function nearest(tops) {
    var best = 0;
    tops.forEach(function (tp, i) {
      if (Math.abs(tp - el.scrollTop) < Math.abs(tops[best] - el.scrollTop)) best = i;
    });
    return best;
  }
  function ease(x) { return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; }
  function animateTo(top) {
    animating = true;
    var start = el.scrollTop, dist = top - start, dur = 1200, t0 = performance.now();
    function step(now) {
      var p = Math.min(1, (now - t0) / dur);
      el.scrollTop = start + dist * ease(p);
      if (p < 1) requestAnimationFrame(step);
      else setTimeout(function () { animating = false; }, 160);
    }
    requestAnimationFrame(step);
  }
  el.style.scrollSnapType = "none";
  el.addEventListener("wheel", function (e) {
    if (!mq.matches) return;
    e.preventDefault();
    if (animating || Math.abs(e.deltaY) < 8) return;
    var tops = cardTops();
    var i = nearest(tops);
    var next = Math.max(0, Math.min(tops.length - 1, i + (e.deltaY > 0 ? 1 : -1)));
    if (next === i && Math.abs(tops[i] - el.scrollTop) < 4) return;
    animateTo(tops[next]);
  }, { passive: false });
})();
