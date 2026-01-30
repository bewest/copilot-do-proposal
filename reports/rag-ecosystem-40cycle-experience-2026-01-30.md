# 40-Cycle backlog-cycle-v2 Experience Report

**Date**: 2026-01-30  
**Workspace**: rag-nightscout-ecosystem-alignment  
**Workflow**: `workflows/orchestration/backlog-cycle-v2.conv`  
**sdqctl Version**: 0.1.x (copilot adapter)

## Executive Summary

A marathon 40-cycle autonomous documentation session that ran for **3 hours 50 minutes**, processing **1,663 turns** with **137M input tokens**. The session completed a comprehensive bottom-up accuracy verification of the Nightscout ecosystem documentation, producing **175 commits**, **110 completed backlog items**, **247 unique gaps**, and **199 requirements**.

Key insight: The backlog-cycle-v2 workflow proved capable of sustained autonomous operation at scale, maintaining coherent context across 40 cycles through effective compaction and phase preservation.

## Session Statistics

| Metric | Value | Notes |
|--------|-------|-------|
| **Duration** | 230 min (3h50m) | 13,808 seconds |
| **Cycles** | 40/40 | 100% completion |
| **Phases completed** | ~360 | 9 phases × 40 cycles |
| **Turns** | 1,663 | ~41.6 turns/cycle |
| **Input tokens** | 136,870,789 | 137M |
| **Output tokens** | 566,213 | 0.57M |
| **Token ratio** | 242:1 | Consistent with prior runs |
| **Tool calls** | 2,021 | ~50.5 tools/cycle |
| **Failed tools** | 7 | 0.35% failure rate |
| **Commits** | 175 | ~4.4 commits/cycle |
| **Avg time/cycle** | 5.75 min | Good pacing |

## Workflow Effectiveness

### backlog-cycle-v2 Design Strengths

The workflow's 9-phase structure proved highly effective for autonomous operation:

1. **Phase 0 (State Check)**: Git and queue hygiene before work—prevented dirty state accumulation
2. **Phase 1 (Task Selection)**: Priority-ordered selection from LIVE-BACKLOG → Ready Queue → Domain backlogs
3. **Phase 2 (Execute)**: Core work phase with tool access
4. **Phase 3 (Verify)**: Validation using ecosystem tools
5. **Phase 4 (Documentation)**: Update 5 facets consistently
6. **Phase 5 (Backlog Hygiene)**: Move items to Processed table
7. **Phase 6 (Commit)**: Git commit with semantic message
8. **Phase 7 (Candidate Discovery)**: Find new work items
9. **Phase 8-9 (Queue/Archive)**: Route items, integrate findings

### Key Workflow Features That Enabled Scale

| Feature | Impact |
|---------|--------|
| `ON-CONTEXT-LIMIT compact` | Automatic compaction preserved coherence across 40 cycles |
| `COMPACT-PRESERVE git-status selected-task findings` | Critical state survived compaction |
| `RUN-ON-ERROR continue` | Tool failures didn't halt progress |
| `RUN-OUTPUT-LIMIT 20K` | Prevented context bloat from verbose output |
| LIVE-BACKLOG priority | Human requests processed first |

### Commit Distribution by Type

| Type | Count | Percentage |
|------|-------|------------|
| `docs:` | 53 | 30% |
| `chore:` | 38 | 22% |
| `feat:` | 9 | 5% |
| `feat(conformance):` | 4 | 2% |
| Level-based verification | 20+ | 11% |
| Other | ~51 | 30% |

## Scale Observations (40-Cycle Endurance)

### What Worked at Scale

1. **Consistent pacing**: ~5.75 min/cycle average maintained throughout
2. **Token efficiency**: 242:1 input/output ratio (similar to shorter runs)
3. **Low failure rate**: 0.35% tool failures (7/2,021)—robust error handling
4. **Coherent task selection**: Workflow correctly prioritized across 6 domain backlogs
5. **Automatic grooming**: Backlog hygiene phases kept queues healthy

### Comparison with Prior Runs

| Run | Duration | Cycles | Commits | Turns | Termination |
|-----|----------|--------|---------|-------|-------------|
| backlogv2-run5 (2026-01-26) | 40 min | 4.5 | 11 | 353 | Rate limit |
| **This session** (2026-01-30) | 230 min | 40 | 175 | 1,663 | Complete |

