import type { APIRoute } from "astro";
import catalog from "../../public/exports/catalog.json";

const SITE = "https://ai-atoms.com";
export const GET: APIRoute = () => {
  const urls = [
    "/", "/start/", "/categories/", "/builder/",
    ...((catalog as any).classes as string[]).map((c) => `/atoms/${c}/`),
    ...Object.keys((catalog as any).categories).map((c) => `/categories/${c}/`),
    ...(catalog.atoms as any[]).map((a) => `/atoms/${a.type}/${a.id.slice(a.type.length + 1)}/`),
  ];
  const body = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.map((u) => `  <url><loc>${SITE}${u}</loc></url>`).join("\n")}\n</urlset>\n`;
  return new Response(body, { headers: { "Content-Type": "application/xml; charset=utf-8" } });
};
