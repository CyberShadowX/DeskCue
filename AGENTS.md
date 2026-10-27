# DeskCue development rules

## Authorized migration (2026-10-27)

The user explicitly approved replacing the former WPF DeskCue with the complete
DeskBox-based DeskCue fork, including product renaming, upstream synchronization,
cloud releases, and a local build fallback. This is the one-time migration of
project-specific rules. The old project and its instructions remain in the local
archive; the upstream author's machine paths and Git identity are not adopted.

## Controller workflow

- Work under F:\AI\AIProjects. Confirm repository, branch, and status before edits.
- One Controller owns requirements, integration, verification, and reporting.
- For new work, discuss and refine scope until the user says exactly
  `方案确认，开始执行`. The current migration has already received that approval.
- The approved implementation proceeds without repeated internal-plan approval.
- Preserve unrelated changes and local user data. Never force-kill DeskCue or the
  separately installed DeskBox. Use normal application shutdown for owned builds.
- Implement -> test -> independent review -> fix -> re-review for each task.
  Critical/Important findings block advancement. Use a fresh final reviewer and
  fresh main-session verification. Record remaining Minor findings honestly.
- Source synchronization is only from Tianyu199509/DeskBox; remote writes and
  releases are only to the user's CyberShadowX/DeskCue repository. Never push
  upstream. Never upload personal data, private backups, credentials or logs
  containing personal content. No paid services or signing identities are adopted.
- Keep original copyright, GPL-3.0-only, third-party notices and explicit upstream
  attribution. DeskCue is a derived work, not an independent-originality claim.
- Do not silently remove an upstream capability. Fork-specific changes are limited
  to branding, separate application identity, delivery, and replacing services
  controlled by the upstream author with appropriate DeskCue destinations.

## Build and release

- Solution: DeskCue.sln. WinUI3/.NET10/Rust, explicit x64 or ARM64 architecture.
- SDK/toolchain pins and source provenance are authoritative. Do not run AnyCPU.
- Local tooling may be placed at F:\AI\AIProjects\.deskcue-tools; use process-only
  environment changes. No global PATH/toolchain changes are required.
- Main build/release entry: tools/Publish-DeskCue.ps1; shared implementation under
  deskcue/. Cloud and local builds use the same source selection, transformation,
  version, tests and package generation. No bare publish shortcut for retail.
- Full Native AOT/offline runtime packaging replaces the former WPF single-file
  contract. A complete runtime directory and an installer are expected.
- An installer/source-sync candidate is not a successful update until verified.
  Hash/download/build failures preserve the current installed application.
- Do not run installer auto-organization, move desktop files, enable startup,
  notifications or other user/system actions just to obtain smoke evidence.
- Record verified results, source/package hashes, review verdicts and limits in
  docs/HANDOFF.md. Never upgrade an unexecuted/manual boundary to automated proof.
