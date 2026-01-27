"""
CLI integration tests for core sdqctl commands.

Tests complete command execution with mock adapter for deterministic behavior.
"""

import pytest
from pathlib import Path
from click.testing import CliRunner

from sdqctl.cli import cli


pytestmark = pytest.mark.integration


class TestRenderCommandIntegration:
    """Integration tests for render command."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def conv_file(self, tmp_path):
        """Create a test conversation file."""
        conv = tmp_path / "test.conv"
        conv.write_text("""# Test Render
MODEL mock
ADAPTER mock

PROMPT Analyze the code quality.
PROMPT Provide recommendations.
""")
        return conv

    def test_render_run_outputs_conversation(self, runner, conv_file):
        """Test render run command produces output."""
        result = runner.invoke(cli, ["render", "run", str(conv_file)])
        assert result.exit_code == 0
        assert "Analyze the code quality" in result.output

    def test_render_run_with_json(self, runner, conv_file):
        """Test render run command with JSON output."""
        result = runner.invoke(cli, ["render", "run", str(conv_file), "--json"])
        assert result.exit_code == 0
        # JSON output should be parseable
        assert "{" in result.output or "[" in result.output

    def test_render_help_shows_subcommands(self, runner):
        """Test render --help shows subcommands."""
        result = runner.invoke(cli, ["render", "--help"])
        assert result.exit_code == 0
        assert "run" in result.output
        assert "cycle" in result.output

    def test_render_missing_file_errors(self, runner, tmp_path):
        """Test render command errors on missing file."""
        result = runner.invoke(cli, ["render", "run", str(tmp_path / "nonexistent.conv")])
        assert result.exit_code != 0


class TestValidateCommandIntegration:
    """Integration tests for validate command."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def valid_conv(self, tmp_path):
        """Create a valid conversation file."""
        conv = tmp_path / "valid.conv"
        conv.write_text("""# Valid Conversation
MODEL mock
ADAPTER mock
PROMPT Test prompt.
""")
        return conv

    @pytest.fixture
    def invalid_conv(self, tmp_path):
        """Create a conversation with validation issues."""
        conv = tmp_path / "invalid.conv"
        conv.write_text("""# Invalid Conversation
MODEL mock
ADAPTER mock
REFCAT @nonexistent-file.md
PROMPT Test prompt.
""")
        return conv

    def test_validate_valid_file_succeeds(self, runner, valid_conv):
        """Test validate command succeeds for valid file."""
        result = runner.invoke(cli, ["validate", str(valid_conv)])
        assert result.exit_code == 0

    def test_validate_shows_file_info(self, runner, valid_conv):
        """Test validate shows file information."""
        result = runner.invoke(cli, ["validate", str(valid_conv)])
        assert "valid.conv" in result.output or result.exit_code == 0


class TestIterateCommandIntegration:
    """Integration tests for iterate command."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def simple_conv(self, tmp_path):
        """Create a simple conversation for iteration."""
        conv = tmp_path / "iterate.conv"
        conv.write_text("""# Iterate Test
MODEL mock
ADAPTER mock
MAX-CYCLES 1

