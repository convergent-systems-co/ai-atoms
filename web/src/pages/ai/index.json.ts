import type { APIRoute } from "astro";
import catalog from "../../../public/exports/catalog.json";
const skills = (catalog.atoms as any[]).filter(a => a.type === "skill");
const hooks = (catalog.atoms as any[]).filter(a => a.type === "hook");
export const GET: APIRoute = () => {
  const body = JSON.stringify({
    instructions: "https://ai-atoms.com/ai/instructions.md",
    version: "1",
    site: "https://ai-atoms.com",
    description: "AI runtime primitives — hooks and skills for AI agents and agentic pipelines.",
    catalog: {
      skills: skills.map(s => s.id),
      hooks: hooks.map(h => h.id),
    },
    endpoints: {
      skill: "https://ai-atoms.com/atoms/skill/{id}.json",
      hook: "https://ai-atoms.com/atoms/hook/{id}.json",
    },
    workflow: [
      "1. Read this index to discover available skills and hooks",
      "2. Fetch a specific skill: GET /atoms/skill/<slug>.json",
      "3. Read system_prompt_fragment to understand invocation",
      "4. Fetch a hook: GET /atoms/hook/<slug>.json",
      "5. Read trigger.event and trigger.pattern to understand when it fires"
    ],
  }, null, 2);
  return new Response(body, { headers: { "Content-Type": "application/json" } });
};
