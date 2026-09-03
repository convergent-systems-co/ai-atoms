#!/usr/bin/env python3
"""Import model atoms from the Ollama library (https://ollama.com/library).

Ollama publishes no JSON index of its library, so this reads the library page and
takes what it shows for each model: name, one-line description, capability badges
(tools, vision, thinking, embedding, cloud, audio), published sizes, pull count,
tag count, and last-updated date. Each model becomes one `model` atom with a
single Ollama provider entry and a link back to the model page.

Vendor and task are inferred from the model name using the tables below and are
labelled as inferred in `provenance.notes`; a name the tables do not cover gets
vendor "unknown" rather than a guess.

Existing atoms are updated in place (the provider stats change over time); the
atom `version` is bumped on the patch level only when content changed.

Usage: python3 scripts/import-ollama-models.py [--dry-run] [--from-file library.html]
"""
import html
import json
import re
import sys
import urllib.request
from datetime import date, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ATOMS_DIR = REPO / "atoms" / "model"
LIBRARY_URL = "https://ollama.com/library"
TODAY = date.today().isoformat()
DRY_RUN = "--dry-run" in sys.argv

# Leading name fragment -> (vendor, family). Order matters: longest match first.
VENDORS: list[tuple[str, str, str]] = [
    ("llama", "Meta", "Llama"), ("codellama", "Meta", "Code Llama"),
    ("qwen", "Alibaba", "Qwen"), ("qwq", "Alibaba", "QwQ"), ("codeqwen", "Alibaba", "Qwen"),
    ("gemma", "Google", "Gemma"), ("codegemma", "Google", "Gemma"),
    ("mistral", "Mistral AI", "Mistral"), ("mixtral", "Mistral AI", "Mixtral"), ("codestral", "Mistral AI", "Codestral"),
    ("devstral", "Mistral AI", "Devstral"), ("magistral", "Mistral AI", "Magistral"), ("ministral", "Mistral AI", "Ministral"),
    ("deepseek", "DeepSeek", "DeepSeek"), ("deepcoder", "Agentica", "DeepCoder"), ("deepscaler", "Agentica", "DeepScaleR"),
    ("phi", "Microsoft", "Phi"), ("orca", "Microsoft", "Orca"),
    ("command-", "Cohere", "Command"), ("aya", "Cohere", "Aya"),
    ("nomic", "Nomic AI", "Nomic Embed"), ("granite", "IBM", "Granite"), ("glm", "Zhipu AI", "GLM"),
    ("gpt-oss", "OpenAI", "GPT-OSS"), ("nemotron", "NVIDIA", "Nemotron"), ("minimax", "MiniMax", "MiniMax"),
    ("kimi", "Moonshot AI", "Kimi"), ("falcon", "TII", "Falcon"), ("starcoder", "BigCode", "StarCoder"),
    ("yi", "01.AI", "Yi"), ("internlm", "Shanghai AI Lab", "InternLM"), ("smollm", "Hugging Face", "SmolLM"),
    ("olmo", "AI2", "OLMo"), ("tulu", "AI2", "Tülu"), ("snowflake", "Snowflake", "Arctic"),
    ("bge", "BAAI", "BGE"), ("mxbai", "Mixedbread", "mxbai"), ("all-minilm", "sentence-transformers", "MiniLM"),
    ("dbrx", "Databricks", "DBRX"), ("dolphin", "Cognitive Computations", "Dolphin"), ("vicuna", "LMSYS", "Vicuna"),
    ("solar", "Upstage", "Solar"), ("exaone", "LG AI Research", "EXAONE"), ("hermes", "Nous Research", "Hermes"),
    ("openhermes", "Nous Research", "Hermes"), ("zephyr", "Hugging Face", "Zephyr"), ("wizard", "WizardLM", "WizardLM"),
    ("llava", "LLaVA", "LLaVA"), ("moondream", "vikhyat", "Moondream"), ("stablelm", "Stability AI", "StableLM"),
    ("stable-code", "Stability AI", "Stable Code"), ("sqlcoder", "Defog", "SQLCoder"), ("athene", "Nexusflow", "Athene"),
    ("reflection", "Matt Shumer", "Reflection"), ("cogito", "Deep Cogito", "Cogito"), ("bakllava", "SkunkworksAI", "BakLLaVA"),
    ("tinyllama", "TinyLlama", "TinyLlama"), ("neural-chat", "Intel", "Neural Chat"), ("marco", "Alibaba", "Marco"),
    ("sailor", "SEA AI Lab", "Sailor"), ("paraphrase", "sentence-transformers", "MiniLM"), ("snowflake-arctic", "Snowflake", "Arctic"),
    ("shieldgemma", "Google", "ShieldGemma"), ("medgemma", "Google", "MedGemma"), ("functiongemma", "Google", "Gemma"),
    ("embeddinggemma", "Google", "Gemma"), ("nuextract", "NuMind", "NuExtract"), ("bespoke", "Bespoke Labs", "Bespoke"),
    ("opencoder", "OpenCoder", "OpenCoder"), ("openthinker", "Open Thoughts", "OpenThinker"), ("r1-1776", "Perplexity", "R1-1776"),
    ("lfm", "Liquid AI", "LFM"), ("olympiccoder", "Hugging Face", "OlympicCoder"), ("firefunction", "Fireworks AI", "FireFunction"),
    ("nemotron-mini", "NVIDIA", "Nemotron"), ("mistral-nemo", "Mistral AI", "Mistral NeMo"), ("codegeex", "Zhipu AI", "CodeGeeX"),
    ("everythinglm", "Totally Not An LLM", "EverythingLM"), ("meditron", "EPFL", "Meditron"), ("medllama", "Siraj Raval", "MedLlama"),
    ("xwinlm", "Xwin-LM", "Xwin-LM"), ("goliath", "Alpin", "Goliath"), ("notux", "Argilla", "Notux"), ("notus", "Argilla", "Notus"),
    ("megadolphin", "Cognitive Computations", "Dolphin"), ("samantha", "Cognitive Computations", "Samantha"),
    ("nous-hermes", "Nous Research", "Hermes"), ("yarn", "Nous Research", "YaRN"), ("wizardlm", "WizardLM", "WizardLM"),
    ("magicoder", "iSE Lab", "Magicoder"), ("duckdb-nsql", "MotherDuck", "DuckDB-NSQL"), ("alfred", "LightOn", "Alfred"),
    ("codeup", "DeepSE", "CodeUp"), ("codebooga", "oobabooga", "CodeBooga"), ("open-orca", "Open-Orca", "OpenOrca"),
    ("stable-beluga", "Stability AI", "Stable Beluga"), ("orca-mini", "Pankaj Mathur", "Orca Mini"), ("llama-pro", "Tencent ARC", "LLaMA Pro"),
    ("llama-guard", "Meta", "Llama Guard"), ("nexusraven", "Nexusflow", "NexusRaven"), ("dolphincoder", "Cognitive Computations", "Dolphin"),
    ("starling", "Berkeley", "Starling"), ("openchat", "OpenChat", "OpenChat"), ("phind", "Phind", "Phind CodeLlama"),
    ("wizardcoder", "WizardLM", "WizardCoder"), ("wizard-math", "WizardLM", "WizardMath"), ("wizard-vicuna", "WizardLM", "Wizard Vicuna"),
    ("mathstral", "Mistral AI", "Mathstral"), ("mistral-large", "Mistral AI", "Mistral Large"), ("mistral-small", "Mistral AI", "Mistral Small"),
    ("mistrallite", "Amazon", "MistralLite"), ("reader-lm", "Jina AI", "Reader-LM"), ("bge-m3", "BAAI", "BGE"),
    ("granite-embedding", "IBM", "Granite"), ("smallthinker", "PowerInfer", "SmallThinker"), ("exaone-deep", "LG AI Research", "EXAONE"),
    ("qwen3", "Alibaba", "Qwen3"), ("gemma3", "Google", "Gemma 3"), ("llama4", "Meta", "Llama 4"), ("llama3", "Meta", "Llama 3"),
    ("llama2", "Meta", "Llama 2"), ("phi4", "Microsoft", "Phi-4"), ("phi3", "Microsoft", "Phi-3"), ("mistral-openorca", "Open-Orca", "Mistral OpenOrca"),
    ("nomic-embed", "Nomic AI", "Nomic Embed"), ("snowflake-arctic-embed", "Snowflake", "Arctic Embed"), ("deepseek-r1", "DeepSeek", "DeepSeek-R1"),
    ("deepseek-v", "DeepSeek", "DeepSeek-V"), ("deepseek-coder", "DeepSeek", "DeepSeek Coder"), ("gpt-oss", "OpenAI", "GPT-OSS"),
    ("tinydolphin", "Cognitive Computations", "Dolphin"), ("dolphin-mistral", "Cognitive Computations", "Dolphin"),
    ("dolphin-llama3", "Cognitive Computations", "Dolphin"), ("dolphin-phi", "Cognitive Computations", "Dolphin"),
    ("dolphin3", "Cognitive Computations", "Dolphin"), ("nemotron-3", "NVIDIA", "Nemotron 3"), ("qwen2", "Alibaba", "Qwen2"),
    ("qwen2.5", "Alibaba", "Qwen2.5"), ("qwen2.5-coder", "Alibaba", "Qwen2.5-Coder"), ("qwen3-coder", "Alibaba", "Qwen3-Coder"),
    ("qwen3-embedding", "Alibaba", "Qwen3-Embedding"), ("qwen3-vl", "Alibaba", "Qwen3-VL"), ("glm-4", "Zhipu AI", "GLM-4"),
    ("glm-5", "Zhipu AI", "GLM-5"), ("gemma2", "Google", "Gemma 2"), ("gemma3n", "Google", "Gemma 3n"),
]
VENDORS.sort(key=lambda v: -len(v[0]))
CODE_HINT = re.compile(r"coder|code|devstral|codestral|starcoder|sqlcoder|magicoder|duckdb-nsql|nuextract")
SIZE = re.compile(r"^(e?\d+(\.\d+)?(x\d+)?[bm])$")


