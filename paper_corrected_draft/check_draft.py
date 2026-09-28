"""Static consistency check for the corrected draft (no LaTeX toolchain required).

python paper_corrected_draft/check_draft.py

Checks brace and environment balance per file, that every \\input and \\includegraphics target
exists, that every \\ref has a \\label, that every
\\citep/\\citet key is in ../historical/paper/references.bib, and that withdrawn historical figures appear only
in the appendix section that lists them as withdrawn. Exit 0 = all checks pass.
"""
import re
import sys
from pathlib import Path

DRAFT = Path(__file__).resolve().parent
# 11.9% is omitted: it is also the corrected Grok Stage C resolution rate (27/226).
WITHDRAWN = ["50.0\\%", "38.1\\%", "65.9\\%", "5.3\\%", "28.8\\%", "0.537", "50--66", "134/231"]


def expand(path, seen):
    text = path.read_text(encoding="utf-8")
    seen.append(path)
    for target in re.findall(r"\\input\{([^}]+)\}", text):
        child = (DRAFT / target).with_suffix(".tex")
        if not child.is_file():
            raise SystemExit(f"missing \\input target: {target}")
        text += "\n" + expand(child, seen)
    return text


def main():
    files = []
    text = expand(DRAFT / "main.tex", files)
    problems = []
    for path in files:
        source = re.sub(r"\\[{}%]|%.*", "", path.read_text(encoding="utf-8"))
        if source.count("{") != source.count("}"):
            problems.append(f"unbalanced braces: {path.name}")
        begins = re.findall(r"\\begin\{(\w+\*?)\}", source)
        ends = re.findall(r"\\end\{(\w+\*?)\}", source)
        if sorted(begins) != sorted(ends):
            problems.append(f"unmatched environments: {path.name}")
    for target in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", text):
        if not (DRAFT / target).is_file():
            problems.append(f"missing figure: {target}")
    labels = set(re.findall(r"\\label\{([^}]+)\}", text))
    refs = set(re.findall(r"\\ref\{([^}]+)\}", text))
    problems += [f"undefined \\ref: {r}" for r in sorted(refs - labels)]
    bib = (DRAFT / "../historical/paper/references.bib").read_text(encoding="utf-8")
    keys = set(re.findall(r"@\w+\{([^,\s]+),", bib))
    cited = {k.strip() for group in re.findall(r"\\cite[pt]?\{([^}]+)\}", text) for k in group.split(",")}
    problems += [f"unknown citation key: {k}" for k in sorted(cited - keys)]
    body = "\n".join(p.read_text(encoding="utf-8") for p in files if p.name != "appendix.tex")
    appendix = (DRAFT / "appendix.tex").read_text(encoding="utf-8")
    historical = appendix.split("\\label{app:historical}", 1)[1].split("\\section", 1)[0]
    outside = appendix.replace(historical, "")
    for token in WITHDRAWN:
        for name, source in (("main text", body), ("appendix outside the withdrawn list", outside)):
            if token in source:
                problems.append(f"withdrawn figure {token} appears in {name}")
    print(f"files: {len(files)}; labels: {len(labels)}; refs: {len(refs)}; citations: {len(cited)}")
    for p in problems:
        print("FAIL", p)
    print("PASS" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
