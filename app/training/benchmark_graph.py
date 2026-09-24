"""
JGH Benchmark Graph Generator.
Reads the EXACT empirical evaluation report JSON produced by benchmark_evaluator.py,
and generates a professional, high-resolution benchmark visualization.
Every value is dynamically extracted from the runner output.
"""

import sys
import json
import argparse
from pathlib import Path
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ARTIFACT_DIR = Path("C:/Users/nayak_o7hopi6/.gemini/antigravity-ide/brain/8bef9c29-21e0-46ac-a5ba-f1c3ef3a49a2")

def generate_benchmark_graph(report_json_path: Path, output_image_path: Path):
    with open(report_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    metrics = data.get("metrics", {})
    split_name = data.get("split", "Held-Out Test").replace("_", " ").title()
    version_tag = data.get("version_tag", "Production")
    e2e_acc = data.get("e2e_accuracy", 0.0)

    # Required Graph Metrics per Section 22:
    target_keys = [
        ("requirement_understanding", "Requirement\nAccuracy"),
        ("schema_grounding", "Schema\nAccuracy"),
        ("business_rule_accuracy", "Business Rule\nAccuracy"),
        ("sql_accuracy", "SQL\nAccuracy"),
        ("semantic_accuracy", "Semantic\nAccuracy"),
        ("result_accuracy", "Result\nAccuracy"),
        ("response_grounding", "Response\nAccuracy"),
        ("end_to_end_accuracy", "E2E\nAccuracy")
    ]

    labels = []
    values = []
    colors = []

    for k, display_name in target_keys:
        val = metrics.get(k, {}).get("accuracy", 0.0)
        labels.append(display_name)
        values.append(val)
        if k == "end_to_end_accuracy":
            colors.append("#2563EB" if val >= 90.0 else "#DC2626")
        else:
            colors.append("#10B981" if val >= 90.0 else "#F59E0B")

    plt.figure(figsize=(12, 6.5), dpi=300)
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

    bars = plt.bar(labels, values, color=colors, width=0.55, edgecolor="#1E293B", linewidth=1.2)

    # Target threshold line at 90%
    plt.axhline(y=90.0, color="#EF4444", linestyle="--", linewidth=2.0, label="Acceptance Target Threshold (>= 90%)")

    # Annotate bar values
    for bar in bars:
        h = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            h + 1.2,
            f"{h:.1f}%",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
            color="#0F172A"
        )

    plt.ylim(0, 110)
    plt.ylabel("Accuracy Score (%)", fontsize=12, fontweight="bold", labelpad=10)
    plt.title(
        f"JGH Intelligence Engine — End-to-End Quantitative Model Benchmark\n"
        f"Split: {split_name} ({data.get('total_cases', 0)} Cases) | Model: {version_tag} | Primary E2E Accuracy: {e2e_acc:.1f}%",
        fontsize=14,
        fontweight="bold",
        pad=15
    )

    plt.legend(loc="upper right", frameon=True, fontsize=11)
    plt.tight_layout()

    output_image_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_image_path)
    plt.close()
    print(f"[GRAPH GENERATOR] Successfully generated benchmark chart at: {output_image_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, default=str(ARTIFACT_DIR / "jgh_benchmark_graph.png"))
    args = parser.parse_args()

    generate_benchmark_graph(Path(args.input), Path(args.output))
