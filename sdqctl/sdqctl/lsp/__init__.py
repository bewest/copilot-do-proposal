"""
LSP (Language Server Protocol) integration for sdqctl.

Provides semantic code context through language servers:
- Type definitions and signatures
- Symbol lookup and navigation
- Cross-file reference following
- Type comparison across projects

See: proposals/LSP-INTEGRATION.md

Usage:
    from sdqctl.lsp import LSPClient, get_client

    client = get_client("typescript", project_root)
    type_def = client.get_type("Treatment")
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Protocol


class Language(Enum):
    """Supported languages for LSP integration."""

    TYPESCRIPT = "typescript"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    PYTHON = "python"


@dataclass
class TypeDefinition:
    """Structured type definition from language server."""

    name: str
    language: Language
    kind: str  # class, interface, struct, type, enum
    file_path: Path
    line: int
    signature: str  # Full type signature
    doc_comment: str | None = None
    fields: list[dict[str, Any]] = field(default_factory=list)
    methods: list[dict[str, Any]] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Render type definition as markdown."""
        lines = [
            f"## {self.name}",
            f"**Kind**: {self.kind}",
            f"**File**: `{self.file_path}:{self.line}`",
            "",
            "```" + self.language.value,
            self.signature,
            "```",
        ]
        if self.doc_comment:
            lines.extend(["", self.doc_comment])
        return "\n".join(lines)


@dataclass
class SymbolInfo:
    """Information about a code symbol."""

    name: str
    kind: str  # function, method, variable, constant, etc.
    file_path: Path
    line: int
    signature: str
    doc_comment: str | None = None


@dataclass
class LSPError:
    """Error from LSP operation."""

    message: str
    code: str | None = None
    file_path: Path | None = None


class LSPClient(Protocol):
    """Protocol for language server clients.

    Implementations must provide semantic queries for their language.
    """

    @property
    def language(self) -> Language:
        """The language this client handles."""
        ...

    @property
    def is_available(self) -> bool:
        """Whether the language server is available."""
        ...

    def initialize(self, project_root: Path) -> bool:
        """Initialize connection to language server.

        Args:
            project_root: Root directory of the project to analyze

        Returns:
            True if initialization succeeded
        """
        ...

    def shutdown(self) -> None:
        """Shutdown the language server connection."""
        ...

    def get_type(self, name: str) -> TypeDefinition | LSPError:
        """Get type definition by name.

        Args:
            name: Type name to look up

        Returns:
            TypeDefinition if found, LSPError otherwise
        """
        ...

    def get_symbol(self, name: str) -> SymbolInfo | LSPError:
        """Get symbol information by name.

        Args:
            name: Symbol name to look up

        Returns:
            SymbolInfo if found, LSPError otherwise
        """
        ...

    def find_references(self, name: str) -> list[Path] | LSPError:
        """Find all references to a symbol.

        Args:
            name: Symbol name to search for

        Returns:
            List of file paths containing references, or LSPError
        """
        ...


# Registry of available LSP clients
_CLIENTS: dict[Language, type] = {}


def register_client(language: Language):
    """Decorator to register an LSP client implementation."""

    def decorator(cls: type) -> type:
        _CLIENTS[language] = cls
        return cls

    return decorator


def get_client(language: str | Language, project_root: Path) -> LSPClient | None:
    """Get an LSP client for the specified language.

    Args:
        language: Language name or Language enum
        project_root: Root directory of the project

    Returns:
        Initialized LSPClient, or None if not available
    """
    if isinstance(language, str):
        try:
            lang = Language(language.lower())
        except ValueError:
            return None
    else:
        lang = language

    client_cls = _CLIENTS.get(lang)
    if client_cls is None:
        return None

    client = client_cls()
    if client.initialize(project_root):
        return client
    return None


def detect_language(project_root: Path) -> Language | None:
    """Detect primary language of a project.

    Args:
        project_root: Root directory to analyze

    Returns:
        Detected Language, or None if unknown
    """
    # Check for language-specific marker files
    markers = {
        Language.TYPESCRIPT: ["tsconfig.json", "package.json"],
        Language.SWIFT: ["Package.swift", "*.xcodeproj"],
        Language.KOTLIN: ["build.gradle.kts", "build.gradle"],
        Language.PYTHON: ["pyproject.toml", "setup.py", "requirements.txt"],
    }

    for lang, files in markers.items():
        for pattern in files:
            if "*" in pattern:
                if list(project_root.glob(pattern)):
                    return lang
            elif (project_root / pattern).exists():
                return lang

    return None