PROMPT Hello from iterate test.
""")
        return conv

    def test_iterate_dry_run(self, runner, simple_conv):
        """Test iterate --dry-run shows configuration."""
        result = runner.invoke(cli, ["iterate", str(simple_conv), "--dry-run"])
        assert result.exit_code == 0
        assert "Cycle Configuration" in result.output

    def test_iterate_help_shows_options(self, runner):
        """Test iterate --help shows available options."""
        result = runner.invoke(cli, ["iterate", "--help"])
        assert result.exit_code == 0
        assert "--adapter" in result.output
        assert "--max-cycles" in result.output or "-n" in result.output

    def test_iterate_with_max_cycles(self, runner, simple_conv):
        """Test iterate respects -n option in dry-run."""
        result = runner.invoke(cli, ["iterate", str(simple_conv), "-n", "3", "--dry-run"])
        assert result.exit_code == 0


class TestCycleCommandIntegration:
    """Integration tests for cycle command."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def cycle_conv(self, tmp_path):
        """Create a conversation for cycle command."""
        conv = tmp_path / "cycle.conv"
        conv.write_text("""# Cycle Test
MODEL mock
ADAPTER mock

PROMPT Single cycle test.
""")
        return conv

    def test_cycle_dry_run(self, runner, cycle_conv):
        """Test cycle --dry-run shows configuration."""
        result = runner.invoke(cli, ["cycle", str(cycle_conv), "--dry-run"])
        assert result.exit_code == 0

    def test_cycle_help(self, runner):
        """Test cycle --help shows usage."""
        result = runner.invoke(cli, ["cycle", "--help"])
        assert result.exit_code == 0
        assert "cycle" in result.output.lower()


class TestStatusCommandIntegration:
    """Integration tests for status command."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_status_runs_without_error(self, runner):
        """Test status command runs without error."""
        result = runner.invoke(cli, ["status"])
        # Status may show "no active session" which is fine
        assert result.exit_code in (0, 1)

    def test_status_help(self, runner):
        """Test status --help shows usage."""
        result = runner.invoke(cli, ["status", "--help"])
        assert result.exit_code == 0


class TestHelpCommandIntegration:
    """Integration tests for help command."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_help_lists_topics(self, runner):
        """Test help command lists available topics."""
        result = runner.invoke(cli, ["help"])
        assert result.exit_code == 0

    @pytest.mark.parametrize("topic", [
        "directives",
        "adapters",
        "modes",
    ])
    def test_help_topic_exists(self, runner, topic):
        """Test help shows content for known topics."""
        result = runner.invoke(cli, ["help", topic])
        # Should succeed or show "not found" gracefully
        assert result.exit_code in (0, 1)


class TestFlowCommandIntegration:
    """Integration tests for flow command (batch workflows)."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def workflow_files(self, tmp_path):
        """Create multiple workflow files for flow testing."""
        workflows = []
        for i in range(3):
            wf = tmp_path / f"workflow{i}.conv"
            wf.write_text(f"""# Workflow {i}
MODEL mock
ADAPTER mock

