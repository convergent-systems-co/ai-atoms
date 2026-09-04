#!/usr/bin/env python3
"""Fold model-atoms.com's Cloudflare Workers AI model cards into the model class.

model-atoms.com publishes one card per model hosted on Cloudflare Workers AI. Each
card becomes a Cloudflare provider entry. The provider id's last segment is reduced
to a model name by stripping size, quantisation, and variant tokens
("llama-3.2-11b-vision-instruct" -> "llama3.2vision"); when that equals the
normalised name of an existing Ollama-sourced atom, the provider is appended to
that atom — the same weights, another place to get them. Otherwise a new atom is
created under the provider id's last segment. Matching is exact; nothing is merged
on a guess, so a distilled or generational variant becomes its own atom.

Usage: python3 scripts/import-cloudflare-models.py [--dry-run] [--from-file catalog.json]
"""
import json
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MODELS = REPO / "atoms" / "model"
CATALOG_URL = "https://model-atoms.com/exports/catalog.json"
DOCS_URL = "https://developers.cloudflare.com/workers-ai/models/"
TODAY = date.today().isoformat()
DRY_RUN = "--dry-run" in sys.argv
PROVIDER = "Cloudflare Workers AI"
TASK = {"text-generation": "text-generation", "code-generation": "code-generation", "reasoning": "reasoning", "embedding": "embedding",
        "image-generation": "image-generation", "speech-to-text": "speech-to-text", "text-to-speech": "text-to-speech", "multimodal": "multimodal",
        "translation": "translation", "reranking": "reranking", "image-classification": "vision", "object-detection": "vision",
        "image-to-text": "multimodal", "summarization": "text-generation", "text-classification": "other"}


def normalise(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


VARIANT_TOKENS = {"instruct", "it", "chat", "hf", "fp8", "fp16", "int8", "awq", "fast", "lora", "base", "meta"}
SIZE_TOKEN = re.compile(r"^(\d+(\.\d+)?[bm]|a\d+b|\d+e|\d+x\d+b)$")


def model_name_of(provider_id: str) -> str:
    """'@cf/meta/llama-3.2-11b-vision-instruct' -> 'llama32vision'."""
    slug = provider_id.split("/")[-1].lower()
    kept = [t for t in slug.split("-") if t not in VARIANT_TOKENS and not SIZE_TOKEN.match(t)]
    return normalise("-".join(kept))


def load_cards() -> list[dict]:
    if "--from-file" in sys.argv:
        data = json.loads(Path(sys.argv[sys.argv.index("--from-file") + 1]).read_text())
    else:
        with urllib.request.urlopen(CATALOG_URL, timeout=30) as r:
            data = json.loads(r.read())
    return [a for a in data["atoms"] if a["type"] == "model-card"]


def provider_entry(card: dict) -> dict:
    slug = card["provider_id"].split("/")[-1]
    return {"name": PROVIDER, "model_id": card["provider_id"], "url": f"{DOCS_URL}{slug}/"}


def new_atom(card: dict) -> dict:
    slug = card["provider_id"].split("/")[-1].lower()
    slug = re.sub(r"[^a-z0-9.-]", "-", slug)
    return {
        "schema": "https://ai-atoms.com/schemas/model-v1.json", "type": "model", "id": f"model/{slug}", "version": "1.0.0",
        "name": card["name"][:80], "description": card["description"][:1000] or card["name"],
        "vendor": card.get("vendor") or "unknown", **({"family": card["family"]} if card.get("family") else {}),
        "task": TASK.get(card.get("category", ""), "other"),
        "capabilities": card.get("capabilities", []),
        **({"context_window_tokens": card["context_window"]} if isinstance(card.get("context_window"), int) else {}),
        "providers": [provider_entry(card)],
        "links": {"model_card": provider_entry(card)["url"]},
        **({"planned_deprecation": True} if card.get("planned_deprecation") else {}),
        "authored_by": card.get("vendor") or "unknown",
        "source_url": f"https://model-atoms.com/atoms/model-card/{card['id']}/",
        "category": "ai",
        "provenance": {"source": "model-atoms.com", "source_url": f"https://model-atoms.com/atoms/model-card/{card['id']}/",
                       "license": "unknown", "imported_at": TODAY,
                       "notes": "Card as published by model-atoms.com from the Cloudflare Workers AI model list; weights license not recorded there."},
        "tags": ["cloudflare", "workers-ai", *card.get("capabilities", [])],
        "lifecycle": "stable",
    }


def main() -> int:
    cards = load_cards()
    existing = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in MODELS.glob("*.json")}
    by_norm = {normalise(slug): slug for slug in existing}
    merged, created, unchanged = [], [], []
    bumped: set[str] = set()
    for card in cards:
        target = by_norm.get(model_name_of(card["provider_id"]))
        entry = provider_entry(card)
        if target:
            atom = existing[target]
            if any(p["model_id"] == entry["model_id"] for p in atom["providers"]):
                unchanged.append(atom["id"])
                continue
            atom["providers"].append(entry)
            if atom["id"] not in bumped:  # one minor bump per atom per run, however many providers land
                major, minor, patch = atom["version"].split(".")[:3]
                atom["version"] = f"{major}.{int(minor) + 1}.0"
                bumped.add(atom["id"])
            atom["tags"] = sorted(set(atom.get("tags", [])) | {"cloudflare"})
            atom["provenance"]["notes"] = atom["provenance"].get("notes", "").rstrip(".") + f". Cloudflare Workers AI provider entry added from model-atoms.com on {TODAY}."
            if not DRY_RUN:
                (MODELS / f"{target}.json").write_text(json.dumps(atom, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            merged.append(f"{atom['id']} <- {entry['model_id']}")
        else:
            atom = new_atom(card)
            path = MODELS / f"{atom['id'].removeprefix('model/')}.json"
            if path.exists():
                unchanged.append(atom["id"])
                continue
            if not DRY_RUN:
                path.write_text(json.dumps(atom, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            created.append(atom["id"])
    print(json.dumps({"dry_run": DRY_RUN, "cards": len(cards), "merged_into_existing": merged, "created": len(created), "unchanged": len(unchanged)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
