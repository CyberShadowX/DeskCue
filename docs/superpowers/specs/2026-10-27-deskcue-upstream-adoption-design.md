# DeskCue upstream adoption design

Approved scope: user confirmation `方案确认，开始执行` on 2026-10-27 after choosing
CyberShadowX/DeskCue, cloud delivery plus a local build fallback.

## Intent

Replace the former WPF product with the complete DeskBox application. Preserve
upstream functionality/layout/interaction while giving the fork the DeskCue name
and its own operational identity. Subsequent upstream stable releases must be
reproducibly rebuilt as DeskCue, rather than installing DeskBox binaries.

## Approaches

The user selected a complete source fork over reimplementing DeskBox in WPF.
Cloud builds provide normal updates; local builds are an explicit fallback using
the same recipes. Directly installing upstream packages would undo branding.

## Baselines and preservation

- User fork: https://github.com/CyberShadowX/DeskCue; public, default main.
- Upstream: https://github.com/Tianyu199509/DeskBox.
- Initial fork source: 1fdf0bd9f84affe889318173a7f3141843c79604, version 1.5.9;
  the commit following v1.5.9 only corrects the release documentation test count.
- Legacy source e98b255d356c56e7ea23946dd9448793238964ec is archived in a
  verified all-refs Git bundle, with the former release executable and a SQLite
  backup made through SQLite's backup API. Old data is not automatically imported.
- Develop in an independent clone, then replace the main workspace only after
  verification. Preserve old linked worktrees and private evidence outside the
  public repository. Never stop the separately installed DeskBox by force.

## Branding and identities

Transform paths, C#/XAML namespaces, native module names/exports, solution/build
references, localized product names, installer/updater names, resources, registry,
startup, application-data, mutex and IPC strings together. Use fixed new GUIDs
for fork-owned installer, COM/toast and package identities; leave Windows SDK and
third-party interface GUIDs unchanged. The direct distribution is authoritative;
the original Microsoft Store product/publisher and signing identities are not
ours. Preserve original GPL/copyright/third-party notices and explicit upstream
attribution. Do not relabel upstream donation/QR/payment/contact endpoints as ours.

Keep a deterministic transformation in deskcue/brand.py. It operates only on a
fresh source tree, excludes .git/build artifacts/management overlays, preserves
binary assets and source text encoding, and produces a provenance record. Future
updates regenerate from upstream source with the same checked-in recipe, avoiding
unbounded manual merge chains. Unknown/missing critical anchors fail closed.
Every fork-specific runtime and test change beyond mechanical branding is stored
as a checked patch under deskcue/patches; fresh generation must apply all patches
with a successful preflight. A source-only manual fix without a replayable patch
does not meet this contract.

## Version and delivery

Keep upstream version and DeskCue revision separately. DeskCue numeric version is
four components (initial 1.5.9.1), and its release tag is v1.5.9.1. Every release
records upstream tag/commit, branding revision, fork source commit and SHA256s.

Normal update checks/downloads are only from CyberShadowX/DeskCue. Update manifest,
GitHub fallback, manual-download links, asset-name matching and allowed download
URLs all use this fork. Preserve upstream architecture, HTTPS, hash and installer
validation behavior; do not allow DeskBox assets as an update fallback. A new
upstream release is a candidate until the DeskCue package is built and verified.
No embedded GitHub credentials; public update downloads require no account login.

## Synchronization and cloud build

Schedule a lightweight upstream stable-release check every six hours, also expose
manual workflow_dispatch. Ignore drafts/prereleases. Build only when a new source
or branding revision is pending. Resolve the release tag to a commit and stage a
fresh full source tree; copy only tracked DeskCue management overlays. Do not copy
local data or untracked files. No blanket Sync fork over the branded main branch.

Use standard hosted Windows builders. Read-only build jobs run the shared tests,
branding checks, Rust/native/AOT publish and Inno package build. Release/source
write permission is limited to a separate delivery job after all required jobs
pass. Publish matching DeskCue source, immutable version metadata, x64/ARM64
packages and checksums. Source advancement is a normal fast-forward commit; never
force-push a shared branch or replace an existing release's different bytes.
Conflicts, missing anchors, test failures, hash failures or concurrent source
changes leave the last good release/current installation intact.
Git ref promotion and GitHub release publication are separate operations. If a
source/tag push succeeds but final publication fails, record a pending delivery;
the latest published release remains authoritative and the next/manual run must
retry it rather than treating the advanced source version as already delivered.
Reuse matching staged/draft assets; never replace existing different bytes.

## Local route

tools/Publish-DeskCue.ps1 is the normal local release entry and calls the shared
deskcue build recipe. A separate explicit local-sync command stages new upstream
source using the same transformation. Validate it before promoting or installing.
It never silently starts a large compilation after a cloud download failure.
Portable SDK/Rust/Inno tools live inside the canonical project under .deskcue-tools
(updated by the user's 2026-10-29 storage instruction). Existing
VS2022 x64 C++/Windows SDK prerequisites are usable. Local ARM64 may require extra
C++ tools; cloud ARM64 validation must be reported separately from local x64.

## Source-owned services

Use the fork's GitHub repository/releases/issues for product links. Original
author-controlled feedback/statistics/payment/Store endpoints cannot become
DeskCue services merely by renaming a host. Preserve upstream credit, hide or
replace those owner-specific surfaces appropriately, and prevent production
diagnostics from being posted to the original author's backend by default.

## Verification and completion

Task gates: implement, relevant tests, independent review, fix/re-review. Final
gate: fresh reviewer plus fresh Controller tests/build/package and safe runtime
smoke. Test actual name, independent instance identity and fork update destination.
Exercise bad hash/download/foreign asset and build-failure preservation paths.
Verify cloud execution and download results from the actual user repository, not
only YAML text. Record every unverified platform/GUI/manual boundary honestly.
Keep docs/HANDOFF.md and a short Chinese operator guide current. No claim that
an unattended schedule can run forever: GitHub may disable inactive workflows.
