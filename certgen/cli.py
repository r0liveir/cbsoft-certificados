from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .core import CertificateError, build_context, parse_mappings, safe_filename
from .input import read_xlsx
from .pptx import render, template_variables


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="certgen", description="Generate certificate batches from PowerPoint and XLSX data.")
    subcommands = parser.add_subparsers(dest="command", required=True)
    variables = subcommands.add_parser("variables", help="List {{VARIABLES}} in one template slide.")
    variables.add_argument("--template", required=True, type=Path)
    variables.add_argument("--slide", required=True, type=int)
    generate = subcommands.add_parser("generate", help="Validate and render one certificate per data row.")
    generate.add_argument("--template", required=True, type=Path)
    generate.add_argument("--slide", required=True, type=int)
    generate.add_argument("--input", required=True, help="Local .xlsx file or publicly accessible Google Sheets URL.")
    generate.add_argument("--data-sheet", required=True)
    generate.add_argument("--config-sheet", default="config", help="Use '' to disable workbook-wide config.")
    generate.add_argument("--mapping", type=Path, help="Optional JSON mapping for variables that do not match sheet labels.")
    generate.add_argument("--output", required=True, type=Path)
    generate.add_argument("--pdf", action="store_true", help="Also convert generated presentations to PDF using LibreOffice.")
    return parser


def _mapping(path: Path | None) -> dict:
    if not path:
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CertificateError(f"Could not read mapping JSON: {error}") from error
    if not isinstance(data, dict):
        raise CertificateError("Mapping JSON must be an object.")
    return data.get("variables", data)


def _convert_to_pdf(pptx_file: Path, output: Path) -> None:
    command = shutil.which("libreoffice")
    if not command:
        raise CertificateError("PDF output requires LibreOffice on PATH.")
    with tempfile.TemporaryDirectory(prefix="certgen-") as directory:
        result = subprocess.run(
            [command, "--headless", "--convert-to", "pdf", "--outdir", directory, str(pptx_file)],
            capture_output=True,
            text=True,
        )
        produced = Path(directory, pptx_file.with_suffix(".pdf").name)
        if result.returncode != 0 or not produced.exists():
            raise CertificateError("LibreOffice could not create PDF: " + (result.stderr or result.stdout).strip())
        output.mkdir(parents=True, exist_ok=True)
        shutil.copy2(produced, output / produced.name)


def _generate(args) -> int:
    variables = template_variables(args.template, args.slide)
    if not variables:
        raise CertificateError("The selected slide has no {{VARIABLE}} placeholders.")
    mappings = parse_mappings(_mapping(args.mapping))
    unknown = set(mappings) - variables
    if unknown:
        raise CertificateError("Mapping references variables absent from template: " + ", ".join(sorted(unknown)))
    config, rows = read_xlsx(args.input, args.config_sheet or None, args.data_sheet)

    contexts = []
    errors = []
    for row_number, row in enumerate(rows, start=2):
        try:
            contexts.append(build_context(variables, row, config, mappings))
        except CertificateError as error:
            errors.append(f"{args.data_sheet}!{row_number}: {error}")
    if errors:
        raise CertificateError("Validation failed; no certificates were generated:\n- " + "\n- ".join(errors))

    args.output.mkdir(parents=True, exist_ok=True)
    for row_number, context in enumerate(contexts, start=2):
        filename = safe_filename(f"{args.data_sheet}-{row_number - 1}") + ".pptx"
        destination = args.output / filename
        render(args.template, args.slide, context, destination)
        if args.pdf:
            _convert_to_pdf(destination, args.output)
    print(f"Generated {len(contexts)} certificate(s) in {args.output}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "variables":
            for variable in sorted(template_variables(args.template, args.slide)):
                print(variable)
            return 0
        return _generate(args)
    except CertificateError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
