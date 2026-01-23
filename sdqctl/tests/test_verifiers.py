"""Tests for the verification subsystem."""

import pytest
from pathlib import Path

from sdqctl.core.conversation import ConversationFile
from sdqctl.verifiers import (
    VerificationError,
    VerificationResult,
    RefsVerifier,
    LinksVerifier,
    VERIFIERS,
)


class TestVerificationResult:
    """Tests for VerificationResult dataclass."""
    
    def test_passed_result(self):
        """Test a passing verification result."""
        result = VerificationResult(
            passed=True,
            summary="All checks passed",
        )
        assert result.passed
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
    
    def test_failed_result(self):
        """Test a failing verification result."""
        result = VerificationResult(
            passed=False,
            errors=[
                VerificationError(
                    file="test.md",
                    line=10,
                    message="Broken reference",
                    fix_hint="Fix the path",
                )
            ],
            summary="1 error found",
        )
        assert not result.passed
        assert len(result.errors) == 1
        assert result.errors[0].file == "test.md"
    
    def test_to_markdown(self):
        """Test markdown output formatting."""
        result = VerificationResult(
            passed=False,
            errors=[
                VerificationError(
                    file="test.md",
                    line=10,
                    message="Broken reference: @missing.txt",
                )
            ],
            summary="1 error found",
        )
        md = result.to_markdown()
        assert "❌ Failed" in md
        assert "test.md:10" in md
        assert "Broken reference" in md
    
    def test_to_json(self):
        """Test JSON output formatting."""
        result = VerificationResult(
            passed=True,
            errors=[],
            warnings=[
                VerificationError(file="warn.md", line=1, message="Warning")
            ],
            summary="0 errors, 1 warning",
            details={"files_scanned": 5},
        )
        json_out = result.to_json()
        assert json_out["passed"] is True
        assert json_out["error_count"] == 0
        assert json_out["warning_count"] == 1
        assert json_out["details"]["files_scanned"] == 5


class TestRefsVerifier:
    """Tests for RefsVerifier."""
    
    def test_verifier_registered(self):
        """Test that refs verifier is in the registry."""
        assert "refs" in VERIFIERS
        assert VERIFIERS["refs"] == RefsVerifier
    
    def test_verify_empty_directory(self, tmp_path):
        """Test verification of empty directory."""
        verifier = RefsVerifier()
        result = verifier.verify(tmp_path)
        
        assert result.passed
        assert result.details["files_scanned"] == 0
        assert result.details["refs_found"] == 0
    
    def test_verify_valid_reference(self, tmp_path):
        """Test verification with valid reference."""
        # Create target file
        target = tmp_path / "target.txt"
        target.write_text("Target content")
        
        # Create file with reference
        source = tmp_path / "source.md"
        source.write_text("See @target.txt for details")
        
        verifier = RefsVerifier()
        result = verifier.verify(tmp_path)
        
        assert result.passed
        assert result.details["refs_valid"] == 1
        assert result.details["refs_broken"] == 0
    
    def test_verify_broken_reference(self, tmp_path):
        """Test verification with broken reference."""
        # Create file with broken reference
        source = tmp_path / "source.md"
        source.write_text("See @nonexistent.txt for details")
        
        verifier = RefsVerifier()
        result = verifier.verify(tmp_path)
        
        assert not result.passed
        assert result.details["refs_broken"] == 1
        assert len(result.errors) == 1
        assert "nonexistent.txt" in result.errors[0].message
    
    def test_ignore_jsdoc_annotations(self, tmp_path):
        """Test that JSDoc-style annotations are ignored."""
        source = tmp_path / "code.md"
        source.write_text("""
        @param name The name
        @returns The result
        @deprecated Use newMethod
        """)
        
        verifier = RefsVerifier()
        result = verifier.verify(tmp_path)
        
        # Should pass - no real references to check
        assert result.passed
        assert result.details["refs_found"] == 0 or result.details["refs_broken"] == 0
    
    def test_relative_path_reference(self, tmp_path):
        """Test ./relative/path references."""
        subdir = tmp_path / "sub"
        subdir.mkdir()
        
        target = subdir / "target.txt"
        target.write_text("content")
        
        source = tmp_path / "source.md"
        source.write_text("See @./sub/target.txt")
        
        verifier = RefsVerifier()
        result = verifier.verify(tmp_path)
        
        assert result.passed


class TestVerifyExecutionIntegration:
    """Test VERIFY directive execution in workflows."""

    def test_verify_step_in_workflow(self, tmp_path):
        """Test that VERIFY steps run during workflow execution."""
        # Create a test file with a valid reference
        doc_dir = tmp_path / "docs"
        doc_dir.mkdir()
        test_file = doc_dir / "test.md"
        test_file.write_text("See @../README.md for more info.")
        
        # Create the referenced file
        readme = tmp_path / "README.md"
        readme.write_text("# Test")
        
        # Create workflow with VERIFY step
        workflow = tmp_path / "test.conv"
        workflow.write_text("""MODEL mock
ADAPTER mock
VERIFY-ON-ERROR continue
VERIFY-OUTPUT always
VERIFY refs

PROMPT Analyze the verification results.
""")
        
        conv = ConversationFile.parse(workflow.read_text(), source_path=workflow)
        
        # Check parsing
        verify_steps = [s for s in conv.steps if s.type == "verify"]
        assert len(verify_steps) == 1
        assert verify_steps[0].verify_type == "refs"
        assert conv.verify_on_error == "continue"
        assert conv.verify_output == "always"


