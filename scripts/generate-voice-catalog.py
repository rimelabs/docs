#!/usr/bin/env python3
"""Generate per-model voice catalog pages from a committed catalog snapshot.

Source of truth: users.rime.ai/data/voices/voice_details.json
Only fields that are 100% populated for a model become columns. Sparse fields
(dialect, demographic, genre, styles) are never rendered as columns because a
blank cell reads as "none" rather than "not specified".
"""
import json, sys, collections, pathlib

SNAP = sys.argv[1]
OUTDIR = pathlib.Path(sys.argv[2])
# Only the two models that outlive the retirements get a catalog page. Arcana
# retires 2026-08-15 and Mist v2 is superseded, so browsing their catalogs to
# choose a voice would point developers at a dead end.
MODELS = [
    ("coda",   "docs/voices-coda.mdx",    "Coda voices",    "Coda"),
    ("mistv3", "docs/voices-mist-v3.mdx", "Mist v3 voices", "Mist v3"),
]
LANGNAME = {"eng":"English","spa":"Spanish","ger":"German","fra":"French","por":"Portuguese",
            "jpn":"Japanese","ara":"Arabic","hin":"Hindi","heb":"Hebrew"}

rows = json.load(open(SNAP))
rows = rows if isinstance(rows, list) else rows.get("voices", rows)
by_model = collections.defaultdict(list)
for r in rows:
    if isinstance(r, dict) and r.get("speaker"):
        by_model[(r.get("modelId") or "").strip()].append(r)

# Catalog records whose `description` contradicts the record's own `lang`.
# Reported to the modeling team 2026-08-04. The description is withheld rather
# than published, because generating from the catalog would republish the error.
# Remove an entry here once the catalog record is corrected.
SUPPRESS_DESCRIPTION = {
    # Records whose `description` names a language the record is not filed under,
    # or claims the voice is bilingual when only one language record exists.
    # Reported to the modeling team 2026-08-05. The description is withheld rather
    # than published, because generating from the catalog would republish the error.
    # Remove an entry once the catalog record is corrected.
    ("alfhild",  "coda",   "eng"),  # "adult German female voice", filed English/US
    ("yukiko",   "coda",   "eng"),  # "Japanese female voice with a Kansai lilt", filed English/US
    ("pola",     "coda",   "eng"),  # "Dominican Spanish female voice", filed English
    ("pola",     "mistv3", "eng"),  # same description, filed English
    ("pola",     "arcana", "eng"),  # same; the arcana `spa` record is correct and keeps it
    ("lucia",    "mistv2", "spa"),  # "Brazilian Portuguese voice", filed Spanish
    ("lucia",    "mistv3", "spa"),  # same; the coda `por` record is correct and keeps it
    ("solana",   "coda",   "eng"),  # "bilingual across English and Brazilian Portuguese", only eng exists
    ("potrero",  "coda",   "eng"),  # "bilingual American male voice", only eng exists, second language unnamed
}

def esc(s):
    return (s or "").replace("|", "\\|").strip()

