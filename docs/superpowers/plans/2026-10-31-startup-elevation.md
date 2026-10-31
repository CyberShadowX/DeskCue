# Startup Elevation Repair Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development or superpowers:executing-plans task by task.

**Goal:** Prevent a not-yet-ready Explorer from producing a false administrator warning, preserve valid startup context, and verify administrator compatibility honestly.

**Architecture:** Preserve unknown shell-token state until the current session's real shell is available. Reassess before user-visible decisions instead of using a permanent constructor snapshot. Recognize and migrate only demonstrably owned startup registrations; retain full-administrator operation without modifying UAC or accounts.

**Tech Stack:** WinUI3/.NET10/Rust, x64/ARM64 shared Native AOT delivery, project-local PowerShell tools and xUnit.

**Spec:** User approved this chat's diagnosed scope with `方案确认，开始执行` on 2026-10-31. Actual startup logs show DeskCue starting about three seconds before Explorer; Unknown was collapsed into false and cached. Live DeskCue, Explorer and MyDockFinder are all High integrity. The existing task has Source `DeskCue.LocalStartup.v1`, a SID-scoped `DeskCue-Logon-...` name, and no startup arguments.

## Global Constraints

- All code, tools, worktrees, caches and private evidence stay under F:/AI/AIProjects/DeskCue.
- Preserve Administrator account, UAC policies, personal data and unrelated changes; no force-kill of DeskCue, DeskBox or MyDockFinder.
- Only the user's CyberShadowX/DeskCue repository receives authorized source/releases; preserve GPL attribution and upstream pins.
- Normal shutdown, complete verified payload and shared publisher are required for local replacement.
- Unknown is not evidence of a lower-integrity shell or of a reliable unelevated restart.
- Scope includes current-owned startup repair and compatibility investigation; framework-limited drag/notifications must not be advertised as restored without implementation and actual evidence.

## Review Focus

- Explorer absent, inaccessible, from another session, or later restarting: no guessed mismatch or retry/relaunch loop.
- Unknown becoming High versus Medium: only the real known mismatch may trigger the corresponding notice/relaunch path.
- Shutdown and dispatcher lifetime during delayed reassessment: no stale windows or background UI calls.
- Startup registration ownership: never adopt/delete another installation's or another user's task; preserve startup intent and arguments.
- Tests/fixtures must use synthetic data and isolated logs; same-integrity operation does not establish WinUI XAML drag support.

### Task 1: Unknown-aware shell assessment and startup decisions

Files: DragDropPermissionService.cs, App.xaml.cs/App.Startup.cs and a focused App elevation partial if appropriate; StartupElevationGateTests and focused lifecycle/policy tests.

- [x] Run a focused baseline; add regressions proving Unknown does not mean AppAboveShell or CanRelaunch.
- [x] Observe RED for Unknown -> High/Medium and persistent Unknown; add a testable bounded reassessment policy without real sleeps.
- [x] Use the real shell window/process in this session, preserve unknown state, and refresh decisions on the UI lifetime before showing notices.
- [x] Preserve startup/parent-wait arguments and avoid claiming a ShellExecute fallback really de-elevated.
- [x] Run focused tests/build, independently review, fix and re-review, then commit.

### Task 2: Owned legacy startup normalization

Files: tools/Repair-DeskCueStartup.ps1, pure emit/validate modes in tests/DeskCue.StartupUnicodeProbe and deskcue/tests/test_startup_repair.py. Production backend/service/reader remain unchanged; repair is explicit and strictly installation-owned.

- [x] Establish exact legacy ownership predicates from current task Source/name/SID/action/executable and compare-before-write state.
- [x] Add failing tests for correct adoption/arguments and refusal of foreign user/install/source/action/runlevel variants.
- [x] Normalize to supported startup registration without changing UAC, principal privilege or unrelated tasks; preserve explicit user-enabled startup intent.
- [x] Test/review/re-review before applying the approved repair to the actual owned task.

### Task 3: Integrated compatibility, packaging and acceptance

Files: fork patch/config/provenance/version/release notes, shared build records and docs/HANDOFF.md.

- [ ] Record actual administrator compatibility paths and remaining framework limits; handle user-reported failing functions if supplied.
- [ ] Rebuild/replay the complete fork patch for current and a future mechanical branding revision; independently review metadata.
- [ ] Main-session fresh full tests and shared Native AOT build; isolated startup/GUI acceptance and normal fixture teardown.
- [ ] Preserve production profile, normally exit current application, stage the exact verified complete runtime and launch it.
- [ ] Publish through authorized own-repository delivery and verify exact source, receipts, packages and update feed.
- [ ] Fresh final independent review, final main-session checks and honest handoff. Real reboot acceptance remains pending until actually performed with the user.

Task1 gate: commits fea05ab5/06a75ddf; initial full5938/5938, final focused218/218. Independent review0Critical/0Important/0Minor after M1 ordering fix. Native/GUI/reboot pending.

Task2 source gate: ea4cd788, latest26 synthetic+1 fresh purehelper passed, independent review0Critical/0Important/0Minor. Native read-only Preview validated the actual owned legacy task; no Apply/system task mutation yet. Historical management154 is not the final integrated count; shared build reruns the final suite.
