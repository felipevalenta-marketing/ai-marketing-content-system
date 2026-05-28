"""Argparse-based CLI entrypoint for the AI Marketing Content System."""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from typing import Any, Callable
import traceback

from src.cli.cli_renderer import render_cli_result
from src.cli.commands import (
    handle_assets,
    handle_campaign,
    handle_config,
    handle_generate,
    handle_smoke,
    handle_validate,
)


CommandHandler = Callable[[Namespace], dict[str, Any]]


class CLIArgumentParser(ArgumentParser):
    """Argument parser that raises friendly errors instead of exiting loudly."""

    def error(self, message: str) -> None:  # type: ignore[override]
        raise ValueError(message)


def build_parser() -> ArgumentParser:
    """Build the top-level CLI parser."""

    parser = CLIArgumentParser(prog="main.py", description="AI Marketing Content System CLI")
    subparsers = parser.add_subparsers(dest="command")

    _add_generate_parser(subparsers)
    _add_campaign_parser(subparsers)
    _add_assets_parser(subparsers)
    _add_validate_parser(subparsers)
    _add_smoke_parser(subparsers)
    _add_config_parser(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint that dispatches subcommands safely."""

    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except ValueError as exc:
        result = {
            "command": "unknown",
            "success": False,
            "mode": "inspection",
            "summary": {},
            "payload": {},
            "warnings": [],
            "errors": [str(exc)],
            "metadata": {},
        }
        print(render_cli_result(result, output_format="terminal"))
        return 1
    if not getattr(args, "command", None):
        parser.print_help()
        return 0

    handler = getattr(args, "_handler", None)
    if handler is None:
        parser.print_help()
        return 1

    try:
        result = handler(args)
    except ValueError as exc:
        result = {
            "command": getattr(args, "command", "unknown"),
            "success": False,
            "mode": "inspection",
            "summary": {},
            "payload": {},
            "warnings": [],
            "errors": [str(exc)],
            "metadata": {},
        }
    except Exception as exc:  # pragma: no cover - defensive CLI guard
        if getattr(args, "verbose", False):
            traceback.print_exc()
            return 1
        result = {
            "command": getattr(args, "command", "unknown"),
            "success": False,
            "mode": "inspection",
            "summary": {},
            "payload": {},
            "warnings": [],
            "errors": [str(exc)],
            "metadata": {},
        }

    output_format = "json" if getattr(args, "json", False) or getattr(args, "report_json", False) else "markdown" if getattr(args, "markdown", False) or getattr(args, "report_markdown", False) else "terminal"
    print(render_cli_result(result, output_format=output_format))
    return 0 if bool(result.get("success")) else 1


def _add_common_flags(parser: ArgumentParser) -> None:
    """Add shared output and debug flags."""

    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--json", action="store_true", help="Render output as JSON.")
    output_group.add_argument("--markdown", action="store_true", help="Render output as markdown.")
    report_group = parser.add_mutually_exclusive_group()
    report_group.add_argument("--report", action="store_true", help="Generate an analytics report.")
    report_group.add_argument("--report-json", action="store_true", help="Generate and prefer JSON report output.")
    report_group.add_argument("--report-markdown", action="store_true", help="Generate and prefer markdown report output.")
    parser.add_argument("--verbose", action="store_true", help="Show full traceback on unexpected errors.")


def _add_generate_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("generate", help="Run content generation.")
    parser.add_argument("--brand")
    parser.add_argument("--platform")
    parser.add_argument("--content-type")
    parser.add_argument("--audience")
    parser.add_argument("--location")
    parser.add_argument("--property-type")
    parser.add_argument("--creative-direction")
    parser.add_argument("--objective")
    parser.add_argument("--extra-notes")
    parser.add_argument("--visual-style")
    parser.add_argument("--image-type")
    parser.add_argument("--aspect-ratio")
    parser.add_argument("--export", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    _add_common_flags(parser)
    parser.set_defaults(_handler=handle_generate)


def _add_campaign_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("campaign", help="Compose a campaign pack.")
    parser.add_argument("--brand")
    parser.add_argument("--campaign-type")
    parser.add_argument("--audience")
    parser.add_argument("--location")
    parser.add_argument("--property-type")
    parser.add_argument("--objective")
    parser.add_argument("--platforms")
    parser.add_argument("--assets")
    parser.add_argument("--extra-notes")
    parser.add_argument("--export", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    _add_common_flags(parser)
    parser.set_defaults(_handler=handle_campaign)


def _add_assets_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("assets", help="Build an asset coordination plan.")
    parser.add_argument("--brand")
    parser.add_argument("--campaign-type")
    parser.add_argument("--platforms")
    parser.add_argument("--assets")
    parser.add_argument("--objective")
    parser.add_argument("--audience")
    parser.add_argument("--location")
    parser.add_argument("--property-type")
    parser.add_argument("--creative-direction")
    parser.add_argument("--visual-style")
    parser.add_argument("--extra-notes")
    parser.add_argument("--export", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    _add_common_flags(parser)
    parser.set_defaults(_handler=handle_assets)


def _add_validate_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("validate", help="Validate generated or sample content.")
    parser.add_argument("--brand")
    parser.add_argument("--platform")
    parser.add_argument("--content-type")
    parser.add_argument("--text")
    _add_common_flags(parser)
    parser.set_defaults(_handler=handle_validate)


def _add_smoke_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("smoke", help="Run lightweight smoke checks.")
    _add_common_flags(parser)
    parser.set_defaults(_handler=handle_smoke)


def _add_config_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("config", help="Show a safe configuration summary.")
    _add_common_flags(parser)
    parser.set_defaults(_handler=handle_config)