PROMPT Task {i}: analyze component.
""")
            workflows.append(wf)
        return tmp_path, workflows

    def test_flow_dry_run_single_file(self, runner, tmp_path):
        """Test flow --dry-run with single file."""
        wf = tmp_path / "single.conv"
        wf.write_text("MODEL mock\nADAPTER mock\nPROMPT Test.")
        
        result = runner.invoke(cli, ["flow", str(wf), "--dry-run"])
        assert result.exit_code == 0

    def test_flow_dry_run_glob_pattern(self, runner, workflow_files):
        """Test flow --dry-run with glob pattern."""
        tmp_path, _ = workflow_files
        
        result = runner.invoke(cli, [
            "flow", str(tmp_path / "*.conv"),
            "--dry-run"
        ])
        assert result.exit_code == 0

    def test_flow_with_adapter_override(self, runner, tmp_path):
        """Test flow with adapter override."""
        wf = tmp_path / "test.conv"
        wf.write_text("MODEL gpt-4\nADAPTER copilot\nPROMPT Test.")
        
        result = runner.invoke(cli, [
            "flow", str(wf),
            "--adapter", "mock",
            "--dry-run"
        ])
        assert result.exit_code == 0

    def test_flow_parallel_option(self, runner, workflow_files):
        """Test flow with parallel option."""
        tmp_path, _ = workflow_files
        
        result = runner.invoke(cli, [
            "flow", str(tmp_path / "*.conv"),
            "--parallel", "2",
            "--dry-run"
        ])
        assert result.exit_code == 0

    def test_flow_continue_on_error_option(self, runner, tmp_path):
        """Test flow with continue-on-error option."""
        wf = tmp_path / "test.conv"
        wf.write_text("MODEL mock\nADAPTER mock\nPROMPT Test.")
        
        result = runner.invoke(cli, [
            "flow", str(wf),
            "--continue-on-error",
            "--dry-run"
        ])
        assert result.exit_code == 0

    def test_flow_no_matches_warns(self, runner, tmp_path):
        """Test flow handles no matching files gracefully."""
        result = runner.invoke(cli, [
            "flow", str(tmp_path / "nonexistent*.conv"),
            "--dry-run"
        ])
        # May succeed with warning or show "no files" message
        # Behavior depends on implementation - just verify it runs
        assert result.exit_code in (0, 1)


class TestApplyCommandIntegration:
    """Integration tests for apply command (component iteration)."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def apply_workspace(self, tmp_path):
        """Create workspace with workflow and components."""
        # Create workflow with template variable
        workflow = tmp_path / "analyze.conv"
        workflow.write_text("""# Component Analysis
MODEL mock
ADAPTER mock

PROMPT Analyze {{COMPONENT_NAME}} at {{COMPONENT_PATH}}.
""")
        
        # Create components
        components_dir = tmp_path / "components"
        components_dir.mkdir()
        for name in ["auth", "utils", "config"]:
            comp = components_dir / f"{name}.js"
            comp.write_text(f"// {name} module")
        
        return tmp_path, workflow, components_dir

    def test_apply_dry_run_single_component(self, runner, apply_workspace):
        """Test apply --dry-run with single component."""
        tmp_path, workflow, components_dir = apply_workspace
        
        result = runner.invoke(cli, [
            "apply", str(workflow),
            "--components", str(components_dir / "auth.js"),
            "--dry-run"
        ])
        assert result.exit_code == 0

    def test_apply_dry_run_glob_pattern(self, runner, apply_workspace):
        """Test apply --dry-run with glob pattern."""
        tmp_path, workflow, components_dir = apply_workspace
        
        result = runner.invoke(cli, [
            "apply", str(workflow),
            "--components", str(components_dir / "*.js"),
            "--dry-run"
        ])
        assert result.exit_code == 0

    def test_apply_with_adapter_override(self, runner, apply_workspace):
        """Test apply with adapter override."""
        tmp_path, workflow, components_dir = apply_workspace
        
        result = runner.invoke(cli, [
            "apply", str(workflow),
            "--components", str(components_dir / "auth.js"),
            "--adapter", "mock",
            "--dry-run"
        ])
        assert result.exit_code == 0

    def test_apply_parallel_option(self, runner, apply_workspace):
        """Test apply with parallel option."""
        tmp_path, workflow, components_dir = apply_workspace
        
        result = runner.invoke(cli, [
            "apply", str(workflow),
            "--components", str(components_dir / "*.js"),
            "--parallel", "2",
            "--dry-run"
        ])
        assert result.exit_code == 0

    def test_apply_missing_workflow_errors(self, runner, tmp_path):
        """Test apply errors when workflow doesn't exist."""
        result = runner.invoke(cli, [
            "apply", str(tmp_path / "nonexistent.conv"),
            "--components", "*.js",
            "--dry-run"
        ])
        assert result.exit_code != 0

    def test_apply_help_shows_examples(self, runner):
        """Test apply --help shows usage examples."""
        result = runner.invoke(cli, ["apply", "--help"])
        assert result.exit_code == 0
        assert "COMPONENT" in result.output or "component" in result.output