def list_available_servers() -> dict[Language, bool]:
    """List all supported languages and their availability.

    Returns:
        Dict mapping Language to whether server is available
    """
    result = {}
    for lang in Language:
        client_cls = _CLIENTS.get(lang)
        if client_cls:
            client = client_cls()
            result[lang] = client.is_available
        else:
            result[lang] = False
    return result


def detect_tsserver(project_root: Path | None = None) -> Path | None:
    """Detect TypeScript server (tsserver) location.

    Checks in order:
    1. Local node_modules/.bin/tsserver (if project_root provided)
    2. Global tsserver in PATH

    Args:
        project_root: Optional project directory to check for local install

    Returns:
        Path to tsserver executable, or None if not found
    """
    import shutil

    # Check local node_modules first
    if project_root:
        local_tsserver = project_root / "node_modules" / ".bin" / "tsserver"
        if local_tsserver.exists():
            return local_tsserver

    # Check global PATH
    global_tsserver = shutil.which("tsserver")
    if global_tsserver:
        return Path(global_tsserver)

    return None


@register_client(Language.TYPESCRIPT)
class TypeScriptClient:
    """TypeScript language server client using tsserver."""

    def __init__(self):
        self._tsserver_path: Path | None = None
        self._project_root: Path | None = None
        self._initialized = False

    @property
    def is_available(self) -> bool:
        """Check if tsserver is available."""
        return detect_tsserver(self._project_root) is not None

    @property
    def server_path(self) -> Path | None:
        """Get the detected tsserver path."""
        if self._tsserver_path is None:
            self._tsserver_path = detect_tsserver(self._project_root)
        return self._tsserver_path

    @property
    def version(self) -> str | None:
        """Get TypeScript version."""
        if not self.server_path:
            return None
        # tsserver doesn't have --version, check typescript package
        if self._project_root:
            pkg_json = self._project_root / "node_modules" / "typescript" / "package.json"
            if pkg_json.exists():
                import json
                try:
                    data = json.loads(pkg_json.read_text())
                    return data.get("version")
                except (json.JSONDecodeError, OSError):
                    pass
        return "unknown"

    def initialize(self, project_root: Path) -> bool:
        """Initialize client for a project.

        Args:
            project_root: Root directory of the TypeScript project

        Returns:
            True if initialization successful
        """
        self._project_root = project_root
        self._tsserver_path = detect_tsserver(project_root)
        self._initialized = self._tsserver_path is not None
        return self._initialized

    def shutdown(self) -> None:
        """Shutdown the client."""
        self._initialized = False

    def get_type(self, name: str) -> TypeDefinition | LSPError:
        """Get type definition by name.

        Note: Full implementation coming in Phase 2.
        """
        if not self._initialized:
            return LSPError(message="Client not initialized", code="NOT_INITIALIZED")
        return LSPError(message="Type lookup coming in Phase 2", code="NOT_IMPLEMENTED")

    def get_symbol(self, name: str) -> SymbolInfo | LSPError:
        """Get symbol information by name.

        Note: Full implementation coming in Phase 2.
        """
        if not self._initialized:
            return LSPError(message="Client not initialized", code="NOT_INITIALIZED")
        return LSPError(message="Symbol lookup coming in Phase 2", code="NOT_IMPLEMENTED")

    def find_references(self, name: str) -> list[Path] | LSPError:
        """Find all references to a symbol.

        Note: Full implementation coming in Phase 2.
        """
        if not self._initialized:
            return LSPError(message="Client not initialized", code="NOT_INITIALIZED")
        return LSPError(message="Reference search coming in Phase 2", code="NOT_IMPLEMENTED")


__all__ = [
    "Language",
    "TypeDefinition",
    "SymbolInfo",
    "LSPError",
    "LSPClient",
    "register_client",
    "get_client",
    "detect_language",
    "list_available_servers",
    "detect_tsserver",
    "TypeScriptClient",
]