**Observation**: This session ran 5.75× longer with 8.9× more cycles, demonstrating that rate limits from shorter sessions were not fundamental blockers—just timing. The 40-cycle run completed all requested cycles.

### Efficiency Metrics

| Metric | This Run | Prior Run | Delta |
|--------|----------|-----------|-------|
| Min/cycle | 5.75 | 8.9 | -35% |
| Commits/cycle | 4.4 | 2.4 | +83% |
| Turns/cycle | 41.6 | 78.4 | -47% |
| Tools/cycle | 50.5 | 97.3 | -48% |

**Analysis**: This session was more efficient—fewer turns and tools per cycle, but higher commit output. The bottom-up verification methodology (systematic level progression) likely contributed to efficiency.

## Documentation Accuracy Outcomes

### Bottom-Up Verification Framework

The session implemented a 6-level bottom-up accuracy verification:

| Level | Focus | Items | Accuracy |
|-------|-------|-------|----------|
| **Level 2** | Terminology matrix sampling | 3 | 100% |
| **Level 3** | Domain deep-dive verification | 7 | 100% |
| **Level 4** | GAP-* claim verification | 5 | 100% |
| **Level 5** | REQ-* traceability audit | 4 | 83-100% |
| **Level 6** | Document coherence audit | 4 | 40-100% |

### Artifacts Produced

| Category | Count | Examples |
|----------|-------|----------|
| Domain deep-dives | 67 files | `bolus-wizard-formula-comparison.md`, `cgm-remote-monitor-design-review.md` |
| Traceability files | 25 files | `aid-algorithms-gaps.md`, `sync-identity-requirements.md` |
| Mapping documents | 122 files | Project-specific field mappings |
| Unique gaps | 247 | GAP-ALG-*, GAP-API-*, GAP-SYNC-*, etc. |
| Unique requirements | 199 | REQ-*-001 through REQ-*-035 per domain |

### Algorithm Comparison Deep-Dives

The session produced systematic comparisons across AID systems:

| Comparison | Systems | Gaps | Requirements |
|------------|---------|------|--------------|
| Bolus wizard formula | Loop vs AAPS | 4 | 3 |
| Autosens/Dynamic ISF | oref0 vs Loop RC | 4 | 3 |
| Carb absorption model | Model-based vs deviation | 4 | 3 |
| Prediction curves | Single vs 4 curves | 4 | 3 |
| Temp basal vs SMB | Loop vs oref0 | 4 | 3 |
| Insulin model | Exponential formula | 4 | 3 |
| Target range handling | Dynamic vs static | 4 | 3 |
| Override/temp target sync | eventType differences | 4 | 3 |
| Profile schema | Time format/safety limits | 5 | 4 |
| Devicestatus schema | Loop vs oref0 | 4 | — |

### Traceability Growth

```
traceability/ changes: 18 files, +11,223 / -4,504 lines
```

Net addition of ~6,700 lines of traceability documentation.

## sdqctl Tooling Feedback

### What Worked Well

| Feature | Effectiveness | Notes |
|---------|---------------|-------|
| `iterate -n 40` | ✅ Excellent | Ran full 40 cycles without intervention |
| `COMPACT-PRESERVE` | ✅ Critical | Preserved state across compactions |
| `RUN-ON-ERROR continue` | ✅ Essential | 7 failures didn't halt session |
| `RUN-OUTPUT-LIMIT` | ✅ Helpful | Prevented context overflow |
| Copilot adapter | ✅ Stable | No adapter-level failures |
| `-vvv` logging | ✅ Useful | Detailed session reconstruction possible |

### Areas for Improvement

| Issue | Impact | Recommendation |
|-------|--------|----------------|
| No mid-run checkpoint | Low | Add `--checkpoint-every N` for long runs |
| Rate limit visibility | Low | Session completed, but metric for margin would help |
| Tool failure diagnostics | Low | 7 failures—unclear which tools failed |

### Integration Observations

The session demonstrated tight integration between sdqctl and workspace tooling:

```bash
# Tools used successfully throughout session
python tools/queue_stats.py        # Queue health monitoring
python tools/doc_chunker.py        # File size checks
sdqctl verify refs                 # Reference validation
git status/commit                  # Version control
```

