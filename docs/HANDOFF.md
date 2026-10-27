# DeskCue migration handoff

## Current checkpoint (2026-10-28)

The main workspace is now the complete DeskBox-based DeskCue fork:
`F:/AI/AIProjects/DeskCue`, branch `main`, own origin `CyberShadowX/DeskCue`.
The next public candidate is **1.5.9.3**, branding revision 3. Its complete local
retail build, native x64/ARM64 cloud delivery and final acceptance are pending.
Earlier successful builds are not acceptance of this candidate.

Prior source `6b6195c2be230e6951860ae02c293598d7ecb508` (1.5.9.2)
passed the actual local shared publisher: 5827 C# plus 108 management tests,
5935 passed, no failures or skips; Release build 20 warnings, no errors.
The full Native AOT payload has 394 files; installer and receipts are preserved.
The EXE SHA256 was
`cf0da26e93362d47e42c0c67f20ee7fdef6d9dcd5df9c0150dd3ef38348951f0`.
Evidence: `.artifacts/v2-publication.log` and the retained corresponding run
under `.artifacts/deskcue-release/win-x64/runs/`.

Actual CI40536288571 passed5827/5827. Delivery40536288591 completed its x64
5935-test/AOT/installer build, but ARM64 aborted after4315 passing tests because
of a native hang. That run produced no public release, version tag or feed.

Native ARM64 minidump/SOS analysis and controlled run40546464968 identified
Everything SDK CleanUp followed by another SDK call as the cause. The original
ARM64 DLL matches the official SDK bytes and is not replaced. The minimal
provider fix preserves the original bounded query drain, avoids process-global
CleanUp per provider and leaves the gate usable by in-flight work. Independent
round2 review passed0C/0I/0M; controlled drain RED, focused26/26 and five fresh
hosts each4/4 passed. The original search test and timeout remain unchanged.

Fresh-data historical release notes were also routed to nonexistent fork tags.
Only known three-part history now reads upstream notes; four-part fork releases
and installer/feed/download trust stay fork-owned. Controlled RED21 -> GREEN
116/116, no skips; independent re-review passed0C/0I/0M. Final source review
identified no other durable blocking finding.

Final complete patch:137807bytes, SHA256
`c60e809e4b21a730d8a00cb513fbf14688bdba4c327b8acf63cec5a54437d5bf`.
Fresh LF generation reproduced BASE3
`32a8074efccc8da8d74ff91f693c80d3177f10bb`; checked patch application exactly
reproduced all1697 indexed entries across src/tests/native/scripts/installer.
Evidence: `.artifacts/v3-final-product-replay.json`. Controller helper108/108
passed. Complete retail/native dualarch/cloud/runtime acceptance follows.

The user normally exited the1.5.9.2 test app. A read-only check confirmed
PID35212 absent/noDeskCue and the separate DeskBox PID45252 unchanged. This is
manual user confirmation plus process evidence, not automated tray-exit coverage:
`.artifacts/runtime-final/manual-exit-confirmation.json`.

## Approved scope and ownership

On2026-10-27 the user approved full replacement with the exact execution phrase,
including own-repository cloud releases and an explicit local fallback. Upstream
is `Tianyu199509/DeskBox`; its local push URL is disabled. All remote writes go
only to `CyberShadowX/DeskCue`. GPL-3.0-only, original copyright, third-party
notices and explicit upstream attribution remain in the app and source.

Fixed distinct package/installer/notification/instance identities coexist with
DeskBox. Updates accept only the fork's named installers and verified hashes.
Feedback opens the fork's public Issues; the upstream private feedback, payment
and Store identities are not adopted. Issues/Discussions were enabled and read
back; no issue, comment or discussion content was posted.

Cloud delivery checks stable upstream releases every six hours and on manual
dispatch. Candidates replay branding plus the required patch; native x64/ARM64
must both pass before atomic source/tag promotion and verified publication.
Frozen source/package bytes support publication retries. The app checks verified
DeskCue releases rather than installing an unmodified upstream binary; it has
no repository write credential. See [使用与更新](../deskcue/使用与更新.md).

## Legacy preservation and local safety

The complete former WPF project and Git history are preserved at
`F:/AI/AIProjects/DeskCue-legacy-20261027` (master `e98b255`). A separate all-ref
bundle, former EXE and consistent SQLite backup are under the private archive
`F:/AI/AIProjects/.archives/DeskCue/2026-10-27-before-deskbox`.
No old data is automatically imported or uploaded. Cutover transactionally moved
owned top-level entries and repaired owned worktrees; `.artifacts/cutover-result.json`.

`tools/Publish-DeskCue.ps1` builds the complete offline runtime and installer,
verifies source/tests/package bytes, preserves the previous release and blocks
replacement while its app is running. It never kills, installs or starts apps.
Portable tools are under `F:/AI/AIProjects/.deskcue-tools`, using process-only
environment changes. The former WPF single-file EXE contract no longer applies.

## Verification boundaries

Scoped independent reviews passed branding, update/service boundaries, path
safety, rollback, frozen-byte retry, source promotion and toolchain pins.
The reminder snapshot bug and cross-environment fixture assumptions were fixed
with controlled failing/passing evidence and review. Historical failed runs are
retained under ignored local evidence, not counted as successful releases.

WinUI preflights rendered DeskCue1.5.9.1/1.5.9.2 settings/about and verified
second-launch single-instance behavior. Normal automated tray exit passed for
1.5.9.1;1.5.9.2 required the manual exit above. Neither accepts1.5.9.3 or its feed.

Not performed: installer installation, real two-version installed upgrade,
startup/relogin, toast delivery, Windows10, physical DPI/multiple monitors,
all-language human review, exhaustive parity or user visual acceptance.
Packages are unsigned; no upstream signing identity is claimed. Existing
compiler/analyzer warnings remain. Original DeskBox is not closed or modified;
its global hotkey can conflict with DeskCue.

Future upstream workflow-file changes may require reviewed manual integration:
the delivery GITHUB_TOKEN cannot request workflow-file write permission. Such a
rejected atomic source/tag push occurs before release publication, preserving
the previous release/feed. Current HEAD-mode validation does not prove every
future two-parent upstream promotion will be accepted by GitHub. No extra token
or permission has been introduced. SDK disposal also retains the original
one-second drain cap; longer in-flight work remains an existing boundary.

## Final acceptance sign-off

- Workspace/legacy preservation: completed and checked.
- Identities, fork-owned services and replayable delivery: scoped reviews passed.
- Revision3 SDK lifecycle and historical notes fixes: scopedPASS0C/0I/0M.
- Revision3 complete local retail publication: pending.
- Revision3 actual dualarch cloud release/feed/hash verification: pending.
- Revision3 actual GUI, own-feed check and normal shutdown: pending.
- Fresh final independent review and Controller verification: pending.
- User visual/platform acceptance and manual boundaries above: not performed.
