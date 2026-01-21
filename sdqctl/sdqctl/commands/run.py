"""
sdqctl run - Execute a single prompt or ConversationFile.

Usage:
    sdqctl run "Audit authentication module"
    sdqctl run workflow.conv
    sdqctl run workflow.conv --adapter copilot --model gpt-4
    sdqctl run workflow.conv --allow-files "./lib/*" --deny-files "./lib/special"
"""

import asyncio
import subprocess
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from ..adapters import get_adapter
from ..adapters.base import AdapterConfig
from ..core.conversation import ConversationFile, FileRestrictions
from ..core.session import Session


def git_commit_checkpoint(
    checkpoint_name: str,
    output_file: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> bool:
    """Commit outputs to git as a checkpoint.
    
    Returns True if commit succeeded, False otherwise.
    """
    try:
        # Check if we're in a git repo
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return False  # Not in a git repo
        
        # Stage output files
        files_to_add = []
        if output_file and output_file.exists():
            files_to_add.append(str(output_file))
        if output_dir and output_dir.exists():
            files_to_add.append(str(output_dir))
        
        if not files_to_add:
            return False  # Nothing to commit
        
        # Add files
        subprocess.run(["git", "add"] + files_to_add, check=True)
        
        # Check if there are staged changes
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            capture_output=True,
        )
        if result.returncode == 0:
            return False  # No changes to commit
        
        # Commit
        commit_msg = f"checkpoint: {checkpoint_name}"
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            check=True,
            capture_output=True,
        )
        return True
        
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False  # git not installed

console = Console()


@click.command("run")
@click.argument("target")
@click.option("--adapter", "-a", default=None, help="AI adapter (copilot, claude, openai, mock)")
@click.option("--model", "-m", default=None, help="Model override")
@click.option("--context", "-c", multiple=True, help="Additional context files")
@click.option("--allow-files", multiple=True, help="Glob pattern for allowed files (can be repeated)")
@click.option("--deny-files", multiple=True, help="Glob pattern for denied files (can be repeated)")
@click.option("--allow-dir", multiple=True, help="Directory to allow (can be repeated)")
@click.option("--deny-dir", multiple=True, help="Directory to deny (can be repeated)")
@click.option("--output", "-o", default=None, help="Output file")
@click.option("--json", "json_output", is_flag=True, help="JSON output")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--dry-run", is_flag=True, help="Show what would happen")
def run(
    target: str,
    adapter: Optional[str],
    model: Optional[str],
    context: tuple[str, ...],
    allow_files: tuple[str, ...],
    deny_files: tuple[str, ...],
    allow_dir: tuple[str, ...],
    deny_dir: tuple[str, ...],
    output: Optional[str],
    json_output: bool,
    verbose: bool,
    dry_run: bool,
) -> None:
    """Execute a single prompt or ConversationFile.
    
    Examples:
    
    \b
    # Run inline prompt
    sdqctl run "Audit authentication module"
    
    \b
    # Run workflow file
    sdqctl run workflow.conv
    
    \b
    # Focus on lib, exclude special module
    sdqctl run "Analyze code" --allow-files "./lib/*" --deny-files "./lib/special"
    
    \b
    # Test-only analysis
    sdqctl run workflow.conv --allow-files "./tests/**" --deny-files "./lib/**"
    """
    asyncio.run(_run_async(
        target, adapter, model, context, 
        allow_files, deny_files, allow_dir, deny_dir,
        output, json_output, verbose, dry_run
    ))