## Lessons Learned

### 1. Bottom-Up Verification is Efficient

The leveled approach (Level 2 → 6) ensured foundational claims were verified before higher-level documents. This prevented cascading errors and made each verification cycle more efficient.

### 2. Backlog Hygiene Enables Long Runs

The workflow's Phase 5 (Backlog Hygiene) and Phase 7 (Candidate Discovery) kept work flowing. Without automatic queue replenishment, the 40-cycle run would have stalled.

### 3. LIVE-BACKLOG Priority Works

Human requests injected via LIVE-BACKLOG were processed first—the 12 algorithm comparison deep-dives were all human-initiated and completed.

### 4. Compaction Preserves Coherence

Despite 137M input tokens across 40 cycles, the session maintained coherent understanding of the ecosystem through effective compaction. The `COMPACT-PRESERVE` directive was essential.

### 5. Tool Failure Resilience Matters

The 0.35% tool failure rate (7/2,021) was absorbed by `RUN-ON-ERROR continue`. In a 40-cycle run, even rare failures would accumulate without this setting.

## Recommendations

### For sdqctl Development

1. **Add `--checkpoint-every N`**: Save session state every N cycles for long runs
2. **Expose tool failure details**: Which 7 tools failed and why?
3. **Rate limit forecasting**: Estimate remaining capacity for long sessions

### For Workflow Authors

1. **Use COMPACT-PRESERVE liberally**: List all state that must survive compaction
2. **Include hygiene phases**: Backlog grooming and candidate discovery enable long runs
3. **Set RUN-OUTPUT-LIMIT**: Prevents context bloat from verbose tools
4. **Level your verification**: Bottom-up (foundational → derived) is more efficient

### For Long-Running Sessions

1. **Use `--introduction`**: Set session goals upfront for coherent prioritization
2. **Prepare LIVE-BACKLOG**: Human requests get priority treatment
3. **Monitor with `-vvv`**: Detailed logging enables post-session analysis
4. **Expect ~5-6 min/cycle**: Budget accordingly for large `-n` values

## Conclusion

The 40-cycle backlog-cycle-v2 session demonstrates that sdqctl can effectively orchestrate long-running autonomous documentation workflows. The combination of structured phases, automatic compaction, and error resilience enabled 3+ hours of productive work producing 175 commits of verified, traced documentation.

The bottom-up verification methodology proved particularly effective—starting from terminology and mapping verification (Level 2-3), through gap and requirement audits (Level 4-5), to document coherence checks (Level 6). This systematic approach achieved 100% accuracy on foundational levels while surfacing coherence issues in forward-looking proposals.

Key metrics to remember:
- **5.75 min/cycle** average pacing
- **4.4 commits/cycle** productivity
- **0.35% tool failure rate** resilience
- **242:1 token ratio** efficiency

The workflow is ready for production use on similar documentation verification tasks.

---

## Appendix: Command Used

```bash
time sdqctl -vvv iterate \
  --introduction "We want a series of iterations and items on appropriate backlogs to evaluate from a 'bottom up' approach starting with first evidence sources and mappings to analyses, to proposals and gaps and traceability and designs: Add to appropriate queue[s]: { FOR EACH SECTION of topical domains and work represented in the docs, verify and adjust to increase accuracy, cohesivity and comprehension with relevant documents against the evidence. Make sure to use the tooling to help verify the accuracy and claims. }

Add items to the queue[s] as appropriate to ensure a thorough and methodical review of accuracy and cohesion across the ecosystem backed by easy verification using the tools.
 * When not possible, make sure the docs on tooling proposals outline what is needed, either in terms of updating docs or updating tools or proposals for the sdqctl team who has provided many features and willing to provide more if they are clearly expressed from experience." \
  workflows/orchestration/backlog-cycle-v2.conv -n 40
```

## Appendix: Session Tail Output

```
Total messages: 1069
16:37:43 Done in 13807.8s
16:37:43 [INFO] sdqctl.adapters.copilot: [backlog-cycle-v2:40/40:P13/13] Session complete: 1663 turns, 136870789 in / 566213 out tokens, 2021 tools (7 failed)

real 230m9.149s
user 16m0.536s
sys 1m9.475s
```
