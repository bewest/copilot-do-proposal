"""Tests for LSP module."""

from pathlib import Path

import pytest

from sdqctl.lsp import (
    Language,
    LSPError,
    SymbolInfo,
    TypeDefinition,
    detect_language,
    get_client,
    list_available_servers,
    register_client,
)


class TestLanguageEnum:
    """Test Language enum."""

    def test_typescript_value(self):
        assert Language.TYPESCRIPT.value == "typescript"

    def test_swift_value(self):
        assert Language.SWIFT.value == "swift"

    def test_kotlin_value(self):
        assert Language.KOTLIN.value == "kotlin"

    def test_python_value(self):
        assert Language.PYTHON.value == "python"


class TestTypeDefinition:
    """Test TypeDefinition dataclass."""

    def test_basic_creation(self):
        td = TypeDefinition(
            name="Treatment",
            language=Language.TYPESCRIPT,
            kind="interface",
            file_path=Path("src/models/treatment.ts"),
            line=10,
            signature="interface Treatment { ... }",
        )
        assert td.name == "Treatment"
        assert td.language == Language.TYPESCRIPT
        assert td.kind == "interface"

    def test_to_markdown(self):
        td = TypeDefinition(
            name="Treatment",
            language=Language.TYPESCRIPT,
            kind="interface",
            file_path=Path("src/models/treatment.ts"),
            line=10,
            signature="interface Treatment {\n  id: string;\n}",
        )
        md = td.to_markdown()
        assert "## Treatment" in md
        assert "**Kind**: interface" in md
        assert "```typescript" in md
        assert "interface Treatment" in md

    def test_to_markdown_with_doc_comment(self):
        td = TypeDefinition(
            name="Bolus",
            language=Language.SWIFT,
            kind="struct",
            file_path=Path("Models/Bolus.swift"),
            line=5,
            signature="struct Bolus { ... }",
            doc_comment="Represents a bolus insulin delivery.",
        )
        md = td.to_markdown()
        assert "Represents a bolus" in md


class TestSymbolInfo:
    """Test SymbolInfo dataclass."""

    def test_basic_creation(self):
        si = SymbolInfo(
            name="deliverBolus",
            kind="function",
            file_path=Path("src/pump.ts"),
            line=42,
            signature="function deliverBolus(units: number): Promise<void>",
        )
        assert si.name == "deliverBolus"
        assert si.kind == "function"
        assert si.line == 42


class TestLSPError:
    """Test LSPError dataclass."""

    def test_basic_creation(self):
        err = LSPError(message="Symbol not found")
        assert err.message == "Symbol not found"
        assert err.code is None

    def test_with_code(self):
        err = LSPError(message="Server timeout", code="TIMEOUT")
        assert err.code == "TIMEOUT"


class TestDetectLanguage:
    """Test language detection."""

    def test_detect_typescript(self, tmp_path):
        (tmp_path / "tsconfig.json").write_text("{}")
        assert detect_language(tmp_path) == Language.TYPESCRIPT

    def test_detect_python(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]")
        assert detect_language(tmp_path) == Language.PYTHON

    def test_detect_swift(self, tmp_path):
        (tmp_path / "Package.swift").write_text("// Swift package")
        assert detect_language(tmp_path) == Language.SWIFT

    def test_detect_kotlin(self, tmp_path):
        (tmp_path / "build.gradle.kts").write_text("// Kotlin")
        assert detect_language(tmp_path) == Language.KOTLIN

    def test_detect_unknown(self, tmp_path):
        assert detect_language(tmp_path) is None


class TestClientRegistry:
    """Test client registration and retrieval."""

    def test_get_client_unknown_language(self, tmp_path):
        assert get_client("unknown", tmp_path) is None

    def test_get_client_no_implementation(self, tmp_path):
        # No clients registered yet
        assert get_client("typescript", tmp_path) is None

    def test_list_available_servers(self):
        result = list_available_servers()
        assert isinstance(result, dict)
        assert Language.TYPESCRIPT in result


class TestRegisterClient:
    """Test client registration decorator."""

    def test_register_decorator(self):
        # Create a mock client class
        @register_client(Language.TYPESCRIPT)
        class MockTSClient:
            language = Language.TYPESCRIPT
            is_available = False

            def initialize(self, project_root):
                return False

        # Verify registration worked
        from sdqctl.lsp import _CLIENTS

        assert Language.TYPESCRIPT in _CLIENTS
