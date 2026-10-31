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

- [x] Record actual administrator compatibility paths and remaining framework limits; handle user-reported failing functions if supplied.
- [x] Rebuild/replay the complete fork patch for current and a future mechanical branding revision; independently review metadata.
- [x] Main-session fresh full tests and shared Native AOT build; isolated startup/GUI acceptance and normal fixture teardown.
- [x] Preserve production profile, attempt normal exit and honor a separately authorized force-close only if needed, stage the exact verified complete runtime and launch it.
- [x] Publish through authorized own-repository delivery and verify exact source, receipts, packages and update feed.
- [x] Fresh final independent review, final main-session checks and honest handoff. The separate user-performed reboot acceptance below has now been verified.
- [x] User-performed real reboot/logon acceptance: new Windows boot, canonical task launch of installed7,2.950s before Explorer, bounded assessment2328ms/HighHigh/None,42steps0failed and no erroneous notice/relaunch verified2026-10-31.

Historical Task1 source gate: fea05ab5/06a75ddf; initial full5938/5938, focused218/218. Independent review0Critical/0Important/0Minor after M1 ordering fix. Native/GUI were pending at that checkpoint; current integrated evidence follows. Actual reboot evidence is recorded in the integrated acceptance below.

Task2 final source gate: ea4cd788/6322bd81,30/30 focused incl fresh pure helper; encoding-aware recovery XML verified. Independent review0Critical/0Important/0Minor. Actual Apply/Repaired and post-launch Preview/AlreadyRepaired verified. Final main shared management162 and C#5939 all passed.

Integrated acceptance: exact0cdb78b9/main shared6101PASS, Native synthetic GUI and production replacement/startup normalized. Production ordinary shutdown351 was followed by user-specific force-close permission, recorded honestly. Cloud41190303508/all4jobs/all9assets verified. User-performed real reboot/logon passed2026-10-31; one observed boot is not exhaustive future-timing coverage.