for model, path, title, label in MODELS:
    recs = by_model.get(model, [])
    if not recs:
        print(f"  skip {model}: no records"); continue
    # completeness gate: only emit a column if every record for this model has it
    def complete(field):
        return all((r.get(field) or "").strip() for r in recs)
    cols = [("speaker","Voice")]
    for f, h in (("gender","Gender"), ("age","Age"), ("country","Country")):
        if complete(f): cols.append((f,h))
    show_desc = any((r.get("description") or "").strip() for r in recs)

    langs = collections.defaultdict(list)
    for r in recs: langs[(r.get("lang") or "").strip()].append(r)
    # stable order: English first, then by descending count, then alphabetical code
    order = sorted(langs, key=lambda l: (l != "eng", -len(langs[l]), l))

    out = []
    out.append("---")
    out.append(f'title: "{title}"')
    out.append(f'description: "Every {label} voice, grouped by language, with the metadata the public catalog publishes."')
    out.append("---")
    out.append("")
    out.append("{/* Generated from the voice catalog snapshot in data/voices/.")
    out.append("    Regenerate with the catalog script; do not hand-edit this file.")
    out.append("    Curated recommendations belong on /docs/voices, not here. */}")
    out.append("")
    n_voices = len({r["speaker"].lower() for r in recs})
    multi = sum(1 for s, ls in collections.Counter(
        (r["speaker"].lower()) for r in recs).items() if ls > 1)
    out.append(f"The public catalog publishes {n_voices} {label} voices. Pass the value in the Voice "
               f"column as `speaker`, with `modelId` set to `{model}` and `lang` set to the code given "
               f"in the section you took the voice from.")
    out.append("")
    if multi == 0:
        out.append(f"Each {label} voice serves exactly one language. {label} as a model covers "
                   f"{len(order)} languages, but no individual voice crosses between them, so choosing "
                   f"a language narrows the voices available to you. Pairing a voice with a different "
                   f"`lang` is not a supported combination.")
    else:
        out.append(f"{multi} of these voices serve more than one language and appear in more than one "
                   f"section below. The rest serve exactly one, so pairing a voice with a different "
                   f"`lang` is not a supported combination.")
    out.append("")
    out.append(f"**To hear a voice, do not rely on the descriptions here.** Play it in the "
               f"[Rime dashboard](https://app.rime.ai), or ask an assistant connected to the "
               f"[hosted MCP server](/docs/mcp) to browse and synthesize a line for you: "
               f"[`list_voices`](/mcp-reference/list-voices) needs no API key, and "
               f"[`synthesize_speech`](/mcp-reference/synthesize-speech) uses yours. This page is a "
               f"reference index for looking up what exists and what it works with.")
    out.append("")
    out.append(f"Use your browser's find command to search by voice name, country, or description. "
               f"For the machine-readable source, see [the voice details endpoint](/api-reference/data/voice-details).")
    out.append("")
    out.append(f"Switching to {label} from another model? A voice name is not carried by every model, "
               f"so check [voice availability on Coda and Mist v3](/docs/voices-availability) "
               f"before you "
               f"change `modelId`.")
    out.append("")
    if len(order) > 1:
        jump = " · ".join(f"[{LANGNAME.get(l,l)}](#{LANGNAME.get(l,l).lower()})" for l in order)
        out.append(f"**Jump to:** {jump}")
        out.append("")
    def emit_table(recs_t):
        """One table for a list of records. There is no Featured column: the
        flag is expressed by which table a voice appears in, which keeps the
        table narrow enough that Description stays on screen."""
        head = [h for _, h in cols] + (["Description"] if show_desc else [])
        out.append("| " + " | ".join(head) + " |")
        out.append("|" + "|".join(["---"] * len(head)) + "|")
        for r in sorted(recs_t, key=lambda x: x["speaker"].lower()):
            cells = []
            for f, _ in cols:
                v = esc(r.get(f))
                cells.append(f"`{v}`" if f == "speaker" else v)
            if show_desc:
                key = (r["speaker"].lower(), model, (r.get("lang") or "").strip())
                cells.append("Withheld pending a catalog correction."
                             if key in SUPPRESS_DESCRIPTION else esc(r.get("description")))
            out.append("| " + " | ".join(cells) + " |")
        out.append("")

    for l in order:
        recs_l = langs[l]
        name = LANGNAME.get(l, l)
        feat = [r for r in recs_l if r.get("flagship")]
        rest = [r for r in recs_l if not r.get("flagship")]
        # Long sections collapse by default so the human path stays shallow.
        # Accordions render their contents in the page, so an agent or a browser
        # find still sees every row. Threshold picked so short languages, which
        # are already scannable, are not hidden behind a click.
        collapse = len(recs_l) > 25
        out.append(f"## {name}")
        out.append("")
        if feat and rest:
            out.append(f"{len(recs_l)} voices. The {len(feat)} featured voices are in the first table, "
                       f"the remaining {len(rest)} in the second, each alphabetical. Set `lang` to "
                       f"`{l}` for this language.")
            out.append("")
            out.append(f"**Featured {name} voices**")
            out.append("")
            emit_table(feat)
            if collapse:
                out.append(f'<Accordion title="All other {name} voices ({len(rest)})">')
                out.append("")
                emit_table(rest)
                out.append("</Accordion>")
                out.append("")
            else:
                out.append(f"**All other {name} voices**")
                out.append("")
                emit_table(rest)
        else:
            if feat:
                intro = (f"{len(recs_l)} voices, listed alphabetically. All of them are featured "
                         f"voices.")
            else:
                intro = f"{len(recs_l)} voices, listed alphabetically."
            out.append(f"{intro} Set `lang` to `{l}` for this language.")
            out.append("")
            if collapse:
                out.append(f'<Accordion title="{name} voices ({len(recs_l)})">')
                out.append("")
                emit_table(recs_l)
                out.append("</Accordion>")
                out.append("")
            else:
                emit_table(recs_l)
    p = OUTDIR / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"  {path}: {len(recs)} voices, {len(order)} languages, {len('\n'.join(out))/1024:.1f} KB, cols={[h for _,h in cols]}")