async def _run_async(
    target: str,
    adapter_name: Optional[str],
    model: Optional[str],
    extra_context: tuple[str, ...],
    allow_files: tuple[str, ...],
    deny_files: tuple[str, ...],
    allow_dir: tuple[str, ...],
    deny_dir: tuple[str, ...],
    output_file: Optional[str],
    json_output: bool,
    verbose: bool,
    dry_run: bool,
) -> None:
    """Async implementation of run command."""

    # Determine if target is a file or inline prompt
    target_path = Path(target)
    if target_path.exists() and target_path.suffix in (".conv", ".copilot"):
        # Load ConversationFile
        conv = ConversationFile.from_file(target_path)
        if verbose:
            console.print(f"[blue]Loaded workflow from {target_path}[/blue]")
    else:
        # Treat as inline prompt
        conv = ConversationFile(
            prompts=[target],
            adapter=adapter_name or "mock",
            model=model or "gpt-4",
        )
        if verbose:
            console.print("[blue]Running inline prompt[/blue]")

    # Apply overrides
    if adapter_name:
        conv.adapter = adapter_name
    if model:
        conv.model = model

    # Add extra context files
    for ctx in extra_context:
        conv.context_files.append(f"@{ctx}")

    # Apply CLI file restrictions (merge with file-defined ones)
    cli_restrictions = FileRestrictions(
        allow_patterns=list(allow_files),
        deny_patterns=list(deny_files),
        allow_dirs=list(allow_dir),
        deny_dirs=list(deny_dir),
    )
    
    # Merge: CLI allow patterns replace file patterns, CLI deny patterns add to file patterns
    if allow_files or deny_files or allow_dir or deny_dir:
        conv.file_restrictions = conv.file_restrictions.merge_with_cli(
            list(allow_files) + list(f"{d}/**" for d in allow_dir),
            list(deny_files) + list(f"{d}/**" for d in deny_dir),
        )
        if verbose:
            console.print(f"[blue]File restrictions: allow={conv.file_restrictions.allow_patterns}, deny={conv.file_restrictions.deny_patterns}[/blue]")

    # Override output
    if output_file:
        conv.output_file = output_file

    # Create session
    session = Session(conv)

    # Show status
    if verbose or dry_run:
        status = session.get_status()
        restrictions_info = ""
        if conv.file_restrictions.allow_patterns or conv.file_restrictions.deny_patterns:
            restrictions_info = f"\nAllow patterns: {conv.file_restrictions.allow_patterns}\nDeny patterns: {conv.file_restrictions.deny_patterns}"
        
        console.print(Panel.fit(
            f"Adapter: {conv.adapter}\n"
            f"Model: {conv.model}\n"
            f"Mode: {conv.mode}\n"
            f"Prompts: {len(conv.prompts)}\n"
            f"Context files: {len(conv.context_files)}\n"
            f"Context loaded: {status['context']['files_loaded']} files"
            f"{restrictions_info}",
            title="Workflow Configuration"
        ))

    if dry_run:
        console.print("\n[yellow]Dry run - no execution[/yellow]")
        
        # Show prompts
        for i, prompt in enumerate(conv.prompts, 1):
            console.print(f"\n[bold]Prompt {i}:[/bold]")
            console.print(prompt[:200] + ("..." if len(prompt) > 200 else ""))
        
        return

    # Get adapter
    try:
        ai_adapter = get_adapter(conv.adapter)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[yellow]Using mock adapter instead[/yellow]")
        ai_adapter = get_adapter("mock")

    # Run workflow
    try:
        await ai_adapter.start()

        # Create adapter session
        adapter_session = await ai_adapter.create_session(
            AdapterConfig(
                model=conv.model,
                streaming=True,
            )
        )

        session.state.status = "running"
        responses = []

        # Include context in first prompt
        context_content = session.context.get_context_content()

        # Build pause point lookup: {prompt_index: message}
        pause_after = {idx: msg for idx, msg in conv.pause_points}

        # Process steps (includes prompts, checkpoints, compact, etc.)
        # Fall back to prompts list if no steps defined (backward compat)
        prompt_count = 0
        total_prompts = len(conv.prompts)
        first_prompt = True
        
        steps_to_process = conv.steps if conv.steps else [
            {"type": "prompt", "content": p} for p in conv.prompts
        ]
        
        for step in steps_to_process:
            step_type = step.type if hasattr(step, 'type') else step.get('type')
            step_content = step.content if hasattr(step, 'content') else step.get('content', '')
            
            if step_type == "prompt":
                prompt = step_content
                prompt_count += 1
                
                if verbose:
                    console.print(f"\n[bold blue]Sending prompt {prompt_count}/{total_prompts}...[/bold blue]")

                # Add context to first prompt
                full_prompt = prompt
                if first_prompt and context_content:
                    full_prompt = f"{context_content}\n\n{prompt}"
                    first_prompt = False

                # Stream response
                if verbose:
                    console.print("[dim]Response:[/dim]")

                def on_chunk(chunk: str) -> None:
                    if verbose and not json_output:
                        console.print(chunk, end="")

                response = await ai_adapter.send(adapter_session, full_prompt, on_chunk=on_chunk)

                if verbose:
                    console.print()  # Newline after streaming

                responses.append(response)
                session.add_message("user", prompt)
                session.add_message("assistant", response)

                # Check for PAUSE after this prompt
                prompt_idx = prompt_count - 1
                if prompt_idx in pause_after:
                    pause_msg = pause_after[prompt_idx]
                    session.state.prompt_index = prompt_count  # Next prompt to resume from
                    checkpoint_path = session.save_pause_checkpoint(pause_msg)
                    
                    await ai_adapter.destroy_session(adapter_session)
                    await ai_adapter.stop()
                    
                    console.print(f"\n[yellow]⏸  PAUSED: {pause_msg}[/yellow]")
                    console.print(f"[dim]Checkpoint saved: {checkpoint_path}[/dim]")
                    console.print(f"\n[bold]To resume:[/bold] sdqctl resume {checkpoint_path}")
                    return
            
            elif step_type == "checkpoint":
                # Save session state and commit outputs to git
                checkpoint_name = step_content or f"checkpoint-{len(session.state.checkpoints) + 1}"
                
                if verbose:
                    console.print(f"\n[bold yellow]📌 CHECKPOINT: {checkpoint_name}[/bold yellow]")
                
                # Write current output to file if configured
                if conv.output_file and responses:
                    current_output = "\n\n---\n\n".join(responses)
                    output_path = Path(conv.output_file)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_text(current_output)
                    if verbose:
                        console.print(f"[dim]Output written to {output_path}[/dim]")
                
                # Save session checkpoint
                checkpoint = session.create_checkpoint(checkpoint_name)
                
                # Commit to git
                output_path = Path(conv.output_file) if conv.output_file else None
                output_dir = Path(conv.output_dir) if conv.output_dir else None
                
                if git_commit_checkpoint(checkpoint_name, output_path, output_dir):
                    console.print(f"[green]✓ Git commit: checkpoint: {checkpoint_name}[/green]")
                elif verbose:
                    console.print("[dim]No git changes to commit[/dim]")
            
            elif step_type == "compact":
                # Request compaction from the AI
                if verbose:
                    console.print("\n[bold magenta]🗜  COMPACTING conversation...[/bold magenta]")
                
                preserve = step.preserve if hasattr(step, 'preserve') else []
                compact_prompt = session.get_compaction_prompt()
                if preserve:
                    compact_prompt = f"Preserve these items: {', '.join(preserve)}\n\n{compact_prompt}"
                
                response = await ai_adapter.send(adapter_session, compact_prompt)
                session.add_message("system", f"[Compaction summary]\n{response}")
                
                if verbose:
                    console.print("[dim]Conversation compacted[/dim]")
            
            elif step_type == "new_conversation":
                # End current session, start fresh
                if verbose:
                    console.print("\n[bold cyan]🔄 Starting new conversation...[/bold cyan]")
                
                await ai_adapter.destroy_session(adapter_session)
                adapter_session = await ai_adapter.create_session(
                    AdapterConfig(model=conv.model, streaming=True)
                )
                first_prompt = True  # Re-include context in next prompt
                
                if verbose:
                    console.print("[dim]New session created[/dim]")

        # Cleanup
        await ai_adapter.destroy_session(adapter_session)
        session.state.status = "completed"

        # Output
        final_output = "\n\n---\n\n".join(responses)

        if json_output:
            import json
            result = {
                "status": "completed",
                "prompts": len(conv.prompts),
                "responses": responses,
                "session": session.to_dict(),
            }
            console.print_json(json.dumps(result))
        else:
            if output_file:
                Path(output_file).write_text(final_output)
                console.print(f"\n[green]Output written to {output_file}[/green]")
            else:
                console.print("\n" + "=" * 60)
                console.print(Markdown(final_output))

    except Exception as e:
        session.state.status = "failed"
        console.print(f"[red]Error: {e}[/red]")
        raise

    finally:
        await ai_adapter.stop()
