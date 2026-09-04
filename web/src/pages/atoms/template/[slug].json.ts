// Machine-readable endpoint: GET /atoms/template/<slug>.json returns the atom verbatim.
import type { APIRoute } from "astro";
import catalog from "../../../../public/exports/catalog.json";

const CLASS = "template";

export function getStaticPaths() {
  return (catalog.atoms as any[])
    .filter((a: any) => a.type === CLASS)
    .map((a: any) => ({ params: { slug: a.id.replace(`${CLASS}/`, "") }, props: { atom: a } }));
}

export const GET: APIRoute = ({ props }) => {
  return new Response(JSON.stringify(props.atom, null, 2), {
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
};
