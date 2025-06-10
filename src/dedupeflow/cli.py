"""Modern CLI interface using Typer."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd
import typer
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

from dedupeflow.core.engine import DedupeEngine
from dedupeflow.models import DedupeConfig

app = typer.Typer(
    name="dedupeflow",
    help="A modern data deduplication and record linkage tool.",
    add_completion=False,
)
console = Console()


@app.command()
def dedupe(
    input_file: Path = typer.Argument(..., help="Input CSV file to deduplicate"),
    config_file: Path = typer.Argument(..., help="JSON configuration file"),
    output_file: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output file for results"
    ),
    id_column: str = typer.Option(
        "id", "--id-col", help="Column name containing record IDs"
    ),
    format: str = typer.Option(
        "json", "--format", "-f", help="Output format (json, csv)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
) -> None:
    """Deduplicate records in a CSV file."""

    if verbose:
        console.print(f"Loading data from {input_file}")

    # Load data
    try:
        data = pd.read_csv(input_file)
    except Exception as e:
        console.print(f"[red]Error loading data: {e}[/red]")
        raise typer.Exit(1)

    # Load configuration
    try:
        with open(config_file) as f:
            config_data = json.load(f)
        config = DedupeConfig(**config_data)
    except Exception as e:
        console.print(f"[red]Error loading config: {e}[/red]")
        raise typer.Exit(1)

    # Create engine and run deduplication
    engine = DedupeEngine(config)

    def progress_callback(current: int, total: int) -> None:
        if verbose:
            console.print(f"Processed {current}/{total} comparisons")

    with Progress() as progress:
        task = progress.add_task("Deduplicating...", total=len(data))

        try:
            results = engine.deduplicate(
                data,
                id_column=id_column,
                progress_callback=progress_callback if verbose else None,
            )
        except Exception as e:
            console.print(f"[red]Error during deduplication: {e}[/red]")
            raise typer.Exit(1)

    # Display results summary
    console.print(f"\n[green]Deduplication completed![/green]")
    console.print(f"Total comparisons: {results.total_comparisons}")
    console.print(f"Matches found: {results.total_matches}")
    console.print(f"Execution time: {results.execution_time_seconds:.2f}s")

    # Output results
    if output_file:
        if format == "json":
            with open(output_file, "w") as f:
                json.dump(results.dict(), f, indent=2, default=str)
        elif format == "csv":
            matches_df = pd.DataFrame([match.dict() for match in results.matches])
            matches_df.to_csv(output_file, index=False)

        console.print(f"Results saved to {output_file}")
    else:
        # Display results table
        table = Table(title="Top Matches")
        table.add_column("Record 1")
        table.add_column("Record 2")
        table.add_column("Score")
        table.add_column("Confidence")

        for match in results.matches[:10]:  # Show top 10
            table.add_row(
                str(match.record1_id),
                str(match.record2_id),
                f"{match.overall_score:.3f}",
                f"{match.confidence:.3f}",
            )

        console.print(table)


@app.command()
def validate_config(
    config_file: Path = typer.Argument(..., help="Configuration file to validate")
) -> None:
    """Validate a configuration file."""
    try:
        with open(config_file) as f:
            config_data = json.load(f)

        config = DedupeConfig(**config_data)
        console.print("[green]✓ Configuration is valid![/green]")

        # Display config summary
        table = Table(title="Configuration Summary")
        table.add_column("Field")
        table.add_column("Type")
        table.add_column("Weight")
        table.add_column("Method")

        for field in config.fields:
            table.add_row(
                field.name,
                field.comparator.value,
                str(field.weight),
                field.method or "default",
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]✗ Configuration is invalid: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def generate_config(
    csv_file: Path = typer.Argument(..., help="CSV file to analyze"),
    output_file: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output configuration file"
    ),
) -> None:
    """Generate a sample configuration from a CSV file."""
    try:
        data = pd.read_csv(csv_file)

        # Auto-detect field types and generate config
        fields = []
        for column in data.columns:
            if column.lower() == "id":
                continue

            # Simple type detection
            sample_values = data[column].dropna().head(10)

            if pd.api.types.is_numeric_dtype(data[column]):
                comparator = "numeric"
                method = "threshold"
            elif pd.api.types.is_datetime64_any_dtype(data[column]):
                comparator = "date"
                method = "exact"
            else:
                comparator = "string"
                method = "levenshtein"

            fields.append(
                {
                    "name": column,
                    "comparator": comparator,
                    "weight": 1.0,
                    "method": method,
                    "required": True,
                }
            )

        config = {
            "fields": fields,
            "global_threshold": 0.8,
            "require_all_fields": False,
            "enable_blocking": True,
            "blocking_keys": [fields[0]["name"]] if fields else [],
        }

        if output_file:
            with open(output_file, "w") as f:
                json.dump(config, f, indent=2)
            console.print(f"Configuration saved to {output_file}")
        else:
            console.print(json.dumps(config, indent=2))

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
