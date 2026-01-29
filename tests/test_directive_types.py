"""Tests for custom directive type registration (DIR-002)."""

import pytest

from sdqctl.core.conversation.types import (
    Directive,
    DirectiveType,
    clear_custom_directives,
    get_custom_directives,
    is_custom_directive,
    register_custom_directive,
    unregister_custom_directive,
)


@pytest.fixture(autouse=True)
def clean_registry():
    """Clear custom directive registry before and after each test."""
    clear_custom_directives()
    yield
    clear_custom_directives()


class TestBuiltinDirectives:
    """Tests for built-in DirectiveType enum directives."""

    def test_directive_with_enum_type(self):
        """Built-in directives use DirectiveType enum."""
        d = Directive(
            type=DirectiveType.MODEL,
            value="gpt-4",
            line_number=1,
            raw_line="MODEL gpt-4",
        )
        assert d.type == DirectiveType.MODEL
        assert d.type_name == "MODEL"
        assert d.is_custom is False

    def test_directive_type_name_returns_enum_value(self):
        """type_name property returns the enum's string value."""
        d = Directive(
            type=DirectiveType.VERIFY,
            value="refs",
            line_number=5,
            raw_line="VERIFY refs",
        )
        assert d.type_name == "VERIFY"


class TestCustomDirectives:
    """Tests for plugin-defined custom directive types."""

    def test_directive_with_string_type(self):
        """Custom directives can use string type."""
        d = Directive(
            type="HYGIENE",
            value="queue-stats",
            line_number=10,
            raw_line="HYGIENE queue-stats",
        )
        assert d.type == "HYGIENE"
        assert d.type_name == "HYGIENE"
        assert d.is_custom is True

    def test_register_custom_directive(self):
        """Custom directives can be registered."""
        register_custom_directive("TRACE", {"handler": "trace-check.sh"})
        assert is_custom_directive("TRACE")
        assert is_custom_directive("trace")  # Case insensitive

    def test_unregister_custom_directive(self):
        """Custom directives can be unregistered."""
        register_custom_directive("TEMP", {})
        assert is_custom_directive("TEMP")
        unregister_custom_directive("TEMP")
        assert not is_custom_directive("TEMP")

    def test_get_custom_directives(self):
        """get_custom_directives returns all registered types."""
        register_custom_directive("TYPE1", {"a": 1})
        register_custom_directive("TYPE2", {"b": 2})
        
        result = get_custom_directives()
        assert "TYPE1" in result
        assert "TYPE2" in result
        assert result["TYPE1"] == {"a": 1}
        assert result["TYPE2"] == {"b": 2}

    def test_clear_custom_directives(self):
        """clear_custom_directives empties the registry."""
        register_custom_directive("KEEP", {})
        clear_custom_directives()
        assert get_custom_directives() == {}

    def test_is_custom_directive_false_for_unregistered(self):
        """is_custom_directive returns False for unregistered types."""
        assert not is_custom_directive("UNKNOWN")
        assert not is_custom_directive("MODEL")  # Built-in, not custom

    def test_register_with_metadata(self):
        """Custom directives store metadata."""
        metadata = {
            "name": "queue-stats",
            "handler": "python -m check_hygiene",
            "description": "Check backlog hygiene",
        }
        register_custom_directive("HYGIENE", metadata)
        
        result = get_custom_directives()
        assert result["HYGIENE"] == metadata

    def test_register_without_metadata(self):
        """Custom directives can be registered without metadata."""
        register_custom_directive("SIMPLE")
        assert is_custom_directive("SIMPLE")
        assert get_custom_directives()["SIMPLE"] == {}


class TestDirectiveTypeCoexistence:
    """Tests for built-in and custom directive coexistence."""

    def test_both_types_in_same_workflow(self):
        """Built-in and custom directives can coexist."""
        # Simulate a workflow with mixed directive types
        directives = [
            Directive(DirectiveType.MODEL, "gpt-4", 1, "MODEL gpt-4"),
            Directive("HYGIENE", "check", 2, "HYGIENE check"),
            Directive(DirectiveType.PROMPT, "Analyze", 3, "PROMPT Analyze"),
            Directive("TRACE", "verify", 4, "TRACE verify"),
        ]
        
        built_in = [d for d in directives if not d.is_custom]
        custom = [d for d in directives if d.is_custom]
        
        assert len(built_in) == 2
        assert len(custom) == 2
        assert built_in[0].type_name == "MODEL"
        assert custom[0].type_name == "HYGIENE"