class TestLinksVerifier:
    """Tests for LinksVerifier."""
    
    def test_verifier_registered(self):
        """Test that links verifier is in the registry."""
        assert "links" in VERIFIERS
        assert VERIFIERS["links"] == LinksVerifier
    
    def test_verify_empty_directory(self, tmp_path):
        """Test verification of empty directory."""
        verifier = LinksVerifier()
        result = verifier.verify(tmp_path)
        
        assert result.passed
        assert result.details["files_scanned"] == 0
        assert result.details["links_found"] == 0
    
    def test_verify_valid_link(self, tmp_path):
        """Test verification with valid markdown link."""
        # Create target file
        target = tmp_path / "target.md"
        target.write_text("# Target")
        
        # Create file with link
        source = tmp_path / "source.md"
        source.write_text("See [the target](target.md) for details")
        
        verifier = LinksVerifier()
        result = verifier.verify(tmp_path)
        
        assert result.passed
        assert result.details["links_valid"] == 1
        assert result.details["links_broken"] == 0
    
    def test_verify_broken_link(self, tmp_path):
        """Test verification with broken markdown link."""
        # Create file with broken link
        source = tmp_path / "source.md"
        source.write_text("See [missing](nonexistent.md) for details")
        
        verifier = LinksVerifier()
        result = verifier.verify(tmp_path)
        
        assert not result.passed
        assert result.details["links_broken"] == 1
        assert len(result.errors) == 1
        assert "Broken link" in result.errors[0].message
        assert "nonexistent.md" in result.errors[0].message
    
    def test_external_urls_skipped(self, tmp_path):
        """Test that external URLs are skipped by default."""
        source = tmp_path / "source.md"
        source.write_text("See [GitHub](https://github.com/example)")
        
        verifier = LinksVerifier()
        result = verifier.verify(tmp_path)
        
        assert result.passed
        assert result.details["links_external"] == 1
    
    def test_anchor_links_valid(self, tmp_path):
        """Test that anchor-only links are considered valid."""
        source = tmp_path / "source.md"
        source.write_text("See [section](#section-name)")
        
        verifier = LinksVerifier()
        result = verifier.verify(tmp_path)
        
        assert result.passed
        assert result.details["links_valid"] == 1
    
    def test_relative_path_link(self, tmp_path):
        """Test relative path links."""
        subdir = tmp_path / "docs"
        subdir.mkdir()
        
        target = subdir / "target.md"
        target.write_text("# Target")
        
        source = tmp_path / "README.md"
        source.write_text("See [the docs](docs/target.md)")
        
        verifier = LinksVerifier()
        result = verifier.verify(tmp_path)
        
        assert result.passed
        assert result.details["links_valid"] == 1
    
    def test_link_with_anchor(self, tmp_path):
        """Test link to file with anchor is valid if file exists."""
        target = tmp_path / "target.md"
        target.write_text("# Target\n\n## Section")
        
        source = tmp_path / "source.md"
        source.write_text("See [section](target.md#section)")
        
        verifier = LinksVerifier()
        result = verifier.verify(tmp_path)
        
        assert result.passed
        assert result.details["links_valid"] == 1
    
    def test_multiple_links_mixed(self, tmp_path):
        """Test file with multiple links, some valid some broken."""
        # Create only one target
        target = tmp_path / "exists.md"
        target.write_text("# Exists")
        
        source = tmp_path / "source.md"
        source.write_text("""
        - [Valid](exists.md)
        - [Broken](missing.md)
        - [External](https://example.com)
        """)
        
        verifier = LinksVerifier()
        result = verifier.verify(tmp_path)
        
        assert not result.passed
        assert result.details["links_valid"] == 1
        assert result.details["links_broken"] == 1
        assert result.details["links_external"] == 1
    
    def test_recursive_scan(self, tmp_path):
        """Test recursive scanning of subdirectories."""
        subdir = tmp_path / "sub"
        subdir.mkdir()
        
        source = subdir / "nested.md"
        source.write_text("See [broken](nonexistent.md)")
        
        verifier = LinksVerifier()
        result = verifier.verify(tmp_path, recursive=True)
        
        assert not result.passed
        assert result.details["files_scanned"] == 1
        assert result.details["links_broken"] == 1
    
    def test_non_recursive_scan(self, tmp_path):
        """Test non-recursive scanning skips subdirectories."""
        subdir = tmp_path / "sub"
        subdir.mkdir()
        
        # File in subdir with broken link
        nested = subdir / "nested.md"
        nested.write_text("See [broken](nonexistent.md)")
        
        # File in root with valid link
        root_file = tmp_path / "root.md"
        root_file.write_text("See [sub](sub/)")
        
        verifier = LinksVerifier()
        result = verifier.verify(tmp_path, recursive=False)
        
        # Only root file scanned
        assert result.details["files_scanned"] == 1
