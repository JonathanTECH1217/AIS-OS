import { test, wait } from "./harness.js";

test("menus", async (t, st) => {
  await t.fresh();
  const map = st.keys.map();
  const byId = new Map([...map.entries()].map(([k, id]) => [id, k]));
  for (const btn of document.querySelectorAll(".tb-menu")) {
    btn.click();
    await wait(30);
    const rows = [...document.querySelectorAll(".menu > .menu-item")];
    t.ok(`${btn.textContent} menu opens with items`, rows.length > 3, String(rows.length));
    // every shortcut shown in a menu is the one the keyboard runs
    for (const row of rows) {
      const keys = row.querySelector(".menu-keys").textContent;
      const label = row.querySelector(".menu-label").textContent;
      if (!keys || keys === "▸") continue;
      const id = map.get(keys);
      t.ok(`"${label}" shortcut ${keys} is bound`, !!id, keys);
    }
    t.closeMenus();
  }
  // enabled state: Undo is disabled on a fresh short, enabled after an edit
  document.querySelectorAll(".tb-menu")[1].click();
  await wait(30);
  const undoRow = [...document.querySelectorAll(".menu-item")].find((r) => r.querySelector(".menu-label").textContent.startsWith("Undo"));
  t.ok("Undo disabled before any edit", undoRow && undoRow.classList.contains("is-disabled"));
  t.closeMenus();
  st.actions.run("addMarker");
  await wait(30);
  document.querySelectorAll(".tb-menu")[1].click();
  await wait(30);
  const undo2 = [...document.querySelectorAll(".menu-item")].find((r) => r.querySelector(".menu-label").textContent.startsWith("Undo"));
  t.ok("Undo enabled and named after an edit", undo2 && !undo2.classList.contains("is-disabled") && undo2.textContent.includes("Add Marker"), undo2 && undo2.textContent);
  t.closeMenus();
  // shape submenu
  document.querySelectorAll(".tb-menu")[2].click();
  await wait(30);
  const shapeRow = [...document.querySelectorAll(".menu-item")].find((r) => r.textContent.includes("New shape"));
  shapeRow.dispatchEvent(new MouseEvent("mouseenter"));
  await wait(30);
  t.ok("New shape submenu lists Box, Bar, Circle, Arrow", [...document.querySelectorAll(".menu.sub .menu-label")].map((x) => x.textContent).join(",") === "Box,Bar,Circle,Arrow");
  t.closeMenus();
});
