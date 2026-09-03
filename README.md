# ai-atoms

**What is this?** A typed, versioned catalog of AI runtime primitives: skills, hooks, prompts,
agents, personas, and models. Every atom is a JSON file that validates against its class schema,
carries a category from one shared vocabulary and the provenance of where it came from, and is
served at `https://ai-atoms.com/atoms/<class>/<slug>.json`.

**Who is it for?** Runtime authors (Claude Code, Olympus, the `ai` CLI) that want to install
bounded behaviour by id, and contributors who want to publish one.

**How do I run it?**

```bash
pip install jsonschema pytest
python3 scripts/build-exports.py      # validates every atom, writes exports/catalog.json
python3 -m pytest                     # build-script and hook tests
cd web && npm ci && npm run build     # static site into web/dist/

python3 scripts/import-ollama-models.py    # refresh model atoms from ollama.com/library
python3 scripts/import-claudeskills.py     # import new skills from claudeskills.in
```

**Where do I start?** `https://ai-atoms.com/start/` for people; `https://ai-atoms.com/ai/index.json` and `/llms.txt` for agents.

**How do I contribute or extend it?** See `CONTRIBUTING.md` for the per-class rules,
`SPEC.md` for every field, `ARCHITECTURE.md` for the pipeline, and `docs/adr/` for why it is
shaped this way. The site's `/builder/` page generates a valid starting file for any class.

Licensing: code Apache-2.0, data CC-BY-4.0. Part of the convergent-systems.co atoms ecosystem.