# ---------------------------------------------------------------------------
# Availability matrix. Columns are only the two models that outlive the
# retirements, because those are the only destinations worth switching to.
# Rows are the voices at least one of them serves, so a name that is absent
# means the voice does not survive: stated explicitly rather than implied by
# a row of crosses.
# ---------------------------------------------------------------------------

SURVIVORS = [("coda", "Coda"), ("mistv3", "Mist v3")]
# Models a developer might be switching away from, with why.
LEGACY = [("arcana", "Arcana", "retires August 15, 2026"),
          ("mistv2", "Mist v2", "superseded by Mist v3"),
          ("mist", "Mist", "superseded by Mist v3")]

def write_availability(rows, out_path):
    spk = collections.defaultdict(set)
    for r in rows:
        if isinstance(r, dict) and r.get("speaker"):
            spk[r["speaker"].strip().lower()].add((r.get("modelId") or "").strip())
    on = {m: {k for k, v in spk.items() if m in v} for m, _ in SURVIVORS + [(x[0], x[1]) for x in LEGACY]}
    surv = on["coda"] | on["mistv3"]
    o = []
    o.append("---")
    o.append('title: "Voice availability on Coda and Mist v3"')
    o.append('description: "Whether the voice you use today is carried by Coda or Mist v3, the two '
             'models that outlive the retirements."')
    o.append("---")
    o.append("")
    o.append("{/* Generated from the voice catalog snapshot in data/voices/.")
    o.append("    Regenerate with scripts/generate-voice-catalog.py; do not hand-edit. */}")
    o.append("")
    o.append("Coda and Mist v3 are the two models that outlive the retirements. A voice name is not "
             "carried by every model, so changing `modelId` while keeping the same `speaker` can "
             "leave you naming a voice the target does not serve. Check your voice here first.")
    o.append("")
    o.append(f"<Warning>**If your voice is not in the table below, neither Coda nor Mist v3 serves "
             f"it, and you need to choose a different voice rather than change `modelId`.** That "
             f"applies to {len(spk) - len(surv)} of the {len(spk)} names in the catalog, including "
             f"{len(on['arcana'] - surv)} of Arcana's {len(on['arcana'])}. A shared name is also no "
             f"guarantee of identical audio: each model is trained separately, so treat a match as "
             f"permission to try the switch and compare audio on your own text before moving "
             f"production traffic.</Warning>")
    o.append("")
    o.append("## What survives from the models being retired")
    o.append("")
    o.append("| Currently on | Why you are moving | Voices | Also on Coda | Also on Mist v3 | On neither |")
    o.append("|---|---|---:|---:|---:|---:|")
    for m, label, why in LEGACY:
        s = on[m]
        o.append(f"| {label} | {why} | {len(s)} | {len(s & on['coda'])} | {len(s & on['mistv3'])} "
                 f"| {len(s - surv)} |")
    o.append("")
    o.append(f"Arcana is the hardest move: {len(on['arcana'] - surv)} of its {len(on['arcana'])} "
             f"voices have no counterpart on either surviving model, so most Arcana users need a "
             f"voice change rather than a parameter change. Only {len(on['coda'] & on['mistv3'])} "
             f"names are on both Coda and Mist v3, so switching between the two surviving models is "
             f"not a drop-in change either.")
    o.append("")
    o.append("## Voices Coda or Mist v3 serves")
    o.append("")
    o.append(f"{len(surv)} names. A check mark means the model serves that name in at least one "
             f"language, not in every language. For the languages a given voice serves, see the "
             f"[Coda](/docs/voices-coda) or [Mist v3](/docs/voices-mist-v3) catalog.")
    o.append("")
    # 253 rows is a reference lookup, not something to scan, so it collapses by
    # default. Accordion contents render in the page, so browser find still
    # reaches every row.
    o.append(f'<Accordion title="All {len(surv)} voices">')
    o.append("")
    o.append("| Voice | " + " | ".join(n for _, n in SURVIVORS) + " |")
    o.append("|---" + "|:---:" * len(SURVIVORS) + "|")
    for s in sorted(surv):
        o.append(f"| `{s}` | " + " | ".join("✅" if s in on[m] else "❌" for m, _ in SURVIVORS) + " |")
    o.append("</Accordion>")
    o.append("")
    out_path.write_text("\n".join(o) + "\n", encoding="utf-8")
    print(f"  docs/voices-availability.mdx: {len(surv)} surviving names of {len(spk)}, "
          f"{len(chr(10).join(o))/1024:.1f} KB")

write_availability(rows, OUTDIR / "docs/voices-availability.mdx")
