import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
SAMPLES_DIR = PROJECT_ROOT / "samples"
APP_PATH = SCRIPT_DIR / "app.py"


def load_expected(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_pipeline(docx_path: str) -> Dict[str, Any]:
    """
    Run the main pipeline and parse its JSON stdout.
    Assumes app.py prints final JSON only at the end.
    """
    result = subprocess.run(
        [sys.executable, str(APP_PATH), str(docx_path)],
        capture_output=True,
        text=True,
        cwd=str(SCRIPT_DIR),
    )

    if result.returncode != 0:
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)
        raise subprocess.CalledProcessError(
            result.returncode,
            result.args,
            output=result.stdout,
            stderr=result.stderr,
        )

    return json.loads(result.stdout)


def flatten_sections(sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    flat = []

    def walk(items):
        for sec in items:
            if not isinstance(sec, dict):
                continue
            flat.append(sec)
            children = sec.get("children", [])
            if isinstance(children, list) and children:
                walk(children)

    walk(sections or [])
    return flat


def compute_depth(sections: List[Dict[str, Any]]) -> int:
    if not sections:
        return 0

    deepest = 0

    def walk(items, depth):
        nonlocal deepest
        for sec in items:
            if not isinstance(sec, dict):
                continue
            deepest = max(deepest, depth)
            children = sec.get("children", [])
            if isinstance(children, list) and children:
                walk(children, depth + 1)

    walk(sections, 1)
    return deepest


def evaluate_one(docx_path: str, expected_path: str) -> Dict[str, Any]:
    expected = load_expected(expected_path)
    output = run_pipeline(docx_path)

    sections = output.get("sections", [])
    depth = compute_depth(sections)
    section_count = len(flatten_sections(sections))

    score = 0
    checks = []

    if expected.get("require_title"):
        ok = bool(output.get("title"))
        checks.append(("title", ok))
        score += int(ok)

    if expected.get("require_summary"):
        ok = bool(output.get("summary"))
        checks.append(("summary", ok))
        score += int(ok)

    min_sections = expected.get("min_sections", 0)
    ok = section_count >= min_sections
    checks.append(("min_sections", ok))
    score += int(ok)

    min_depth = expected.get("min_depth", 0)
    ok = depth >= min_depth
    checks.append(("min_depth", ok))
    score += int(ok)

    allowed_types = expected.get("allowed_types", [])
    doc_type = output.get("document_type", "other")
    ok = (not allowed_types) or (doc_type in allowed_types)
    checks.append(("document_type", ok))
    score += int(ok)

    confidence = output.get("confidence", 0.0)

    return {
        "file": os.path.basename(docx_path),
        "section_count": section_count,
        "depth": depth,
        "confidence": confidence,
        "passed": score,
        "total": len(checks),
        "checks": checks,
    }


def main():
    rows = []

    if not SAMPLES_DIR.exists():
        raise FileNotFoundError(f"Samples directory not found: {SAMPLES_DIR}")

    for name in sorted(os.listdir(SAMPLES_DIR)):
        if not name.endswith(".docx"):
            continue

        docx_path = SAMPLES_DIR / name
        expected_path = SAMPLES_DIR / name.replace(".docx", ".expected.json")

        if not expected_path.exists():
            print(f"Skipping {name}: missing expected file")
            continue

        row = evaluate_one(str(docx_path), str(expected_path))
        rows.append(row)

    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()