def http_get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "ai-atoms-import/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def parse_library(page: str) -> list[dict]:
    items = re.findall(r'<li[^>]*class="flex items-baseline[^"]*">(.*?)</li>', page, re.S)
    rows: list[dict] = []
    for item in items:
        name = re.search(r'href="/library/([^"]+)"', item).group(1)
        desc = re.search(r'<p class="max-w-lg[^"]*">(.*?)</p>', item, re.S)
        description = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", desc.group(1)))).strip() if desc else name
        badges = [b.strip() for b in re.findall(r'<span\s+class="inline-flex[^"]*">\s*([^<]+?)\s*</span>', item)]
        sizes = [b.lstrip("e") for b in badges if SIZE.match(b)]
        capabilities = [b for b in badges if not SIZE.match(b)]
        stats = re.findall(r"<span >([^<]+)</span>", item)
        updated = re.search(r'title="([^"]+) UTC"', item)
        rows.append({
            "name": name, "description": description, "capabilities": capabilities, "sizes": sizes,
            "pulls": stats[0] if stats else None, "tag_count": int(stats[1]) if len(stats) > 1 and stats[1].isdigit() else None,
            "updated": datetime.strptime(updated.group(1), "%b %d, %Y %I:%M %p").date().isoformat() if updated else None,
        })
    return rows


