"""
sdqctl refcat - Extract file content with line-level precision.

Usage:
    sdqctl refcat @path/file.py#L10-L50
    sdqctl refcat @path/file.py#L10-L50 --json
    sdqctl refcat @path/file.py#L10 --no-line-numbers
    sdqctl refcat loop:path/file.swift#L100-L200

See proposals/REFCAT-DESIGN.md for full specification.
"""

import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.markdown import Markdown

from ..core.logging import get_logger
from ..core.refcat import (
    AliasNotFoundError,
    ExtractedContent,
    FileNotFoundError,
    InvalidRefError,
    PatternNotFoundError,
    RefcatConfig,
    RefcatError,
    extract_content,
    format_for_context,
    format_for_json,
    parse_ref,
)

logger = get_logger(__name__)
console = Console()


@click.command("refcat")
@click.argument("refs", nargs=-1, required=True)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Output as JSON",
)
@click.option(
    "--no-line-numbers",
    is_flag=True,
    help="Don't prefix lines with line numbers",
)
@click.option(
    "--no-cwd",
    is_flag=True,
    help="Don't include CWD in header",
)
@click.option(
    "--absolute",
    is_flag=True,
    help="Show absolute paths instead of relative",
)
@click.option(
    "--relative-to",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Base directory for relative paths (default: CWD)",
)
@click.option(
    "-q", "--quiet",
    is_flag=True,
    help="Only output content, no headers or formatting",
)
@click.option(
    "--validate-only",
    is_flag=True,
    help="Only validate refs exist, don't output content",
)
def refcat(
    refs: tuple[str, ...],
    json_output: bool,
    no_line_numbers: bool,
    no_cwd: bool,
    absolute: bool,
    relative_to: Optional[Path],
    quiet: bool,
    validate_only: bool,
) -> None:
    """Extract file content with line-level precision.
    
    REFS are file references with optional line ranges:
    
    \b
      @path/file.py              Entire file
      @path/file.py#L10          Single line 10
      @path/file.py#L10-L50      Lines 10 to 50
      @path/file.py#L10-         Line 10 to end of file
      @path/file.py#/pattern/    Find pattern (first match)
      alias:path/file.py#L10     With alias prefix
    
    Examples:
    
    \b
      # Extract specific lines
      sdqctl refcat @sdqctl/core/context.py#L182-L194
      
      # Multiple refs
      sdqctl refcat @file1.py#L10 @file2.py#L20-L30
      
      # JSON output for scripting
      sdqctl refcat @file.py#L10-L50 --json
      
      # Validate refs without output
      sdqctl refcat @file.py#L10-L50 --validate-only
    """
    cwd = relative_to or Path.cwd()
    
    # Build config
    config = RefcatConfig(
        show_line_numbers=not no_line_numbers,
        show_cwd=not no_cwd,
        relative_paths=not absolute,
    )
    
    # Process each ref
    results: list[dict] = []
    errors: list[str] = []
    
    for ref in refs:
        try:
            spec = parse_ref(ref)
            extracted = extract_content(spec, cwd)
            
            if validate_only:
                # Just validate, collect info
                results.append({
                    "ref": ref,
                    "valid": True,
                    "path": str(extracted.path),
                    "lines": f"{extracted.line_start}-{extracted.line_end}",
                })
            else:
                results.append({
                    "ref": ref,
                    "extracted": extracted,
                    "formatted": format_for_context(extracted, config),
                })
                
        except FileNotFoundError as e:
            errors.append(f"Error: {e}")
            if json_output:
                results.append({"ref": ref, "valid": False, "error": str(e)})
        except InvalidRefError as e:
            errors.append(f"Error: {e}")
            if json_output:
                results.append({"ref": ref, "valid": False, "error": str(e)})
        except PatternNotFoundError as e:
            errors.append(f"Error: {e}")
            if json_output:
                results.append({"ref": ref, "valid": False, "error": str(e)})
        except AliasNotFoundError as e:
            errors.append(f"Error: {e}")
            if json_output:
                results.append({"ref": ref, "valid": False, "error": str(e)})
        except RefcatError as e:
            errors.append(f"Error: {e}")
            if json_output:
                results.append({"ref": ref, "valid": False, "error": str(e)})
    
    # Output
    if json_output:
        if validate_only:
            output = {
                "refs": results,
                "valid": len(errors) == 0,
                "errors": errors,
            }
        else:
            output = {
                "refs": [
                    format_for_json(r["extracted"]) if "extracted" in r else r
                    for r in results
                ],
                "errors": errors,
            }
        console.print_json(json.dumps(output, indent=2))
        
    elif validate_only:
        # Validation mode output
        for r in results:
            if r.get("valid"):
                console.print(f"[green]✓[/green] {r['ref']} → {r['path']} ({r['lines']})")
            else:
                console.print(f"[red]✗[/red] {r['ref']}: {r.get('error', 'unknown error')}")
        
        if errors:
            sys.exit(1)
        else:
            console.print(f"\n[green]All {len(results)} ref(s) valid[/green]")
            
    elif quiet:
        # Quiet mode: just content
        for r in results:
            if "extracted" in r:
                print(r["extracted"].content)
                
    else:
        # Normal mode: formatted markdown
        for i, r in enumerate(results):
            if "formatted" in r:
                if i > 0:
                    print()  # Separator between refs
                print(r["formatted"])
    
    # Print errors to stderr
    if errors and not json_output:
        err_console = Console(stderr=True)
        for e in errors:
            err_console.print(f"[red]{e}[/red]")
        sys.exit(1)


# Alias for CLI registration
command = refcat