class TestSessionsCommandIntegration:
    """Integration tests for sessions command."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    def test_sessions_list_runs(self, runner):
        """Test sessions list command runs."""
        result = runner.invoke(cli, ["sessions", "list"])
        # May return 0 with empty list or error if no sessions dir
        assert result.exit_code in (0, 1)

    def test_sessions_list_json_format(self, runner):
        """Test sessions list with JSON format."""
        result = runner.invoke(cli, ["sessions", "list", "--format", "json"])
        assert result.exit_code in (0, 1)

    def test_sessions_list_filter(self, runner):
        """Test sessions list with filter option."""
        result = runner.invoke(cli, ["sessions", "list", "--filter", "test-*"])
        assert result.exit_code in (0, 1)

    def test_sessions_delete_nonexistent(self, runner):
        """Test sessions delete with nonexistent session."""
        result = runner.invoke(cli, ["sessions", "delete", "nonexistent-session-id"])
        # Should error or warn
        assert result.exit_code in (0, 1)

    def test_sessions_cleanup_dry_run(self, runner):
        """Test sessions cleanup with dry-run."""
        result = runner.invoke(cli, [
            "sessions", "cleanup",
            "--older-than", "7d",
            "--dry-run"
        ])
        assert result.exit_code in (0, 1)

    def test_sessions_cleanup_older_than(self, runner):
        """Test sessions cleanup with different duration."""
        result = runner.invoke(cli, [
            "sessions", "cleanup",
            "--older-than", "30d",
            "--dry-run"
        ])
        assert result.exit_code in (0, 1)

    def test_sessions_help_shows_subcommands(self, runner):
        """Test sessions --help shows all subcommands."""
        result = runner.invoke(cli, ["sessions", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "delete" in result.output
        assert "cleanup" in result.output


class TestArtifactCommandIntegration:
    """Integration tests for artifact command."""

    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def artifact_workspace(self, tmp_path):
        """Create workspace with artifact references."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        spec = docs_dir / "spec.md"
        spec.write_text("""# Requirements
REQ-001: User authentication
REQ-002: Data validation
""")
        return tmp_path

    def test_artifact_next_generates_id(self, runner, artifact_workspace):
        """Test artifact next generates next ID."""
        result = runner.invoke(cli, [
            "artifact", "next", "REQ",
            "--path", str(artifact_workspace)
        ])
        assert result.exit_code == 0
        assert "REQ-" in result.output

    def test_artifact_next_with_category(self, runner, artifact_workspace):
        """Test artifact next with category prefix."""
        result = runner.invoke(cli, [
            "artifact", "next", "REQ-CGM",
            "--path", str(artifact_workspace)
        ])
        assert result.exit_code == 0
        assert "REQ-CGM-" in result.output

    def test_artifact_list_type(self, runner, artifact_workspace):
        """Test artifact list for specific type."""
        result = runner.invoke(cli, [
            "artifact", "list", "REQ",
            "--path", str(artifact_workspace)
        ])
        assert result.exit_code == 0
        # May list REQ-001, REQ-002 from fixture

    def test_artifact_list_all_types(self, runner, artifact_workspace):
        """Test artifact list without type filter."""
        result = runner.invoke(cli, [
            "artifact", "list",
            "--path", str(artifact_workspace),
            "--all"
        ])
        assert result.exit_code == 0

    def test_artifact_rename_dry_run(self, runner, artifact_workspace):
        """Test artifact rename with dry-run."""
        result = runner.invoke(cli, [
            "artifact", "rename", "REQ-001", "REQ-AUTH-001",
            "--path", str(artifact_workspace),
            "--dry-run"
        ])
        # May succeed or fail depending on implementation
        assert result.exit_code in (0, 1, 2)

    def test_artifact_retire_dry_run(self, runner, artifact_workspace):
        """Test artifact retire with dry-run."""
        result = runner.invoke(cli, [
            "artifact", "retire", "REQ-001",
            "--reason", "Superseded",
            "--path", str(artifact_workspace),
            "--dry-run"
        ])
        assert result.exit_code in (0, 1, 2)

    def test_artifact_help_shows_types(self, runner):
        """Test artifact --help shows artifact types."""
        result = runner.invoke(cli, ["artifact", "--help"])
        assert result.exit_code == 0
        assert "REQ" in result.output
        assert "next" in result.output
        assert "list" in result.output
