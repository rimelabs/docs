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
MODELS = [
    ("coda",   "docs/voices-coda.mdx",    "Coda voices",    "Coda"),
    ("arcana", "docs/voices-arcana.mdx",  "Arcana voices",  "Arcana"),
    ("mistv3", "docs/voices-mist-v3.mdx", "Mist v3 voices", "Mist v3"),
    ("mistv2", "docs/voices-mist-v2.mdx", "Mist v2 voices", "Mist v2"),
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
    ("alfhild", "coda",   "eng"),  # described as German, recorded as English/US
    ("solana",  "coda",   "eng"),  # described as bilingual English/Portuguese, only an English record exists
    ("yukiko",  "coda",   "eng"),  # described as Japanese, recorded as English/US
    ("lucia",   "mistv2", "spa"),  # described as Brazilian Portuguese, recorded as Spanish
    ("pola",    "arcana", "eng"),  # English record carries a Spanish description; the spa record is correct
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
    show_featured = any(r.get("flagship") for r in recs)
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
    out.append(f"Use your browser's find command to search by voice name, country, or description. "
               f"For the machine-readable source, see [the voice details endpoint](/api-reference/data/voice-details).")
    out.append("")
    if len(order) > 1:
        jump = " · ".join(f"[{LANGNAME.get(l,l)}](#{LANGNAME.get(l,l).lower()})" for l in order)
        out.append(f"**Jump to:** {jump}")
        out.append("")
    for l in order:
        recs_l = sorted(langs[l], key=lambda r: r["speaker"].lower())
        name = LANGNAME.get(l, l)
        out.append(f"## {name}")
        out.append("")
        out.append(f"{len(recs_l)} voices. Set `lang` to `{l}` for this language.")
        out.append("")
        head = [h for _, h in cols] + (["Featured"] if show_featured else []) + (["Description"] if show_desc else [])
        out.append("| " + " | ".join(head) + " |")
        out.append("|" + "|".join(["---"] * len(head)) + "|")
        for r in recs_l:
            cells = []
            for f, _ in cols:
                v = esc(r.get(f))
                cells.append(f"`{v}`" if f == "speaker" else v)
            if show_featured: cells.append("✅" if r.get("flagship") else "")
            if show_desc:
                key = (r["speaker"].lower(), model, (r.get("lang") or "").strip())
                cells.append("Withheld pending a catalog correction."
                             if key in SUPPRESS_DESCRIPTION else esc(r.get("description")))
            out.append("| " + " | ".join(cells) + " |")
        out.append("")
    p = OUTDIR / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"  {path}: {len(recs)} voices, {len(order)} languages, {len('\n'.join(out))/1024:.1f} KB, cols={[h for _,h in cols]}")
