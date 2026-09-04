// Shared catalog helpers so class metadata, categories, and selection rules live in one place.
import catalog from "../../public/exports/catalog.json";

export const CLASSES: string[] = (catalog as any).classes;
export const COUNTS: Record<string, number> = (catalog as any).counts;
export const CATEGORY_INDEX: Record<string, Record<string, number>> = (catalog as any).categories;
export const ATOMS: any[] = catalog.atoms as any[];
export const CATALOG_VERSION: string = catalog.version;
export const BUILT_AT: string = (catalog as any).built_at;
export const BY_ID = new Map<string, any>(ATOMS.map((a) => [a.id, a]));

export interface ClassMeta { symbol: string; label: string; plural: string; blurb: string; install: (slug: string) => string | undefined; facet: "subtype" | "task" | "event" | null }
export const CLASS_META: Record<string, ClassMeta> = {
  skill:   { symbol: "Sk", label: "Skill",   plural: "Skills",   blurb: "Bounded capability with a system-prompt fragment. Drop into .claude/skills/.", install: (s) => `ai skills install ${s}`, facet: null },
  hook:    { symbol: "Hk", label: "Hook",    plural: "Hooks",    blurb: "Fires on a runtime event. Script ships inline; blocking or advisory.", install: (s) => `ai hooks install ${s}`, facet: "event" },
  prompt:  { symbol: "Pr", label: "Prompt",  plural: "Prompts",  blurb: "Typed text injected into the context window: constraint, format, refusal, persona.", install: () => undefined, facet: "subtype" },
  agent:   { symbol: "Ag", label: "Agent",   plural: "Agents",   blurb: "A persona bound to the prompts, skills, tools, policies, and hooks it runs with.", install: () => undefined, facet: "subtype" },
  persona: { symbol: "Pe", label: "Persona", plural: "Personas", blurb: "A portable identity: role, voice, tone, work contract, constraints, boundaries.", install: () => undefined, facet: null },
  model:   { symbol: "Mo", label: "Model",   plural: "Models",   blurb: "Reference data about a model and the providers a runtime can get it from.", install: () => undefined, facet: "task" },
  policy:  { symbol: "Po", label: "Policy",  plural: "Policies", blurb: "A rule a runtime permits, forbids, or bounds an agent by: boundary, capability, isolation.", install: () => undefined, facet: "subtype" },
  tool:    { symbol: "To", label: "Tool",    plural: "Tools",    blurb: "An executable affordance: the function the model sees and the side effects to gate.", install: () => undefined, facet: "subtype" },
};

export const CATEGORY_LABEL: Record<string, string> = {
  coding: "Engineering & Coding", frontend: "Frontend & Web", backend: "Backend & APIs", devops: "DevOps & Cloud",
  security: "Security", testing: "Testing & Quality", dotnet: ".NET / Microsoft", data: "Data & Analytics", ai: "AI & Models",
  design: "Design & UX", product: "Product & Delivery", operations: "Operations & IT", finance: "Finance & Accounting",
  legal: "Legal & Compliance", sales: "Sales & CRM", marketing: "Marketing & Content", hr: "People & HR",
  support: "Customer Support", knowledge: "Knowledge & Docs", research: "Research & Science", governance: "Governance & Meta", other: "Other",
};

export function atomsOf(cls: string): any[] {
  return ATOMS.filter((a) => a.type === cls).sort((a, b) => (a.name ?? a.id).localeCompare(b.name ?? b.id));
}
export function slugOf(id: string): string { return id.slice(id.indexOf("/") + 1); }
export function hrefOf(id: string): string { return `/atoms/${id.split("/")[0]}/${slugOf(id)}/`; }
export function classOf(a: any): string { return a.type; }
export function facetOf(a: any): string | undefined {
  const f = CLASS_META[a.type]?.facet;
  if (!f) return undefined;
  return f === "event" ? (a.event || "library") : a[f];
}
export function sourceOf(a: any): string { return a.provenance?.source ?? (a.authored_by === "convergent-systems-key" ? "ai-atoms" : "authored"); }
export function licenseOf(a: any): string { return a.provenance?.license ?? "catalog"; }

export function count<T>(items: T[], key: (t: T) => string | undefined): Record<string, number> {
  const out: Record<string, number> = {};
  for (const it of items) { const k = key(it); if (k) out[k] = (out[k] ?? 0) + 1; }
  return out;
}
export function searchText(a: any): string {
  return [a.id, a.name, a.description, ...(a.tags ?? []), ...(a.applicable_domains ?? []), a.subtype, a.vendor, a.family, a.task, a.event, a.category, sourceOf(a)]
    .filter(Boolean).join(" ").toLowerCase();
}

/** Atoms good enough to be "of the day": stable or reviewed, described, and not license-unknown. */
export function specimenCandidates(cls: string, limit = 90): any[] {
  // Models record the weights license as unknown because providers do not publish it;
  // that is not a reason to hide them. Skills with unknown license are aggregator imports.
  const pool = atomsOf(cls).filter((a) =>
    (a.description?.length ?? 0) > 50 &&
    (cls === "model" || licenseOf(a) !== "unknown") &&
    a.lifecycle !== "deprecated" &&
    (cls !== "skill" || a.lifecycle === "stable") &&
    (a.category ?? "other") !== "other" &&
    !/^\[retired/i.test(a.description ?? ""));
  // Stable pseudo-random order so the daily rotation does not walk alphabetically.
  const hash = (s: string) => { let h = 2166136261; for (const ch of s) { h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619) >>> 0; } return h; };
  return pool.sort((a, b) => hash(a.id) - hash(b.id)).slice(0, limit);
}
/** Days since 1970-01-01 UTC; the same function runs at build time and in the browser. */
export function dayNumber(d = new Date()): number { return Math.floor(d.getTime() / 86400000); }
