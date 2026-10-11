import argparse
import json
import sys
from pathlib import Path

from .collect import collect
from .core import ContractError, evaluate


def load(path):
    def reject_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ContractError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Agent-assisted intent verification")
    commands = parser.add_subparsers(dest="command", required=True)
    gather = commands.add_parser("collect")
    gather.add_argument("--repo", required=True)
    gather.add_argument("--base", required=True)
    gather.add_argument("--head", default="HEAD")
    gather.add_argument("--document", action="append", default=[])
    triage = commands.add_parser("triage")
    triage.add_argument("--bundle", required=True)
    triage.add_argument("--analysis", required=True)
    triage.add_argument("--policy", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "collect":
            result = collect(args.repo, args.base, args.head, args.document)
        else:
            result = evaluate(load(args.bundle), load(args.analysis), load(args.policy))
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        # Contract failure differs from a valid decision. Consumers inspect JSON decision.
        return 0
    except (ContractError, OSError, ValueError, TypeError) as exc:
        print(f"Invalid input or unavailable evidence: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
