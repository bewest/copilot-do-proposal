# Cycle Command Improvements - Topic Focus

**Topic:** `sdqctl cycle` command session management  
**Source:** User feedback + code analysis  
**Created:** 2026-01-21  
**Status:** Planning

---

## What is the Cycle Command?

The `cycle` command runs multi-cycle workflows with different session management strategies:

```bash
sdqctl cycle workflow.conv -n 5 --session-mode fresh
sdqctl cycle workflow.conv --session-mode compact
sdqctl cycle workflow.conv --session-mode accumulate  # currently called 'shared'
```

**Implementation:** `sdqctl/commands/cycle.py`  
**Session Management:** `sdqctl/core/session.py`  
**Context Loading:** `sdqctl/core/context.py`

---

## Scope Boundaries

### In Scope
- Session mode semantics (fresh, compact, accumulate)
- Context file reloading between cycles
- Mode naming clarity
- Testing of session mode behavior

### Out of Scope (for this topic)
- RUN directive execution (separate topic)
- Compaction algorithm details
- Checkpoint persistence format
- Adapter-specific session handling

---

## Current Behavior Analysis

### Session Modes

| Mode | Current Name | Intended Behavior | Current Implementation |
|------|-------------|-------------------|------------------------|
| **Accumulate** | `shared` | Context grows, compact only when limit reached | ✅ Works correctly |
| **Compact** | `compact` | Summarize after each cycle, stay in same session | ✅ Works correctly |
| **Fresh** | `fresh` | Start completely new session each cycle | ⚠️ Partial - see gaps |

### Fresh Mode Gaps

**What currently happens on "fresh" (cycle.py lines 190-195, 232-236):**
1. ✅ Destroy old adapter session, create new one
2. ✅ Re-inject context via `session.context.get_context_content()`
3. ❌ **CONTEXT files NOT re-read from disk** (cached at Session.__init__)
4. ✅ Prologues/epilogues ARE re-read (resolved in `build_prompt_with_injection`)

**User expectation:**
- "Fresh" should be equivalent to running `sdqctl run` from scratch
- Any files modified during cycle N should be visible in cycle N+1
- CONTEXT files (from `CONTEXT @reports/tracker.md` directive) should refresh

---

## Improvement Chunks

Work is organized by complexity. Complete one chunk before moving to the next.

### 1. Correctness (C)

#### C1: Fresh Mode Should Reload CONTEXT Files ⏳

**Current State:**
- `Session.__init__()` loads CONTEXT files once (session.py lines 92-94)
- `session.context.files` cached for entire run
- Fresh mode gets stale file contents

**Technical Details:**
```python
# session.py lines 92-94 - only called once at Session creation
for pattern in conversation.context_files:
    self.context.add_pattern(pattern)
```

**Required Changes:**
1. Add `Session.reload_context()` method that clears and reloads files
2. Call `reload_context()` at start of each cycle in fresh mode
3. Preserve ContextManager config (base_path, limit_threshold, path_filter)

**Files to Modify:**
- `sdqctl/core/session.py`: Add `reload_context()` method (~10 lines)
- `sdqctl/commands/cycle.py`: Call on fresh mode cycles (~3 lines)

**Test Cases:**
- CONTEXT file modified during cycle → visible in next cycle (fresh mode)
- CONTEXT file modified during cycle → NOT visible (compact/accumulate mode)

**Acceptance Criteria:**
- [ ] `reload_context()` method exists
- [ ] Fresh mode calls it at cycle start
- [ ] Integration test validates file refresh

---

### 2. Ergonomics (E)

#### E1: Rename 'shared' to 'accumulate' 

**Current State:**
- `--session-mode` accepts: `shared`, `compact`, `fresh`
- "shared" is unclear - sounds like multi-user sharing
- "accumulate" better describes context growth behavior

**Required Changes:**
1. Rename option value in click decorator
2. Update variable name in code
3. Update docstring and help text
4. Update tests
5. Update documentation

