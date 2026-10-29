# Project-local build environment implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Recreate the deleted build environment entirely inside the existing DeskCue project and make future setup/builds use that location.

**Architecture:** Resolve the canonical project directory from Git's common directory, so linked worktrees share one ignored `.deskcue-tools` under the main project. A shared environment helper supplies contained process-only tool/cache/temp paths. A repeatable initializer downloads and verifies pinned tools. Existing installed MSVC/Windows SDK and shared Git/Python/PowerShell are read-only prerequisites.

**Tech Stack:** PowerShell7, Python behavioral tests, .NET SDK10.0.402, Rust1.96.0, portable Inno Setup6.7.3, existing x64 MSVC/Windows SDK.

**Spec:** The user's 2026-10-29 instruction: both parent directories were manually deleted; all project-owned content, including compilation tools, must live inside `F:/AI/AIProjects/DeskCue`; recreate the compilation environment there.

## Global constraints

- Initial repository: main `79f960e9594b1b8375497f9f1fc614c18cf117c6`, clean.
- Isolated implementation: `.artifacts/local-environment-worktree`, branch `codex/project-local-environment`.
- Canonical local tools: `F:/AI/AIProjects/DeskCue/.deskcue-tools`.
- Project-owned downloads, tool homes, package caches, temporary files, evidence and future archives stay below the canonical project. Never recreate sibling `.deskcue-tools` or `.archives`.
- Do not recreate the deleted old project/data backups or claim they remain recoverable.
- Do not move the system's installed shared prerequisites or the application's existing user data.
- Do not modify product source, version/identities, upstream patch, current published runtime or remote repositories/releases.
- Initialization/build environment changes are process-only. Prevent .NET's first-use PATH modification with `DOTNET_ADD_GLOBAL_TOOLS_TO_PATH=0` before invoking dotnet.
- Remove only the exact obsolete user-PATH entry for the deleted parent tool directory, with a snapshot and compare-before-write; preserve every other entry.
- No force-kill, startup registration, installer auto-organization or GUI smoke actions.

## Review focus

- A nested linked worktree must reuse the canonical main-project tools, not create another toolset or write to the project's parent.
- Unsafe roots or directory links must fail before writing. Existing contained Rust file links are allowed without traversal outside the tool root.
- Truncated/incorrect downloads and invalid signatures must fail before tool execution or success receipts.
- Re-running initialization must verify existing pins and preserve a usable installation on failure.
- Local process environment must be restored on success/failure; hosted builds must retain their configured tools when local portable tools are absent.

### Task 1: Canonical tool location and environment

**Owner:** local_environment_impl.

**Files:** `deskcue/LocalEnvironment.ps1`, `deskcue/Build-DeskCue.ps1`, `.gitignore`, focused new `deskcue/tests` coverage.

- [x] Specify and share the helper API with the initializer owner.
- [x] Observe failing behavioral tests for root/worktree containment and environment restoration.
- [x] Implement canonical root resolution, project-local write paths and first-use suppression.
- [x] Preserve hosted explicit tools/caches when portable tools are absent.
- [x] Ignore local tools/future archives and run focused plus existing helper tests.
- [x] Independently review spec compliance/code quality; resolve all Critical/Important findings.

### Task 2: Repeatable verified bootstrap

**Owner:** build_environment.

**Files:** `tools/Initialize-DeskCueEnvironment.ps1`, bootstrap-specific helper/test files if necessary; no overlap with Task1 ownership.

- [x] Use the shared canonical-root/environment contract.
- [x] Stage official pinned downloads under local tools, verify hashes/signature before execution.
- [x] Install .NET/Rust/Inno locally without global PATH or installer registration changes.
- [x] Support verification/idempotent reuse and record actual tool versions/receipts.
- [x] Run behavioral negative/probe tests and parser checks before actual downloads.
- [x] Independently review before Controller executes bootstrap.

### Task 3: Integrate, initialize and verify

**Owner:** Controller.

- [x] Confirm both deleted parent directories are absent; preserve the clean current project.
- [x] Integrate reviewed changes and clean the single obsolete PATH item with comparison guard.
- [x] Execute reviewed initialization with all new downloads/cache/temp files under the canonical project.
- [x] Run initializer verification again to prove reuse and exact version pins.
- [x] Perform a real x64 Release application/native Rust compile in a contained source checkout and verify package/cache/temp locations.
- [x] Run fresh environment/helper tests and confirm persistent environment, parent directories and published-runtime hashes.
- [x] Update AGENTS, usage guidance and HANDOFF with the new policy and actual results.
- [x] Fresh final independent review, fix/re-review, local verified commits. No remote push/release is needed for this local-environment task.

## Verification boundary

The existing ordinary Release C# test hosts can append `App.Log` to the real application profile. This task does not change product code or that pre-existing behavior. Environment/helper tests and real application compilation are required; the full C# runtime suite, NativeAOT publication/installer execution, and GUI acceptance are not re-run merely to validate tool location. Existing published1.5.9.4 bytes remain the accepted release.