def vendor_family(name: str) -> tuple[str, str | None]:
    for prefix, vendor, family in VENDORS:
        if name.startswith(prefix):
            return vendor, family
    return "unknown", None


def task_for(name: str, capabilities: list[str]) -> str:
    if "embedding" in capabilities or "embed" in name:
        return "embedding"
    if "rerank" in name:
        return "reranking"
    if CODE_HINT.search(name):
        return "code-generation"
    if "thinking" in capabilities or re.search(r"r1|reason|think|qwq", name):
        return "reasoning"
    if "vision" in capabilities or "audio" in capabilities or "llava" in name or "ocr" in name:
        return "multimodal"
    return "text-generation"


def row_to_atom(row: dict) -> dict:
    vendor, family = vendor_family(row["name"])
    provider = {
        "name": "Ollama",
        "model_id": row["name"],
        "url": f"https://ollama.com/library/{row['name']}",
        "pull_command": f"ollama pull {row['name']}",
        "run_command": f"ollama run {row['name']}",
    }
    if row["tag_count"] is not None:
        provider["tag_count"] = row["tag_count"]
    if row["pulls"]:
        provider["pulls"] = row["pulls"]
    if row["updated"]:
        provider["updated_at"] = row["updated"]
    atom = {
        "schema": "https://ai-atoms.com/schemas/model-v1.json",
        "type": "model",
        "id": f"model/{row['name']}",
        "version": "1.0.0",
        "name": row["name"],
        "description": row["description"][:1000],
        "vendor": vendor,
        **({"family": family} if family else {}),
        "task": task_for(row["name"], row["capabilities"]),
        "capabilities": row["capabilities"],
        **({"parameter_sizes": row["sizes"]} if row["sizes"] else {}),
        "providers": [provider],
        "links": {"model_card": f"https://ollama.com/library/{row['name']}"},
        "authored_by": vendor,
        "source_url": f"https://ollama.com/library/{row['name']}",
        "category": "ai",
        "provenance": {
            "source": "ollama.com/library",
            "source_url": f"https://ollama.com/library/{row['name']}",
            "license": "unknown",
            "imported_at": TODAY,
            "notes": "Description, capabilities, sizes, pulls, tag count and updated date as shown on the Ollama library page. "
                     "Vendor, family and task are inferred from the model name; weights license is not published on the listing.",
        },
        "tags": ["ollama", "local", *row["capabilities"]],
        "lifecycle": "stable",
    }
    return atom


