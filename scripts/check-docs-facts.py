#!/usr/bin/env python3
"""Offline drift guard for docs.rime.ai.

Runs against committed data only. Never touches the network, and needs no
dependencies beyond the Python standard library.

Four checks, deliberately narrow. Each one exists because the syntax it reads is
itself the fact, so a correct rewording cannot fail it:

  VOICE_MODEL_MISMATCH   a code example pairs a speaker with a model that does
                         not serve it, per the committed catalog snapshot
  UNKNOWN_MODEL_ID       a code example sets a modelId that is not a real model
  FEATURE_MATRIX_DRIFT   the feature matrix in docs/models.mdx disagrees with
                         data/models/capabilities.json
  GENERATED_PAGE_STALE   a generated page does not match what the generator
                         produces from the committed snapshot
  FORBIDDEN_CHARACTER    an em dash or a curly quote, which the editorial standard
                         in CLAUDE.md bans; published changelog entries are exempt

Checks deliberately NOT implemented, because they cry wolf:

  Counting integers near a model name in prose. "Coda has 184 voices" and
  "Coda added 6 voices" are indistinguishable to a proximity scan. Counts are
  checked only inside generated pages, which GENERATED_PAGE_STALE already covers.

  Asserting on wording. A rule banning "Mist v3 supports pronunciation control"
  fires on the correct sentence "Mist v3 does not support pronunciation control".
  Prose claims are kept true by rendering them from one place, not by a linter.

Usage:  python3 scripts/check-docs-facts.py [--verbose]
Exit:   0 clean, 1 findings.
"""

import glob
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT = os.path.join(ROOT, "data/voices/voice-details.snapshot.json")
CAPABILITIES = os.path.join(ROOT, "data/models/capabilities.json")
ALLOW = "drift-guard: allow-invalid-example"

# A value that is a placeholder, a schema type, or a cloned-voice id rather than
# a public catalog voice. Never treated as a claim about the catalog.
PLACEHOLDER = re.compile(
    r"^(<[^>]*>|\{+.*\}+|\$\{.*\}|YOUR[_ -].*|your[_ -].*|xxx+|\.\.\.|string|"
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$",
    re.I,
)
FENCE = re.compile(r"```[^\n]*\n(.*?)```", re.S)
KV = r'["\']?\b{}\b["\']?\s*[:=]\s*["\']([^"\']+)["\']'


class Finding:
    def __init__(self, rule, path, line, observed, expected, fixes, excerpt=""):
        self.rule, self.path, self.line = rule, path, line
        self.observed, self.expected, self.fixes, self.excerpt = observed, expected, fixes, excerpt

    def render(self):
        out = [f"{self.path}:{self.line}", self.rule, "", self.observed, self.expected, ""]
        if self.excerpt:
            out += ["Source:", self.excerpt, ""]
        out.append("Fix: " + self.fixes)
        return "\n".join("  " + l if l else "" for l in out)


def load():
    rows = json.load(open(SNAPSHOT, encoding="utf-8"))
    rows = rows if isinstance(rows, list) else rows.get("voices", rows)
    caps = json.load(open(CAPABILITIES, encoding="utf-8"))
    speaker_models = {}
    for r in rows:
        if isinstance(r, dict) and r.get("speaker"):
            speaker_models.setdefault(r["speaker"].strip().lower(), set()).add(
                (r.get("modelId") or "").strip()
            )
    return speaker_models, caps


def pages():
    for f in sorted(glob.glob(os.path.join(ROOT, "**/*.mdx"), recursive=True)):
        rel = os.path.relpath(f, ROOT)
        if rel.startswith(("node_modules", "snippets/")):
            continue
        yield rel, open(f, encoding="utf-8").read()


def line_of(text, index):
    return text.count("\n", 0, index) + 1


def excerpt_at(text, index, width=2):
    lines = text.split("\n")
    n = line_of(text, index) - 1
    lo, hi = max(0, n - width), min(len(lines), n + width + 1)
    return "\n".join(f"{i+1:>5} | {lines[i]}" for i in range(lo, hi))


