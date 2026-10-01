import argparse
import json
from collections import defaultdict
from pathlib import Path


def finding_range(finding: dict) -> tuple[int, int]:
    start = int(finding["start_line"])
    end = int(finding.get("end_line", start))
    if start < 1 or end < start:
        raise ValueError("Finding line ranges must be positive and ordered.")
    return start, end


def ranges_overlap(first: tuple[int, int], second: tuple[int, int]) -> bool:
    return first[0] <= second[1] and second[0] <= first[1]


def load_records(path: str) -> list[dict]:
    records = []
    with Path(path).open(encoding="utf-8") as corpus_file:
        for line_number, line in enumerate(corpus_file, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON on line {line_number}: {error}") from error
            if not isinstance(record.get("expected_findings"), list) or not isinstance(
                record.get("predicted_findings"), list
            ):
                raise ValueError(
                    f"Line {line_number} must contain expected_findings and predicted_findings arrays."
                )
            records.append(record)
    return records


def evaluate_records(records: list[dict]) -> dict:
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    duplicate_count = 0
    actionable_count = 0
    actionable_labeled = 0
    severity_matches = 0
    severity_labeled = 0
    anchored_count = 0
    anchor_labeled = 0
    expected_total = 0
    predicted_total = 0
    expected_by_category = defaultdict(int)
    matched_by_category = defaultdict(int)

    for record in records:
        expected = record["expected_findings"]
        predicted = record["predicted_findings"]
        expected_by_id = {finding["id"]: finding for finding in expected}
        if len(expected_by_id) != len(expected):
            raise ValueError("Expected finding IDs must be unique within each record.")
        matched_ids = set()
        signatures = set()
        changed_lines = record.get("changed_lines")
        expected_total += len(expected)
        predicted_total += len(predicted)

        for finding in expected:
            expected_by_category[str(finding["category"]).lower()] += 1

        for finding in predicted:
            path = finding["file"]
            category = str(finding["category"]).lower()
            line_range = finding_range(finding)
            signature = (path, category, line_range)
            duplicate = signature in signatures
            signatures.add(signature)
            if duplicate:
                duplicate_count += 1

            if isinstance(finding.get("actionable"), bool):
                actionable_labeled += 1
                actionable_count += int(finding["actionable"])

            if changed_lines is not None:
                anchor_labeled += 1
                changed = set(changed_lines.get(path, []))
                if any(line_range[0] <= line <= line_range[1] for line in changed):
                    anchored_count += 1

            match = None
            explicit_match = finding.get("matched_expected_id")
            if not duplicate and explicit_match is not None:
                if explicit_match not in expected_by_id:
                    raise ValueError(f"Unknown matched_expected_id: {explicit_match}")
                if explicit_match not in matched_ids:
                    match = expected_by_id[explicit_match]
            elif not duplicate:
                for candidate in expected:
                    if candidate["id"] in matched_ids:
                        continue
                    if str(candidate["category"]).lower() != category:
                        continue
                    if candidate["file"] != path:
                        continue
                    if ranges_overlap(line_range, finding_range(candidate)):
                        match = candidate
                        break

            if match is None:
                false_positives += 1
                continue

            true_positives += 1
            matched_ids.add(match["id"])
            matched_by_category[str(match["category"]).lower()] += 1
            if match.get("severity") is not None and finding.get("severity") is not None:
                severity_labeled += 1
                severity_matches += int(
                    str(match["severity"]).lower() == str(finding["severity"]).lower()
                )

        false_negatives += len(expected) - len(matched_ids)

    precision_denominator = true_positives + false_positives
    recall_denominator = true_positives + false_negatives
    precision = true_positives / precision_denominator if precision_denominator else None
    recall = true_positives / recall_denominator if recall_denominator else None
    f1 = 2 * precision * recall / (precision + recall) if precision and recall else 0.0
    categories = {
        category: {
            "expected": count,
            "matched": matched_by_category[category],
            "coverage": matched_by_category[category] / count,
        }
        for category, count in sorted(expected_by_category.items())
    }

    return {
        "pull_requests": len(records),
        "expected_findings": expected_total,
        "predicted_findings": predicted_total,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "duplicate_predictions": duplicate_count,
        "actionability_rate": actionable_count / actionable_labeled if actionable_labeled else None,
        "actionability_labeled": actionable_labeled,
        "severity_exact_match_rate": severity_matches / severity_labeled if severity_labeled else None,
        "severity_labeled_matches": severity_labeled,
        "changed_line_anchor_rate": anchored_count / anchor_labeled if anchor_labeled else None,
        "line_anchor_labeled": anchor_labeled,
        "category_coverage": categories,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate predicted PR findings against a labeled JSONL corpus.",
        epilog=(
            "Each JSONL record needs expected_findings and predicted_findings arrays. "
            "Findings use id (expected only), category, severity, file, start_line, and optional end_line. "
            "Predictions may include actionable and matched_expected_id; changed_lines maps file paths to line-number arrays."
        ),
    )
    parser.add_argument("corpus", help="JSONL file with one PR record per line")
    parser.add_argument("--output", default="-", help="JSON report path, or '-' for stdout")
    args = parser.parse_args()

    try:
        report = json.dumps(evaluate_records(load_records(args.corpus)), indent=2) + "\n"
        if args.output == "-":
            print(report, end="")
        else:
            destination = Path(args.output)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(report, encoding="utf-8")
    except (OSError, KeyError, TypeError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()