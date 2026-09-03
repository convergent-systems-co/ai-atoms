// GET /categories/<slug>.json — every atom id in a category, grouped by class.
import type { APIRoute } from "astro";
import catalog from "../../../public/exports/catalog.json";

const index = (catalog as any).categories as Record<string, Record<string, number>>;

export function getStaticPaths() {
  return Object.keys(index).map((slug) => ({ params: { slug } }));
}

export const GET: APIRoute = ({ params }) => {
  const atoms = (catalog.atoms as any[]).filter((a) => (a.category ?? "other") === params.slug);
  const grouped: Record<string, string[]> = {};
  for (const a of atoms) (grouped[a.type] ??= []).push(a.id);
  const body = JSON.stringify({
    category: params.slug,
    counts: index[params.slug!],
    atoms: grouped,
    endpoint: "https://ai-atoms.com/atoms/{class}/{slug}.json",
  }, null, 2);
  return new Response(body, { headers: { "Content-Type": "application/json; charset=utf-8" } });
};
