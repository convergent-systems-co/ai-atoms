// llms.txt (llmstxt.org convention): a short, plain-text map of the site for language models.
import type { APIRoute } from "astro";
import catalog from "../../public/exports/catalog.json";

const counts = (catalog as any).counts as Record<string, number>;
const categories = Object.keys((catalog as any).categories as Record<string, unknown>);

export const GET: APIRoute = () => {
  const body = `# ai-atoms

> A typed, versioned catalog of AI runtime primitives: skills, hooks, prompts, agents, personas, and models. Every atom is static JSON, validated against its class schema, with a category from one shared vocabulary and the provenance of where it came from.

Catalog v${catalog.version}, ${(catalog.atoms as any[]).length} atoms: ${Object.entries(counts).map(([k, v]) => `${v} ${k}s`).join(", ")}.

## Start here
- [Machine index](https://ai-atoms.com/ai/index.json): classes, counts, categories, every atom id, endpoint and schema URLs
- [Instructions for AI agents](https://ai-atoms.com/ai/instructions.md): how to discover, query, and use each class
- [Whole catalog](https://ai-atoms.com/exports/catalog.json): every atom inline

## Endpoints
- One atom: https://ai-atoms.com/atoms/{class}/{slug}.json — slug is the id without its class prefix
- One category: https://ai-atoms.com/categories/{category}.json — ids grouped by class
- Schemas: https://ai-atoms.com/schemas/{class}-v1.json and https://ai-atoms.com/schemas/common-v1.json

## Classes
${Object.keys(counts).map((c) => `- [${c}](https://ai-atoms.com/atoms/${c}/): ${counts[c]} atoms`).join("\n")}

## Categories
${categories.map((c) => `- [${c}](https://ai-atoms.com/categories/${c}.json)`).join("\n")}

## Attribution
Check provenance.license before redistributing. "unknown" means the source stated no license. Code Apache-2.0; catalog data CC-BY-4.0; imported content keeps its source's terms.
`;
  return new Response(body, { headers: { "Content-Type": "text/plain; charset=utf-8" } });
};
