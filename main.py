from __future__ import annotations

import argparse
import sys

from lingua_agent.graph import build_translation_graph


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LinguaGraph translation teaching agent")
    parser.add_argument("--pair", default="zh_ru", help="Language pair config, e.g. zh_ru or ru_zh")
    parser.add_argument("--level", default="B1", help="Learner level, e.g. A2/B1/B2/C1")
    parser.add_argument("--domain", default="general", help="Domain, e.g. general/education/business")
    parser.add_argument("--mode", default="student", choices=["student", "teacher"])
    parser.add_argument("--source", default="", help="Source text")
    parser.add_argument("--translation", default="", help="Student translation to evaluate")
    parser.add_argument("--reference", default="", help="Reference translation")
    parser.add_argument(
        "--task",
        choices=["generate_exercise", "evaluate_translation"],
        default=None,
        help="Task type. Defaults to evaluation when --translation is provided.",
    )
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    app = build_translation_graph()

    result = app.invoke(
        {
            "language_pair": args.pair,
            "user_level": args.level,
            "domain": args.domain,
            "mode": args.mode,
            "source_text": args.source,
            "user_translation": args.translation,
            "reference_translation": args.reference,
            "task_type": args.task,
        }
    )
    print(result["report"])

    next_exercises = result.get("next_exercises", [])
    if next_exercises:
        print("\n## 后续训练")
        for item in next_exercises:
            print(f"- {item['description']}")


if __name__ == "__main__":
    main()
