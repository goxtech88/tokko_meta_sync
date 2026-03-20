#!/usr/bin/env python3
"""
main.py – CLI entry point for Tokko Broker → Meta Ads catalog sync

Usage:
    python main.py sync           Full sync (fetch → map → upload)
    python main.py sync --dry     Dry run (generates CSV but skips Meta upload)
    python main.py list-tokko     Preview properties from Tokko Broker
    python main.py list-meta      List items currently in Meta catalog
"""

from __future__ import annotations

import argparse
import logging
import sys

from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from rich.panel import Panel

console = Console()


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, console=console)],
    )


# ─── Commands ─────────────────────────────────────────────────


def cmd_sync(args: argparse.Namespace) -> None:
    """Run full sync cycle."""
    from sync import run_sync

    console.print(
        Panel.fit(
            "[bold green]Tokko Broker → Meta Ads Sync[/]\n"
            f"Operation type: [cyan]{args.operation or 'sale'}[/]  |  "
            f"Dry run: [yellow]{'Yes' if args.dry else 'No'}[/]",
            border_style="green",
        )
    )

    result = run_sync(operation_type=args.operation, dry_run=args.dry)

    # Summary
    if result.error:
        console.print(f"\n[bold red]✗ Sync failed:[/] {result.error}")
        sys.exit(1)

    table = Table(title="Sync Summary", show_header=False, border_style="green")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    table.add_row("Properties fetched", str(result.tokko_fetched))
    table.add_row("Mapped to CSV", str(result.mapped_ok))
    table.add_row("Skipped", str(result.skipped))
    table.add_row("Meta upload ID", result.meta_upload_id or "(dry run)")
    table.add_row("Duration", f"{result.duration_seconds:.1f}s")
    console.print(table)
    console.print("[bold green]✓ Done![/]")


def cmd_list_tokko(args: argparse.Namespace) -> None:
    """List properties from Tokko Broker."""
    from tokko_client import TokkoClient

    console.print("[bold]Fetching properties from Tokko Broker …[/]")
    client = TokkoClient()
    props = client.get_properties(operation_type=args.operation)

    if not props:
        console.print("[yellow]No properties found.[/]")
        return

    table = Table(title=f"Tokko Broker Properties ({len(props)} total)")
    table.add_column("ID", style="dim")
    table.add_column("Title")
    table.add_column("Type")
    table.add_column("Price", justify="right")
    table.add_column("Address")
    table.add_column("Photos", justify="center")

    for p in props[:50]:  # show first 50
        ops = p.get("operations") or []
        price_str = ""
        if ops:
            prices = ops[0].get("prices") or []
            if prices:
                price_str = f"{prices[0].get('currency', '')} {prices[0].get('price', '')}"

        ptype = ""
        type_obj = p.get("type") or p.get("property_type")
        if isinstance(type_obj, dict):
            ptype = type_obj.get("name", "")
        elif isinstance(type_obj, str):
            ptype = type_obj

        photos = p.get("photos") or []
        loc = p.get("location") or {}
        address = loc.get("full_location", p.get("address", ""))
        # Truncate long addresses
        if len(address) > 40:
            address = address[:37] + "…"

        table.add_row(
            str(p.get("id", "")),
            (p.get("publication_title") or p.get("address") or "—")[:40],
            ptype,
            price_str,
            address,
            str(len(photos)),
        )

    console.print(table)


def cmd_list_meta(args: argparse.Namespace) -> None:
    """List items in the Meta catalog."""
    from meta_catalog import MetaCatalogManager

    console.print("[bold]Fetching items from Meta Ads catalog …[/]")
    meta = MetaCatalogManager()
    items = meta.get_catalog_items()

    if not items:
        console.print("[yellow]No items in catalog.[/]")
        return

    table = Table(title=f"Meta Catalog Items ({len(items)} total)")
    table.add_column("ID", style="dim")
    table.add_column("Name")
    table.add_column("Price", justify="right")
    table.add_column("Availability")
    table.add_column("URL")

    for item in items:
        table.add_row(
            str(item.get("id", "")),
            (item.get("name") or "—")[:40],
            str(item.get("price", "")),
            item.get("availability", ""),
            (item.get("url") or "—")[:50],
        )

    console.print(table)


# ─── Argument parser ─────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tokko Broker → Meta Ads Home Listing catalog sync",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debug logging"
    )

    subs = parser.add_subparsers(dest="command", required=True)

    # sync
    p_sync = subs.add_parser("sync", help="Run full sync")
    p_sync.add_argument(
        "--dry", action="store_true", help="Generate CSV but skip Meta upload"
    )
    p_sync.add_argument(
        "--operation",
        choices=["sale", "rent", "all"],
        default=None,
        help="Operation type filter (default: from .env)",
    )
    p_sync.set_defaults(func=cmd_sync)

    # list-tokko
    p_lt = subs.add_parser("list-tokko", help="List Tokko Broker properties")
    p_lt.add_argument(
        "--operation",
        choices=["sale", "rent", "all"],
        default=None,
        help="Operation type filter",
    )
    p_lt.set_defaults(func=cmd_list_tokko)

    # list-meta
    p_lm = subs.add_parser("list-meta", help="List Meta catalog items")
    p_lm.set_defaults(func=cmd_list_meta)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    _setup_logging(args.verbose)
    args.func(args)


if __name__ == "__main__":
    main()