def bump_patch(version: str) -> str:
    major, minor, patch = version.split(".")[:3]
    return f"{major}.{minor}.{int(patch) + 1}"


def main() -> int:
    if "--from-file" in sys.argv:
        page = Path(sys.argv[sys.argv.index("--from-file") + 1]).read_text(encoding="utf-8")
    else:
        page = http_get(LIBRARY_URL)
    rows = parse_library(page)
    if not rows:
        raise SystemExit("parsed zero models — the library page layout has changed")
    ATOMS_DIR.mkdir(parents=True, exist_ok=True)
    created, updated, unchanged, unknown_vendor = [], [], [], []
    for row in rows:
        atom = row_to_atom(row)
        if atom["vendor"] == "unknown":
            unknown_vendor.append(atom["id"])
        path = ATOMS_DIR / f"{row['name']}.json"
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            atom["version"] = existing["version"]
            atom["provenance"]["imported_at"] = existing.get("provenance", {}).get("imported_at", TODAY)
            if existing == atom:
                unchanged.append(atom["id"])
                continue
            atom["version"] = bump_patch(existing["version"])
            atom["provenance"]["imported_at"] = TODAY
            updated.append(atom["id"])
        else:
            created.append(atom["id"])
        if not DRY_RUN:
            path.write_text(json.dumps(atom, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"dry_run": DRY_RUN, "parsed": len(rows), "created": len(created), "updated": len(updated),
                      "unchanged": len(unchanged), "unknown_vendor": unknown_vendor}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
