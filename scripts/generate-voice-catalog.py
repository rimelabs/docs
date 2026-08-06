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
    out.append(f"Switching to {label} from another model? A voice name is not carried by every "
               f"model. If the voice you use today is not listed below, {label} does not serve it "
               f"and you need to choose a different one rather than change `modelId` alone.")
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