def check_examples(speaker_models, caps):
    """VOICE_MODEL_MISMATCH and UNKNOWN_MODEL_ID, literal pairs in one example only."""
    valid = set(caps["models"]) | {a for m in caps["models"].values() for a in m["aliases"]}
    findings = []
    for rel, text in pages():
        for m in FENCE.finditer(text):
            block = m.group(1)
            if ALLOW in text[max(0, m.start() - 200):m.start()]:
                continue
            sp = re.search(KV.format("speaker"), block)
            mo = re.search(KV.format("modelId"), block) or re.search(KV.format("model_id"), block)
            at = line_of(text, m.start())
            if mo:
                mid = mo.group(1).strip()
                if not PLACEHOLDER.match(mid) and mid not in valid:
                    findings.append(Finding(
                        "UNKNOWN_MODEL_ID", rel, at,
                        f'Example sets modelId "{mid}".',
                        "Valid values come from data/models/capabilities.json: "
                        + ", ".join(sorted(valid)) + ".",
                        "Use a real model id, or mark the block with "
                        f"<!-- {ALLOW} --> if the example is intentionally invalid.",
                        excerpt_at(text, m.start()),
                    ))
            if not (sp and mo):
                continue          # a speaker with no model in the same block is not a claim
            speaker, mid = sp.group(1).strip().lower(), mo.group(1).strip()
            if PLACEHOLDER.match(speaker) or PLACEHOLDER.match(mid):
                continue
            if speaker not in speaker_models:
                continue          # cloned or private voice, not a catalog claim
            family = mid if mid in caps["models"] else next(
                (k for k, v in caps["models"].items() if mid in v["aliases"]), mid)
            serving = speaker_models[speaker]
            if family not in serving and mid not in serving:
                findings.append(Finding(
                    "VOICE_MODEL_MISMATCH", rel, at,
                    f'Example pairs speaker "{speaker}" with modelId "{mid}".',
                    f'The committed catalog serves "{speaker}" on: '
                    + ", ".join(sorted(serving)) + ".",
                    f'Change modelId to one of those, pick a voice that "{mid}" serves '
                    f"(see /docs/voices-coda or /docs/voices-mist-v3), or mark the block "
                    f"with <!-- {ALLOW} -->.",
                    excerpt_at(text, m.start()),
                ))
    return findings


def check_feature_matrix(caps):
    """FEATURE_MATRIX_DRIFT.

    Reads the header row to find which model each column represents, rather than
    assuming positions. An earlier version hard-coded three columns, so when the
    Arcana column was removed it silently stopped checking instead of failing,
    and a matrix claiming Coda supported pronunciation control passed clean.
    A guard that quietly disables itself is worse than no guard, so a matrix it
    cannot read is now a finding rather than a skip.
    """
    rel = "docs/models.mdx"
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        return []
    text = open(path, encoding="utf-8").read()
    findings = []

    header = re.search(r"^\|\s*Attribute\s*\|(.+)$", text, re.M)
    if not header:
        return [Finding("FEATURE_MATRIX_DRIFT", rel, 1,
                        "No feature matrix header was found.",
                        "The guard locates the table by a row starting with | Attribute |.",
                        "Restore that header, or update this check if the table moved.")]
    cols = [c.strip() for c in header.group(1).split("|") if c.strip()]
    # Map a column label to the capability key lookup it implies.
    single = {"Coda": "coda", "Arcana": "arcana", "Mist v3": "mistv3", "Mist v2": "mistv2"}
    if not any(c in single or c == "Mist" for c in cols):
        return [Finding("FEATURE_MATRIX_DRIFT", rel, line_of(text, header.start()),
                        f"No column matches a known model: {cols}.",
                        "Columns should be labelled Coda, Arcana, Mist, Mist v3, or Mist v2.",
                        "Rename the column, or teach this check the new label.")]

    for label, key in (("Pronunciation control", "pronunciationControl"),
                       ("Custom pauses", "customPauses")):
        row = re.search(r"^\|\s*\[?" + re.escape(label) + r"\]?[^|]*\|(.+)$", text, re.M)
        if not row:
            findings.append(Finding(
                "FEATURE_MATRIX_DRIFT", rel, line_of(text, header.start()),
                f'The matrix has no "{label}" row.',
                "capabilities.json tracks this capability, so the matrix should state it.",
                f'Add the "{label}" row, or drop the capability from '
                "data/models/capabilities.json if it no longer applies."))
            continue
        cells = [c.strip() for c in row.group(1).split("|")]
        cells = (cells + [""] * len(cols))[:len(cols)]
        at = line_of(text, row.start())
        for col, cell in zip(cols, cells):
            if col in single:
                want = caps["models"][single[col]][key]
                if ("\u2705" in cell) != want:
                    findings.append(Finding(
                        "FEATURE_MATRIX_DRIFT", rel, at,
                        f'Matrix says {col} {label} = "{cell}".',
                        f"capabilities.json says {key} is {want} for {single[col]}.",
                        "Correct the matrix, or correct data/models/capabilities.json "
                        "if the capability actually changed.",
                        excerpt_at(text, row.start())))
            elif col == "Mist":
                v3, v2 = caps["models"]["mistv3"][key], caps["models"]["mistv2"][key]
                if v3 != v2 and "\u2705" in cell:
                    findings.append(Finding(
                        "FEATURE_MATRIX_DRIFT", rel, at,
                        f'Matrix shows a bare check mark in the shared Mist column for {label}.',
                        f"capabilities.json says mistv3={v3} and mistv2={v2}, so the column "
                        "covers two models that differ.",
                        'Name the model the feature applies to, for example "Mist v2 only".',
                        excerpt_at(text, row.start())))
                elif v3 == v2 and ("\u2705" in cell) != v3:
                    findings.append(Finding(
                        "FEATURE_MATRIX_DRIFT", rel, at,
                        f'Matrix says Mist {label} = "{cell}".',
                        f"capabilities.json says {key} is {v3} for both Mist v3 and Mist v2.",
                        "Correct the matrix, or correct data/models/capabilities.json.",
                        excerpt_at(text, row.start())))
    return findings


