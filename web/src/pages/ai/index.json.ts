import type { APIRoute } from "astro";
import catalog from "../../../public/exports/catalog.json";

// One entry per typed atom class, in catalog order. The catalog build is the
// source of truth for which classes and categories exist; this file only shapes the index.
const CLASSES = (catalog as any).classes as string[];
const CATEGORIES = (catalog as any).categories as Record<string, Record<string, number>>;
const idsByClass = Object.fromEntries(
  CLASSES.map(cls => [cls, (catalog.atoms as any[]).filter(a => a.type === cls).map(a => a.id)])
);
const PLURAL: Record<string, string> = { skill: "skills", hook: "hooks", prompt: "prompts", agent: "agents", persona: "personas", model: "models", policy: "policies", tool: "tools", template: "templates", bundle: "bundles" };

export const GET: APIRoute = () => {
  const body = JSON.stringify({
    instructions: "https://ai-atoms.com/ai/instructions.md",
    version: "3",
    site: "https://ai-atoms.com",
    catalog_version: catalog.version,
    built_at: (catalog as any).built_at,
    description: "AI runtime primitives — skills, hooks, prompts, agents, personas, models, policies, tools, templates, and bundles for AI agents and agentic pipelines.",
    classes: CLASSES,
    counts: (catalog as any).counts,
    categories: CATEGORIES,
    catalog: Object.fromEntries(CLASSES.map(cls => [PLURAL[cls] ?? cls, idsByClass[cls]])),
    endpoints: {
      ...Object.fromEntries(CLASSES.map(cls => [cls, `https://ai-atoms.com/atoms/${cls}/{slug}.json`])),
      category: "https://ai-atoms.com/categories/{category}.json",
      catalog: "https://ai-atoms.com/exports/catalog.json",
    },
    schemas: {
      ...Object.fromEntries(CLASSES.map(cls => [cls, `https://ai-atoms.com/schemas/${cls}-v1.json`])),
      common: "https://ai-atoms.com/schemas/common-v1.json",
    },
    workflow: [
      "1. Read this index: classes, per-category counts, and every atom id",
      "2. Query a category: GET /categories/<category>.json returns ids grouped by class",
      "3. Resolve one atom: GET /atoms/<class>/<slug>.json (slug is the id without its class prefix)",
      "4. skill: inject system_prompt_fragment; hook: wire by event/trigger and install `script`; prompt: inject content into applicable_turns",
      "5. persona: render role, voice, tone, constraints, and knowledge_boundaries into the system turn",
      "6. agent: resolve persona, prompts, skills, tools, policies, and hooks by id, then run with the execution preferences",
      "7. model: pick a providers[] entry and call it by model_id, or run pull_command locally",
      "7a. policy: enforce rule.text; capability grants/elevation gate tool calls; isolation fields configure the sandbox",
      "7b. tool: hand spec (function_name, parameters, returns) to the model; gate spec.side_effects with a capability policy",
      "7c. template: render body by replacing each {{placeholder}} per the placeholders list; apply rules; example shows the finished form",
      "7d. bundle: read entry_point, then write every files[].content to files[].path under a directory named for the slug — never resolve a path it does not ship",
      "8. Check provenance.license before redistributing: 'unknown' means the source stated none",
      "9. Whole catalog with every atom inline: GET /exports/catalog.json"
    ],
  }, null, 2);
  return new Response(body, { headers: { "Content-Type": "application/json" } });
};
