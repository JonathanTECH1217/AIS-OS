// Hash router. "#/companies/rec123" -> route "companies", params ["rec123"]. Today is the first screen (2026-09-23).
const routes = new Map();

export function route(name, render) { routes.set(name, render); }

export function navigate(hash) { location.hash = hash.startsWith("#") ? hash : "#" + hash; }

export function current() {
  const parts = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean);
  return { name: parts[0] || "today", params: parts.slice(1).map(decodeURIComponent) };
}

// Which rail item lights up for a route: a channel workspace belongs to Channels, old Home links go to Today, and the
// old Ads screen now opens the Google Ads channel page (2026-09-29).
const HIGHLIGHT = { channel: "channels", lead: "channels", home: "today", ads: "channels" };

// Draw the current page again in place, keeping the scroll position (after a save or an edit).
export function rerender() { window.dispatchEvent(new HashChangeEvent("hashchange")); }

let lastHash = null;

export function start(root, onChange) {
  async function go() {
    const { name, params } = current();
    const render = routes.get(name) || routes.get("today");
    const lit = HIGHLIGHT[name] || name;
    document.querySelectorAll("#nav a").forEach((a) => a.classList.toggle("is-active", a.dataset.route === lit));
    // The same page drawn again (an edit, a save) keeps its place (Jonathan, 2026-09-29: deleting a headline threw him
    // to the top). Hold the height while it redraws so the window cannot scroll up, then put the scroll back.
    const same = location.hash === lastHash;
    const y = window.scrollY;
    if (same) root.style.minHeight = `${root.offsetHeight}px`;
    root.replaceChildren();
    try {
      await render(root, params);
    } catch (e) {
      root.replaceChildren();
      const p = document.createElement("div");
      p.className = "empty";
      p.textContent = (e && e.errors && e.errors.join(" ")) || String(e);
      root.append(p);
    }
    if (same) {
      root.style.minHeight = "";
      window.scrollTo(0, y);
    }
    lastHash = location.hash;
    if (onChange) onChange(name);
  }
  window.addEventListener("hashchange", go);
  return go();
}