BANNED = {"\u2014": ("em dash", "em dashes"), "\u2018": ("curly quote", "curly quotes"),
          "\u2019": ("curly quote", "curly quotes"), "\u201c": ("curly quote", "curly quotes"),
          "\u201d": ("curly quote", "curly quotes")}
# CLAUDE.md exempts published changelog entries from retroactive style edits.
STYLE_EXEMPT = ("docs/changelog.mdx",)


def check_style():
    """FORBIDDEN_CHARACTER. The character's presence is the fact, so this cannot
    fire on a correct rewording. CLAUDE.md already requires this scan by hand."""
    findings = []
    for rel, text in pages():
        if rel in STYLE_EXEMPT:
            continue
        seen = {}
        for i, ch in enumerate(text):
            if ch in BANNED:
                seen.setdefault(BANNED[ch], []).append(line_of(text, i))
        for (one, many), lines in seen.items():
            shown = ", ".join(str(n) for n in sorted(set(lines))[:8])
            more = f" and {len(set(lines))-8} more" if len(set(lines)) > 8 else ""
            findings.append(Finding(
                "FORBIDDEN_CHARACTER", rel, lines[0],
                f"{len(lines)} {one if len(lines) == 1 else many} on line(s) {shown}{more}.",
                "CLAUDE.md bans the em dash outright and requires straight quotes. "
                "An en dash is allowed inside a numeric range.",
                "Rewrite with a period, comma, colon, or parentheses as grammar "
                "requires, and replace curly quotes with straight ones."))
    return findings


def check_generated_pages():
    """GENERATED_PAGE_STALE.

    Generates into a temporary directory and compares, rather than regenerating in
    place. Regenerating over the working tree would silently overwrite a hand edit
    instead of reporting it, so the guard would pass by destroying its own evidence.
    """
    gen = os.path.join(ROOT, "scripts/generate-voice-catalog.py")
    if not os.path.exists(gen):
        return []
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run([sys.executable, gen, SNAPSHOT, tmp],
                           capture_output=True, text=True, cwd=ROOT)
        if r.returncode != 0:
            return [Finding("GENERATED_PAGE_STALE", "scripts/generate-voice-catalog.py", 1,
                            "The generator exited non-zero.", r.stderr.strip()[:400],
                            "Fix the generator.")]
        findings = []
        produced = glob.glob(os.path.join(tmp, "**/*.mdx"), recursive=True)
        if not produced:
            return [Finding("GENERATED_PAGE_STALE", "scripts/generate-voice-catalog.py", 1,
                            "The generator produced no pages.",
                            "It should write the catalog pages.", "Fix the generator.")]
        for made in sorted(produced):
            rel = os.path.relpath(made, tmp)
            live = os.path.join(ROOT, rel)
            want = open(made, encoding="utf-8").read()
            if not os.path.exists(live):
                findings.append(Finding(
                    "GENERATED_PAGE_STALE", rel, 1,
                    "The generator produces this page but it is not committed.",
                    "Every generated page must be committed.",
                    "Run python3 scripts/generate-voice-catalog.py "
                    "data/voices/voice-details.snapshot.json . and commit the result."))
                continue
            have = open(live, encoding="utf-8").read()
            if have != want:
                n = next((i + 1 for i, (a, b) in enumerate(
                    zip(have.split("\n"), want.split("\n"))) if a != b), 1)
                findings.append(Finding(
                    "GENERATED_PAGE_STALE", rel, n,
                    "This page differs from what the generator produces.",
                    "Generated pages are not hand-editable; the snapshot and the "
                    "generator are the source of truth.",
                    "Run python3 scripts/generate-voice-catalog.py "
                    "data/voices/voice-details.snapshot.json . and commit the result. "
                    "To change the wording, change the generator."))
        return findings


def main():
    verbose = "--verbose" in sys.argv
    speaker_models, caps = load()
    findings = (check_examples(speaker_models, caps)
                + check_feature_matrix(caps)
                + check_style()
                + check_generated_pages())
    counts = {}
    for f in findings:
        counts[f.rule] = counts.get(f.rule, 0) + 1
    if not findings:
        if verbose:
            print(f"docs facts: clean. {len(list(pages()))} pages checked against "
                  f"{os.path.relpath(SNAPSHOT, ROOT)} and "
                  f"{os.path.relpath(CAPABILITIES, ROOT)}.")
        else:
            print("docs facts: clean.")
        return 0
    print(f"docs facts: {len(findings)} finding(s)\n")
    for f in findings:
        print(f.render())
        print()
    print("  Summary: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    print("  Recheck locally: python3 scripts/check-docs-facts.py")
    return 1


if __name__ == "__main__":
    sys.exit(main())
