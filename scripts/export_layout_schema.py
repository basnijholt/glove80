#!/usr/bin/env python3
"""Export LayoutPayload JSON schema from the authoritative Pydantic models."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from glove80.layouts.schema import LayoutPayload

DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "layout_payload.schema.json"


def dump_schema(*, output: Path) -> None:
    schema = LayoutPayload.model_json_schema()
    output.parent.mkdir(parents=True, exist_ok=True)
    json_text = json.dumps(schema, indent=2, ensure_ascii=False) + "\n"
    with output.open("w", encoding="utf-8") as handle:
        handle.write(json_text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Destination file path",
    )
    args = parser.parse_args()
    dump_schema(output=args.output)
    print(f"Wrote schema to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
