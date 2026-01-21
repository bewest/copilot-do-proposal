# RUN Directive Improvements - Topic Focus

**Topic:** RUN directive (subprocess execution in .conv files)  
**Source:** `reports/improvements-tracker.md`  
**Created:** 2026-01-21  
**Status:** In Progress

---

## What is the RUN Directive?

The RUN directive executes shell commands within a conversation workflow:

```
RUN python3 -m pytest tests/
RUN-ON-ERROR continue
RUN-OUTPUT always
RUN-TIMEOUT 120
ALLOW-SHELL true
```

**Implementation:** `sdqctl/commands/run.py` lines 430-504  
**Parsing:** `sdqctl/core/conversation.py` (ConversationFile dataclass)

---

## Scope Boundaries

### In Scope
- RUN directive execution (`subprocess.run` handling)
- Related directives: RUN-ON-ERROR, RUN-OUTPUT, RUN-TIMEOUT, ALLOW-SHELL
- Error recovery and partial output capture
- Security considerations for command execution
- Testing of RUN directive behavior

### Out of Scope (for this topic)
- `sdqctl run` CLI command structure
- Adapter communication (AI interactions)
- Other step types (PROMPT, PAUSE)
- Session/checkpoint handling

---

## Improvement Chunks

Work is organized by priority within each category. Complete one chunk before moving to the next.

### 1. Reliability & Error Recovery

#### R1: Timeout Partial Output Capture (P1-2) ⏳
**File:** `sdqctl/commands/run.py` lines 489-496  
**Issue:** When RUN times out with `RUN-ON-ERROR continue`, no partial output is captured

```python
except subprocess.TimeoutExpired:
    logger.error(f"  ✗ Command timed out")
    progress(f"  ✗ Command timed out")
    
    if conv.run_on_error == "stop":
        # ... stops execution
    # ELSE: continues but NO partial output captured for AI context
```

**Current behavior:** Timeout loses all output, AI gets no feedback  
**Desired behavior:** Timeout ALWAYS captures partial output (special case, ignores RUN-OUTPUT setting)

**Design decision:** Timeout is special - partial output is always valuable for debugging, regardless of RUN-OUTPUT setting.

**Tasks:**
- [ ] Research `subprocess.TimeoutExpired` attributes (stdout, stderr available?)
- [ ] Use `Popen` with `communicate(timeout=)` to capture partial output
- [ ] Add partial output to session context on timeout (always, not gated by RUN-OUTPUT)
- [ ] Add tests for timeout with partial output capture

#### R2: RUN Failure Context Enhancement ⏳
**File:** `sdqctl/commands/run.py` lines 465-476  
**Issue:** On failure, stderr is only shown to console, not added to AI context

**Design decision:** Respect `RUN-OUTPUT` setting, but change default from `always` to... wait, current default IS `always`. Verify this is working correctly.

**Current defaults:**
- `run_output: str = "always"` ← already defaults to always

**Tasks:**
- [ ] Verify failure output is added to context when RUN-OUTPUT is "always" or "on-error"
- [ ] Include exit code in structured format
- [ ] Add tests to confirm failure context behavior

### 2. Security

#### S1: Shell Injection Prevention ✅ DONE
- Added `ALLOW-SHELL` directive (default: false)
- RUN uses `shlex.split()` by default (no shell injection)
- Shell features (pipes, redirects) require explicit `ALLOW-SHELL true`
- 9 tests added in `tests/test_run_command.py`

#### ~~S2: Command Allowlist/Denylist~~ SKIPPED
**Decision:** Skip entirely. RUN is local execution by sdqctl, not AI-controlled. ALLOW-SHELL is sufficient security for untrusted workflows.

### 3. Ergonomics

#### E1: RUN Output Limit ⏳
**File:** `sdqctl/commands/run.py` lines 477-487  
**Issue:** No limit on output size - massive logs could overwhelm context

**Design decision:** 
- Default: no limit (matches current behavior)
- Add `RUN-OUTPUT-LIMIT` directive for users who want limits
- Syntax: `RUN-OUTPUT-LIMIT 10K`, `RUN-OUTPUT-LIMIT none`
- Future: add truncation modes (`head`, `tail`, `head+tail`)

**Tasks:**
- [ ] Add `run_output_limit` field to ConversationFile (default: None = unlimited)
- [ ] Parse `RUN-OUTPUT-LIMIT` directive
- [ ] Truncate output before adding to context if limit set
- [ ] Add tests for output limiting

#### ~~E2: RUN Working Directory~~ SKIPPED
**Decision:** Skip - users can `cd subdir && command` with ALLOW-SHELL or use wrapper scripts.

### 4. Code Quality

#### Q1: Subprocess Handling Duplication ⏳
**File:** `sdqctl/commands/run.py` lines 430-453  
**Issue:** Similar subprocess.run() call duplicated for shell vs non-shell

```python
if conv.allow_shell:
    result = subprocess.run(command, shell=True, ...)
else:
    result = subprocess.run(shlex.split(command), shell=False, ...)
```

**Tasks:**
- [ ] Extract to helper function with shell parameter
- [ ] Reduce code duplication
- [ ] Make timeout and capture_output configurable per-call

### 5. Testing

#### T1: RUN Directive Integration Tests ⏳
**File:** `tests/test_run_command.py`  
**Current:** 18 tests, but RUN subprocess paths have gaps

**Tasks:**
- [ ] Test RUN with successful command (verify output in context)
- [ ] Test RUN with failing command + RUN-ON-ERROR stop
- [ ] Test RUN with failing command + RUN-ON-ERROR continue
- [ ] Test RUN with timeout + partial output
- [ ] Test RUN-OUTPUT modes (always, on-error, never)
- [ ] Test RUN-TIMEOUT parsing (seconds, "30s", "2m")
- [ ] Test ALLOW-SHELL with pipes and redirects

---

## Completed This Session

(Updated after each cycle)

---

## Lessons Learned

(Updated after each cycle with barriers, workarounds, insights)

---

## Next Session Command

```bash
cd /path/to/sdqctl
sdqctl -vv cycle -n 3 --adapter copilot \
  --prologue @reports/run-improvements-focus.md \
  --epilogue "Update @reports/run-improvements-focus.md with completed items and lessons learned" \
  examples/workflows/progress-tracker.conv
```

---

## References

- `sdqctl/commands/run.py` - main implementation
- `reports/improvements-tracker.md` - full improvements list
- `examples/workflows/progress-tracker.conv` - cycle workflow
- `tests/test_run_command.py` - existing tests
