"""Tests for custom directive execution hooks (DIR-003)."""

import pytest
from pathlib import Path

from sdqctl.plugins import (
    DirectiveExecutionContext,
    DirectiveExecutionResult,
    register_directive_hook,
    unregister_directive_hook,
    get_directive_hook,
    has_directive_hook,
    clear_directive_hooks,
    execute_custom_directive,
)


@pytest.fixture(autouse=True)
def clean_hooks():
    """Clear directive hooks before and after each test."""
    clear_directive_hooks()
    yield
    clear_directive_hooks()


class TestDirectiveExecutionContext:
    """Tests for DirectiveExecutionContext."""

    def test_context_creation(self, tmp_path):
        """Context stores directive info."""
        ctx = DirectiveExecutionContext(
            workspace_root=tmp_path,
            directive_name="HYGIENE",
            directive_value="queue-stats",
            line_number=10,
        )
        assert ctx.workspace_root == tmp_path
        assert ctx.directive_name == "HYGIENE"
        assert ctx.directive_value == "queue-stats"
        assert ctx.line_number == 10

    def test_context_emit(self, tmp_path):
        """emit() accumulates output."""
        ctx = DirectiveExecutionContext(
            workspace_root=tmp_path,
            directive_name="TEST",
            directive_value="",
            line_number=1,
        )
        ctx.emit("line 1")
        ctx.emit("line 2")
        assert ctx.output == "line 1\nline 2"

    def test_context_error(self, tmp_path):
        """error() accumulates errors."""
        ctx = DirectiveExecutionContext(
            workspace_root=tmp_path,
            directive_name="TEST",
            directive_value="",
            line_number=1,
        )
        ctx.error("error 1")
        ctx.error("error 2")
        assert ctx.errors == ["error 1", "error 2"]
        assert ctx.has_errors

    def test_context_optional_fields(self, tmp_path):
        """Optional session fields have defaults."""
        ctx = DirectiveExecutionContext(
            workspace_root=tmp_path,
            directive_name="TEST",
            directive_value="",
            line_number=1,
        )
        assert ctx.session_id is None
        assert ctx.cycle_number == 1
        assert ctx.inject_output is True


class TestDirectiveExecutionResult:
    """Tests for DirectiveExecutionResult."""

    def test_ok_result(self):
        """ok() creates successful result."""
        result = DirectiveExecutionResult.ok(output="hello")
        assert result.success is True
        assert result.output == "hello"
        assert result.errors == []

    def test_fail_result(self):
        """fail() creates failed result."""
        result = DirectiveExecutionResult.fail(["error 1", "error 2"])
        assert result.success is False
        assert result.errors == ["error 1", "error 2"]

    def test_result_inject_flag(self):
        """Result controls prompt injection."""
        result = DirectiveExecutionResult.ok(output="x", inject=False)
        assert result.inject_into_prompt is False


class TestHookRegistration:
    """Tests for hook registration functions."""

    def test_register_and_get_hook(self):
        """Hooks can be registered and retrieved."""
        def my_hook(ctx):
            return DirectiveExecutionResult.ok()
        
        register_directive_hook("CUSTOM", my_hook)
        assert get_directive_hook("CUSTOM") is my_hook
        assert get_directive_hook("custom") is my_hook  # Case insensitive

    def test_has_directive_hook(self):
        """has_directive_hook checks registration."""
        assert not has_directive_hook("MISSING")
        
        register_directive_hook("EXISTS", lambda ctx: DirectiveExecutionResult.ok())
        assert has_directive_hook("EXISTS")
        assert has_directive_hook("exists")

    def test_unregister_hook(self):
        """Hooks can be unregistered."""
        register_directive_hook("TEMP", lambda ctx: DirectiveExecutionResult.ok())
        assert has_directive_hook("TEMP")
        
        unregister_directive_hook("TEMP")
        assert not has_directive_hook("TEMP")

    def test_clear_hooks(self):
        """clear_directive_hooks removes all hooks."""
        register_directive_hook("A", lambda ctx: DirectiveExecutionResult.ok())
        register_directive_hook("B", lambda ctx: DirectiveExecutionResult.ok())
        
        clear_directive_hooks()
        assert not has_directive_hook("A")
        assert not has_directive_hook("B")


class TestExecuteCustomDirective:
    """Tests for execute_custom_directive function."""

    def test_execute_registered_hook(self, tmp_path):
        """Executes registered hook with context."""
        def my_hook(ctx):
            return DirectiveExecutionResult.ok(
                output=f"Ran {ctx.directive_name}: {ctx.directive_value}"
            )
        
        register_directive_hook("ECHO", my_hook)
        result = execute_custom_directive(
            "ECHO", "hello world", tmp_path, line_number=5
        )
        
        assert result.success
        assert result.output == "Ran ECHO: hello world"

    def test_execute_missing_hook(self, tmp_path):
        """Returns error for unregistered directive."""
        result = execute_custom_directive("UNKNOWN", "value", tmp_path)
        
        assert not result.success
        assert "No execution hook registered" in result.errors[0]

    def test_execute_hook_exception(self, tmp_path):
        """Catches hook exceptions."""
        def bad_hook(ctx):
            raise ValueError("Hook crashed!")
        
        register_directive_hook("BAD", bad_hook)
        result = execute_custom_directive("BAD", "value", tmp_path)
        
        assert not result.success
        assert "Hook execution error" in result.errors[0]
        assert "Hook crashed!" in result.errors[0]

    def test_execute_with_session_context(self, tmp_path):
        """Session context is passed to hook."""
        received_ctx = {}
        
        def capture_hook(ctx):
            received_ctx["session_id"] = ctx.session_id
            received_ctx["cycle"] = ctx.cycle_number
            return DirectiveExecutionResult.ok()
        
        register_directive_hook("CAPTURE", capture_hook)
        execute_custom_directive(
            "CAPTURE", "val", tmp_path,
            session_id="sess-123",
            cycle_number=5,
        )
        
        assert received_ctx["session_id"] == "sess-123"
        assert received_ctx["cycle"] == 5


class TestHookIntegration:
    """Integration tests for hook system."""

    def test_multiple_hooks_coexist(self, tmp_path):
        """Multiple directive types can have hooks."""
        register_directive_hook("TYPE_A", lambda ctx: DirectiveExecutionResult.ok("A"))
        register_directive_hook("TYPE_B", lambda ctx: DirectiveExecutionResult.ok("B"))
        
        result_a = execute_custom_directive("TYPE_A", "", tmp_path)
        result_b = execute_custom_directive("TYPE_B", "", tmp_path)
        
        assert result_a.output == "A"
        assert result_b.output == "B"

    def test_hook_with_emit_pattern(self, tmp_path):
        """Hook using emit pattern for output."""
        def verbose_hook(ctx):
            ctx.emit(f"Starting {ctx.directive_name}")
            ctx.emit(f"Value: {ctx.directive_value}")
            ctx.emit("Done")
            return DirectiveExecutionResult.ok(output=ctx.output)
        
        register_directive_hook("VERBOSE", verbose_hook)
        result = execute_custom_directive("VERBOSE", "test", tmp_path)
        
        assert "Starting VERBOSE" in result.output
        assert "Value: test" in result.output
        assert "Done" in result.output
