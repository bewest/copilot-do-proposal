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

    def test_get_client_typescript_returns_client(self, tmp_path):
        # TypeScriptClient is registered, but tsserver not available
        # so get_client returns None (initialization fails)
        import shutil
        original_which = shutil.which
        shutil.which = lambda x: None
        try:
            result = get_client("typescript", tmp_path)
            assert result is None  # No tsserver, so init fails
        finally:
            shutil.which = original_which

    def test_list_available_servers(self):
        result = list_available_servers()
        assert isinstance(result, dict)
        assert Language.TYPESCRIPT in result


class TestRegisterClient:
    """Test client registration decorator."""

    def test_register_decorator(self):
        # TypeScriptClient is already registered
        from sdqctl.lsp import _CLIENTS, TypeScriptClient

        assert Language.TYPESCRIPT in _CLIENTS
        assert _CLIENTS[Language.TYPESCRIPT] == TypeScriptClient


class TestDetectTsserver:
    """Test TypeScript server detection."""

    def test_detect_local_tsserver(self, tmp_path):
        """Detect tsserver in local node_modules."""
        from sdqctl.lsp import detect_tsserver

        # Create fake local tsserver
        bin_dir = tmp_path / "node_modules" / ".bin"
        bin_dir.mkdir(parents=True)
        tsserver = bin_dir / "tsserver"
        tsserver.write_text("#!/bin/sh\necho tsserver")

        result = detect_tsserver(tmp_path)
        assert result == tsserver

    def test_detect_no_tsserver(self, tmp_path, monkeypatch):
        """Return None when tsserver not found."""
        from sdqctl.lsp import detect_tsserver

        # Patch shutil.which to return None
        monkeypatch.setattr("shutil.which", lambda x: None)

        result = detect_tsserver(tmp_path)
        assert result is None

    def test_detect_global_tsserver(self, tmp_path, monkeypatch):
        """Detect tsserver in global PATH."""
        from sdqctl.lsp import detect_tsserver

        # Patch shutil.which to return a fake path
        monkeypatch.setattr("shutil.which", lambda x: "/usr/local/bin/tsserver" if x == "tsserver" else None)

        result = detect_tsserver(tmp_path)
        assert result == Path("/usr/local/bin/tsserver")


class TestTypeScriptClient:
    """Test TypeScript client implementation."""

    def test_client_is_registered(self):
        """TypeScriptClient should be registered for TYPESCRIPT."""
        from sdqctl.lsp import _CLIENTS, TypeScriptClient

        assert Language.TYPESCRIPT in _CLIENTS
        assert _CLIENTS[Language.TYPESCRIPT] == TypeScriptClient

    def test_is_available_when_tsserver_exists(self, tmp_path):
        """is_available returns True when tsserver found."""
        from sdqctl.lsp import TypeScriptClient

        # Create fake local tsserver
        bin_dir = tmp_path / "node_modules" / ".bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "tsserver").write_text("#!/bin/sh")

        client = TypeScriptClient()
        client._project_root = tmp_path
        assert client.is_available is True

    def test_is_available_when_missing(self, tmp_path, monkeypatch):
        """is_available returns False when tsserver not found."""
        from sdqctl.lsp import TypeScriptClient

        monkeypatch.setattr("shutil.which", lambda x: None)

        client = TypeScriptClient()
        client._project_root = tmp_path
        assert client.is_available is False

    def test_initialize_success(self, tmp_path):
        """initialize returns True when tsserver available."""
        from sdqctl.lsp import TypeScriptClient

        # Create fake local tsserver
        bin_dir = tmp_path / "node_modules" / ".bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "tsserver").write_text("#!/bin/sh")

        client = TypeScriptClient()
        assert client.initialize(tmp_path) is True
        assert client._initialized is True

    def test_initialize_failure(self, tmp_path, monkeypatch):
        """initialize returns False when tsserver unavailable."""
        from sdqctl.lsp import TypeScriptClient

        monkeypatch.setattr("shutil.which", lambda x: None)

        client = TypeScriptClient()
        assert client.initialize(tmp_path) is False
        assert client._initialized is False

    def test_get_type_returns_not_implemented(self, tmp_path):
        """get_type returns LSPError for Phase 2."""
        from sdqctl.lsp import TypeScriptClient

        # Create fake local tsserver
        bin_dir = tmp_path / "node_modules" / ".bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "tsserver").write_text("#!/bin/sh")

        client = TypeScriptClient()
        client.initialize(tmp_path)
        result = client.get_type("Treatment")

        assert isinstance(result, LSPError)
        assert result.code == "NOT_IMPLEMENTED"

    def test_version_from_package_json(self, tmp_path):
        """version reads from typescript package.json."""
        from sdqctl.lsp import TypeScriptClient
        import json

        # Create fake local tsserver
        bin_dir = tmp_path / "node_modules" / ".bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "tsserver").write_text("#!/bin/sh")

        # Create fake package.json
        ts_dir = tmp_path / "node_modules" / "typescript"
        ts_dir.mkdir(parents=True)
        (ts_dir / "package.json").write_text(json.dumps({"version": "5.3.2"}))

        client = TypeScriptClient()
        client.initialize(tmp_path)
        assert client.version == "5.3.2"

    def test_get_client_returns_typescript_client(self, tmp_path):
        """get_client returns initialized TypeScriptClient."""
        # Create fake local tsserver
        bin_dir = tmp_path / "node_modules" / ".bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "tsserver").write_text("#!/bin/sh")

        client = get_client("typescript", tmp_path)
        assert client is not None
        assert client._initialized is True
