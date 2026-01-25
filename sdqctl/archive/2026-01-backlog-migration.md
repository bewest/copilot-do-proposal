# Backlog Migration Archive - January 2026

> **Archived**: 2026-01-25  
> **Source**: proposals/BACKLOG.md  
> **Reason**: Reduce active backlog size (~1000 → <300 lines); preserve historical record  
> **Decision**: [D-015](DECISIONS.md#d-015-backlog-organization)

This file contains completed work items, resolved research, and historical analysis
that was previously in BACKLOG.md. This content is preserved for reference but is
no longer actively tracked.

---

## Tooling Commands Status (All Complete)

All 8 proposed tooling commands were fully implemented by 2026-01-25:

| Command | Purpose | Subcommands | Completion |
|---------|---------|-------------|------------|
| `render` | Preview prompts (no AI) | `run`, `cycle`, `apply`, `file` | 2026-01-23 |
| `verify` | Static verification | `refs`, `links`, `traceability`, `all` | 2026-01-23 |
| `validate` | Syntax checking | — | 2026-01-23 |
| `show` | Display parsed workflow | — | 2026-01-23 |
| `status` | Session/system info | `--adapters`, `--sessions`, `--models`, `--auth` | 2026-01-23 |
| `sessions` | Session management | `list`, `delete`, `cleanup`, `resume` | 2026-01-25 |
| `init` | Project initialization | — | 2026-01-23 |
| `help` | Documentation access | 12 commands, 6 topics | 2026-01-23 |

---

## SDK v2 Integration (All Complete)

> **Analysis Date**: 2026-01-24  
> **SDK Location**: `../../copilot-sdk/python`

| Feature | Proposal | Status | Completion | ADR |
|---------|----------|--------|------------|-----|
| Infinite Sessions | SDK-INFINITE-SESSIONS.md | ✅ Complete | 2026-01-25 | — |
| Session Persistence | SDK-SESSION-PERSISTENCE.md | ✅ Complete | 2026-01-25 | [ADR-004](decisions/ADR-004-sdk-session-persistence.md) |
| Metadata APIs | SDK-METADATA-APIS.md | ✅ Complete | 2026-01-25 | — |

### Key SDK Changes (Protocol Version 2)

- **Infinite Sessions** - Background compaction at 80% context, blocking at 95%
- **Session APIs** - `list_sessions()`, `resume_session()`, `delete_session()`
- **Metadata APIs** - `get_status()`, `get_auth_status()`, `list_models()`
- **Workspace Path** - `session.workspace_path` for session artifacts

---

## Research Items (All Resolved)

| ID | Topic | Hypothesis | Resolution | Date |
|----|-------|------------|------------|------|
| R-001 | SDK 2 intent reading | SDK 2 may provide tool info differently | Root cause was Q-014 handler leak | 2026-01-25 |
| R-002 | Accumulate mode stability | Event handlers accumulate across cycles | Fixed with handler-once pattern (line 655) | 2026-01-25 |
| R-003 | Event subscription cleanup | `send()` lacks handler cleanup | Handler registered once per session with flag | 2026-01-25 |

---

## Proposal vs Implementation Gap Analysis (Complete)

All proposals analyzed and gaps closed as of 2026-01-25.

### RUN-BRANCHING.md

| Feature | Proposed | Status |
|---------|----------|--------|
| `RUN-RETRY N "prompt"` | Phase 1 | ✅ Implemented |
| `ON-FAILURE` block | Phase 2 | ✅ Implemented |
| `ON-SUCCESS` block | Phase 2 | ✅ Implemented |
| ELIDE + branching = parse error | Design | ✅ Enforced |

### VERIFICATION-DIRECTIVES.md

| Feature | Proposed | Status |
|---------|----------|--------|
| `sdqctl verify refs` CLI | Phase 2 | ✅ Implemented |
| `sdqctl verify links` CLI | Phase 2 | ✅ Implemented |
| `sdqctl verify traceability` CLI | Phase 2 | ✅ Implemented |
| `sdqctl verify all` CLI | Phase 2 | ✅ Implemented |
| `VERIFY refs` directive | Phase 3-4 | ✅ Implemented |
| `VERIFY-ON-ERROR` directive | Phase 3-4 | ✅ Implemented |
| `VERIFY-OUTPUT` directive | Phase 3-4 | ✅ Implemented |
| `VERIFY-LIMIT` directive | Phase 3-4 | ✅ Implemented |
| `links` verifier | Phase 1 | ✅ Implemented |
| `terminology` verifier | Phase 1 | ✅ Implemented |
| `traceability` verifier | Phase 1 | ✅ Implemented |
| `assertions` verifier | Phase 1 | ✅ Implemented |

### PIPELINE-ARCHITECTURE.md

| Feature | Proposed | Status |
|---------|----------|--------|
| `--from-json` flag | Phase 1 | ✅ Implemented |
| `schema_version` field | Phase 2 | ✅ Implemented |
| Pipeline validation | Phase 3 | ✅ Implemented |

### CLI-ERGONOMICS.md

| Feature | Proposed | Status |
|---------|----------|--------|
| `sdqctl help <topic>` | — | ✅ 6 topics implemented |
| `sdqctl help <command>` | — | ✅ 12 commands documented |
| `--list` flag | — | ✅ Implemented |

---

## Priority 3: Implementation Tasks (All Complete)

### 3.1 `--from-json` Flag

**Status**: ✅ Complete (2026-01-24)

Enables external transformation of rendered workflows:
```bash
sdqctl render cycle workflow.conv --json \
  | jq '.cycles[0].prompts[0].resolved += " (modified)"' \
  | sdqctl cycle --from-json -
```

### 3.2 STPA Workflow Templates

**Status**: ✅ Complete (2026-01-24)

Templates created in `examples/workflows/stpa/`:
- `hazard-analysis.conv`
- `uca-identification.conv`
- `safety-constraint-derivation.conv`

### 3.3 VERIFY Directive Implementation

**Status**: ✅ Complete (2026-01-24)

All verifiers implemented:
- `refs` - @-reference validation
- `links` - URL/file link checking
- `traceability` - STPA chain validation
- `terminology` - Deprecated term detection
- `assertions` - Assertion documentation check

---

## Documentation Gaps (Completed Items)

| Gap | Location | Status | Date |
|-----|----------|--------|------|
| Pipeline schema docs | `docs/PIPELINE-SCHEMA.md` | ✅ | 2026-01-24 |
| Verifier extension guide | `docs/EXTENDING-VERIFIERS.md` | ✅ | 2026-01-24 |
| Security model | `docs/SECURITY-MODEL.md` | ✅ | 2026-01-25 |
| Model selection guide | `docs/ADAPTERS.md` | ✅ | 2026-01-25 |
| HELP directive examples | `docs/GETTING-STARTED.md` | ✅ | 2026-01-25 |
| ON-FAILURE/ON-SUCCESS tutorial | `docs/GETTING-STARTED.md` | ✅ | 2026-01-25 |
| `validate` command tutorial | `docs/GETTING-STARTED.md` | ✅ | 2026-01-25 |
| Copilot skill files docs | `docs/GETTING-STARTED.md` | ✅ | 2026-01-25 |
| CONSULT/SESSION-NAME in README | `README.md` | ✅ | 2026-01-25 |
| DEBUG directives in README | `README.md` | ✅ | 2026-01-25 |
| INFINITE-SESSIONS in README | `README.md` | ✅ | 2026-01-25 |
| `flow` command full documentation | `docs/COMMANDS.md` | ✅ | 2026-01-25 |
| `resume` vs `sessions resume` clarity | `docs/COMMANDS.md` | ✅ | 2026-01-25 |
| `artifact` user-facing guide | `docs/GETTING-STARTED.md` | ✅ | 2026-01-25 |

---

## Code Quality Fixes (Completed)

### Critical: Undefined Name Bugs (F821) - FIXED

5 bugs fixed (2026-01-25):

| Location | Variable | Fix Applied |
|----------|----------|-------------|
| `run.py:568` | `quiet` | Changed to `verbosity > 0` |
| `run.py:1172` | `restrictions` | Changed to `conv.file_restrictions` |
| `run.py:1173` | `show_streaming` | Changed to `True` |
| `run.py:1376` | `pending_context` | Removed dead code |
| `copilot.py:1001` | `ModelRequirements` | Added TYPE_CHECKING import |

### Linting Issues - 90% Fixed

**Before**: 1,994 issues | **After**: 197 issues | **Fixed**: 1,797 (90%)

| Category | Before | After |
|----------|--------|-------|
| W293 (whitespace in blank lines) | 1,617 | 0 |
| W291 (trailing whitespace) | 63 | 0 |
| F541 (f-string no placeholders) | 41 | 0 |
| F401 (unused imports) | 35 | 0 |
| I001 (unsorted imports) | 34 | 0 |
| F811 (redefinition) | 1 | 0 |

### Architecture Fixes

| Issue | Resolution | Date |
|-------|------------|------|
| Commands→core→commands circular import | Created `core/help_topics.py` | 2026-01-25 |
| Q-014 Event handler leak | Handler registered once per session | 2026-01-25 |
| Q-015 Duplicate tool calls | Fixed by Q-014 | 2026-01-25 |
| Q-013 Unknown tool names | Root cause was Q-014 | 2026-01-25 |

---

## Quirks Resolved

All quirks Q-001 through Q-016 resolved as of 2026-01-25.
See [docs/QUIRKS.md](../docs/QUIRKS.md) for details.

---

## References

- [BACKLOG.md](../proposals/BACKLOG.md) - Current active items
- [DECISIONS.md](DECISIONS.md) - Design decisions
- [SESSIONS/2026-01-25.md](SESSIONS/2026-01-25.md) - Session logs
