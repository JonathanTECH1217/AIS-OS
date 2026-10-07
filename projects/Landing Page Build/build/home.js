/* The homepage's search bar (Jonathan, 2026-09-26 Q4 and 2026-09-27 Q31): it types "marketing for contractors" once, then
   holds with the caret. Still on file: renders, on ?static=1, under reduced motion, and on the sent state. */
(function(){
  var q = document.getElementById('q');
  var still = location.protocol === 'file:' || /[?&](static|sent)=1/.test(location.search) ||
              !(window.matchMedia && matchMedia('(prefers-reduced-motion: no-preference)').matches);
  if (still || !q) return;
  var text = q.textContent, n = 0;
  q.textContent = '';
  function type(){
    n++; q.textContent = text.slice(0, n);
    if (n < text.length) setTimeout(type, 60);
  }
  setTimeout(type, 500);
})();
