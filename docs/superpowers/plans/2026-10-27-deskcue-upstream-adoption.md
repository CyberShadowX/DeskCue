# DeskCue upstream adoption implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> with the user's per-task independent-review requirement taking precedence.

**Goal:** Replace the legacy WPF application with the fully branded DeskBox fork
and prove repeatable cloud/local DeskCue delivery.

**Architecture:** Keep the upstream history; deterministic source transformation
and a small management overlay preserve the fork across stable upstream releases.
Cloud and local builds share the same scripts and validation. Separate upstream
candidate discovery from verified package installation.

**Tech Stack:** C#/WinUI3/.NET10.0.402, Windows App SDK2.5.1, Rust1.96.0,
Inno Setup6, Python standard library, PowerShell, GitHub Actions.

**Spec:** docs/superpowers/specs/2026-10-27-deskcue-upstream-adoption-design.md

## Global constraints

- Fork CyberShadowX/DeskCue; upstream Tianyu199509/DeskBox, never push upstream.
- Initial product version1.5.9.1; upstream source1fdf0bd9f84affe889318173a7f3141843c79604.
- Full offline Native AOT runtime; explicit x64/ARM64, no AnyCPU.
- Preserve legacy Git/data privately; no automatic import or desktop-file moves.
- Original GPL/copyright/third-party attribution stays intact.
- Never force-kill user apps or adopt upstream owner's identities/services.
- No credentials in the installed app; no paid builders/services.

## Review focus

- Distinct installer/notification/package identities must coexist with DeskBox.
- A renamed feed must still reject foreign DeskBox installers/unsafe URLs.
- Broken generation/build must preserve source/release/install; partial remote
  delivery must retain the published release/install and a retryable pending state.
- Original author's feedback/payment/Store services must not be relabeled ours.
- Cloud/local provenance and installer identities must stay identical.

## Task1: Reproducible source and identity migration

Files: deskcue/brand.py, deskcue/config.json, deskcue/tests/test_brand.py,
transformed src/tests/native/scripts/installer resources, AGENTS.md, README.md,
UPSTREAM.md, docs/HANDOFF.md.

Interfaces: brand.py --root PATH --config PATH transforms a fresh upstream tree;
config schema1 identifies product/repositories/upstream commit/version/revision
and exact fixed identity mappings. It writes deskcue/provenance.json.

- [ ] Capture upstream baseline restore/build/test with explicit x64/win-x64.
- [ ] RED: fixture tests for names/path references, protected notices/binaries,
  identity GUID mapping, malformed version/unsafe root/missing anchors.
- [ ] Implement transformation; run fixture tests and apply to fresh clone.
- [ ] Verify solution/native references and actual product build/test results.
- [ ] Independent review; fix/re-review blocking findings; commit.

## Task2: Fork-owned update and service boundaries

Files: src/DeskCue/Services/AppUpdateService.cs, FeedbackService.cs,
ViewModels/SettingsViewModel*.cs, Views/SettingsWindow.Feedback.cs,
tests/DeskCue.Tests/AppUpdateServiceTests.cs and fork-boundary tests.

Interfaces: existing IAppUpdateService remains; update URLs/allowlists and asset
prefix point only at the configured fork. Existing hash validation is preserved.
Feedback uses explicit user-directed GitHub issues instead of upstream POSTs.

- [ ] RED: own-release accepted; upstream/foreign asset rejected; missing/hash
  mismatch/cancelled download does not yield an installable package.
- [ ] Implement source-owned endpoint and identity boundaries.
- [ ] Capture every Task2 source/test delta as a checked deskcue/patches patch;
  fresh-source regeneration must replay it or stop before build/promotion.
- [ ] Verify own links, hidden upstream commercial identity and retained credit.
- [ ] Run relevant and full suite; independent review/fix/re-review; commit.

## Task3: Shared local generation and retail build

Files: deskcue/Sync-DeskCue.ps1, deskcue/Build-DeskCue.ps1,
tools/Publish-DeskCue.ps1, deskcue/tests/test_delivery.py, operator guide.

Interfaces: Sync takes explicit upstream ref/destination, validates paths and
clean source, archives the exact source, copies management overlay, invokes
brand.py and writes provenance. Build accepts Platform, DotNetPath, IsccPath and
optional SourceRoot; runs restore/build/tests/retail publish/Inno/hash verification
and writes a machine-readable receipt, without installing or launching silently.

- [ ] RED: unsafe staging path, failed child command, mismatched hashes/source
  provenance and concurrent source changes cannot produce successful receipts.
- [ ] Implement common scripts, portable-tool discovery and local wrappers.
- [ ] Run x64 full retail build; verify PE/package/manifest/hash and source receipt.
- [ ] Independent review/fix/re-review; commit.

## Task4: Cloud upstream monitor and verified releases

Files: .github/workflows/deskcue-upstream.yml, deskcue/cloud helpers/tests,
release metadata and operator documentation.

Interfaces: scheduled/manual detector outputs a resolved upstream commit and
numeric DeskCue version; read-only build matrix consumes shared Task3 scripts;
write-only delivery job publishes the matching source/packages/checksums after
all builds pass. Default branch advancement uses fast-forward only.

- [ ] RED: draft/prerelease/same version no build; candidate errors retain old
  release; no build job has contents-write or embedded long-lived credentials.
- [ ] Implement workflow and controlled source/release promotion.
- [ ] Push reviewed source to own fork; execute real workflow and inspect result.
- [ ] Verify released package name/hash/metadata and own updater discovery.
- [ ] Exercise ref-promotion-success/publication-failure recovery, existing draft
  assets and unchanged-published-release retry selection.
- [ ] Independent review/fix/re-review; commit.

## Task5: Integration, release and final acceptance

- [ ] Fresh final reviewer examines all changes and evidence, not summaries only.
- [ ] Controller runs fresh full tests/build/package and safe runtime inspection.
- [ ] Archive original workspace without losing linked-worktree state; switch
  verified clone to F:\AI\AIProjects\DeskCue, repair only owned paths as needed.
- [ ] Verify repository/remotes/version, final package and own runtime identity.
- [ ] Update HANDOFF/operator steps, review verdict and skipped boundaries.
