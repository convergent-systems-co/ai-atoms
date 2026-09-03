// Compact index for the site's search palette: one small record per atom.
import type { APIRoute } from "astro";
import catalog from "../../public/exports/catalog.json";

export const GET: APIRoute = () => {
  const rows = (catalog.atoms as any[]).map((a) => ({
    id: a.id, n: a.name, d: (a.description ?? "").slice(0, 140), c: a.type, k: a.category ?? "other",
    s: [a.subtype, a.task, a.vendor, a.event, ...(a.tags ?? []).slice(0, 4)].filter(Boolean).join(" "),
  }));
  return new Response(JSON.stringify(rows), { headers: { "Content-Type": "application/json; charset=utf-8" } });
};