**Files to Modify:**
- `sdqctl/commands/cycle.py`: ~8 occurrences of "shared"
- `sdqctl/cli.py`: Help text if referenced
- `tests/test_cycle_command.py`: Test fixtures
- `examples/workflows/README.md`: Documentation

**Breaking Change:** Yes - existing scripts using `--session-mode shared` will break

**Migration Path:** Log deprecation warning if "shared" used, accept as alias for 6 months

**Acceptance Criteria:**
- [ ] `accumulate` is the documented mode name
- [ ] `shared` works with deprecation warning (optional)
- [ ] Tests updated

---

### 3. Code Quality (Q)

#### Q1: Document Session Mode Semantics

**Current State:**
- Mode differences scattered in code comments
- No single source of truth for behavior

**Required Changes:**
1. Add comprehensive docstring to `_cycle_async()`
2. Add SESSION_MODES constant with documentation
3. Update README with clear mode comparison

**Files to Modify:**
- `sdqctl/commands/cycle.py`: Docstring expansion
- `README.md`: Session modes documentation section

**Acceptance Criteria:**
- [ ] Each mode has clear documented behavior
- [ ] README has comparison table

---

### 4. Testing (T)

#### T1: Session Mode Integration Tests

**Current State:**
- Basic dry-run tests exist
- No tests for actual file refresh behavior
- No tests validating mode semantics

**Required Tests:**
```python
class TestCycleSessionModes:
    async def test_fresh_mode_reloads_context_files(self):
        """Fresh mode should see file changes between cycles."""
        
    async def test_accumulate_mode_preserves_context(self):
        """Accumulate mode maintains conversation history."""
        
    async def test_compact_mode_summarizes_between_cycles(self):
        """Compact mode reduces context via summarization."""
        
    async def test_fresh_mode_reinjects_prologue(self):
        """Fresh mode sends prologue on every cycle."""
```

**Files to Modify:**
- `tests/test_cycle_command.py`: Add session mode tests

**Acceptance Criteria:**
- [ ] Each mode has dedicated test
- [ ] File refresh behavior verified for fresh mode

---

## Priority Order

1. **C1**: Fresh mode context reload - core correctness issue
2. **T1**: Tests - validate the fix works
3. **E1**: Rename shared → accumulate - clarity
4. **Q1**: Documentation - long-term maintainability

---

## Session Tracking

### Current Session
- **Date:** 2026-01-21
- **Focus:** Planning and analysis
- **Status:** Completed analysis, created focus document

### Completed Items
- [x] Analyzed cycle.py implementation
- [x] Identified fresh mode gap (context files not reloaded)
- [x] Clarified scope with user (reload CONTEXT files, not .conv)
- [x] Confirmed naming change: shared → accumulate

### Remaining Work
- [ ] C1: Implement reload_context()
- [ ] T1: Add session mode tests
- [ ] E1: Rename shared → accumulate
- [ ] Q1: Update documentation

---

## Lessons Learned

### Analysis Phase
- **Finding:** Prologues/epilogues already work correctly for fresh mode
  - `resolve_content_reference()` called on every prompt in loop
  - Only CONTEXT files (from CONTEXT directive) are cached
  
- **Finding:** The gap is specifically `Session.__init__` loading files once
  - Fix is localized to session.py + cycle.py
  - Low complexity change (~15-20 lines)

### Design Decisions
1. **Q: Re-read .conv file on fresh mode?**  
   A: No - .conv is the "stable contract" that defines workflow structure
   
2. **Q: Keep 'shared' as alias?**  
   A: User chose breaking change (rename to 'accumulate')

---

## Usage

Run focused cycle with this prologue:

```bash
sdqctl -vv cycle -n 3 --adapter copilot \
  --prologue @reports/cycle-improvements-focus.md \
  --epilogue "Update @reports/cycle-improvements-focus.md with completed items" \
  examples/workflows/progress-tracker.conv
```
