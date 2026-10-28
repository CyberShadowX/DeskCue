# DeskCue migration handoff

## Current checkpoint (2026-10-28)

The main workspace is now the complete DeskBox-based DeskCue fork:
`F:/AI/AIProjects/DeskCue`, branch `main`, own origin `CyberShadowX/DeskCue`.
Version **1.5.9.3**, branding revision3, has completed local retail publication
and native x64/ARM64 cloud publication. Product source is
`b05395c1f8a433391dbf30df6e5af46de1ec1cbe`. The incorrectly isolated GUI smoke
has been recovered, and a correctly isolated repeat passed About, own-feed
update, single-instance, actual Shell-icon right-click and normal tray Exit.
Fresh final independent review passed0Critical/0Important/0remainingMinor;
the earlier intermittent tray symptom is not claimed fixed.

## Verified revision3 release

- Controller actually ran `tools/Publish-DeskCue.ps1`:5859 C# plus108 helper
  tests,5967/5967 passed,0fail/skip; Release20warnings/0errors. FullNativeAOT
  x64 payload394files/131.3MiB, smoke harness false. Run:r-38a424ccb8544121.
- CI40553510130 passed5859/5859. Delivery40553514453 completed all four jobs:
  candidate122363305920, x64122365174730, ARM64122365174508, deliver122376662789.
  Each native build passed5967 tests with0fail/skip and fullAOT/offlineinstaller;
  cloud x64/ARM64 payloads394/390files. SDK10.0.402/Rust1.96.0/Inno6.7.1.
- Public [v1.5.9.3](https://github.com/CyberShadowX/DeskCue/releases/tag/v1.5.9.3),
  release425818590, published2026-10-27T18:10:45Z, stable/latest, tag at the exact
  source above. All9 public assets were actually downloaded and their hashes
  matched API digests/delivery output; the frozen ZIP's inventory, receipts,
  source bundle, installer bytes and checksum list were independently verified.
- x64 public installer33685299bytes SHA256
  `16b26ad6d566240e6ba160c73a1fb4e141579793d7213c8fe527ab57ac1f1ea1`;
  ARM64 installer33137052bytes SHA256
  `c224b8f0201e7a2340fd61b524163fa7ee93086cfbc45f14ceb8372c4679bf52`.
- Local EXE53549568bytes SHA256
  `dfe951c9e6bedb49b18acdb38d7ac27df03fe9451459724a20dc994992780e88`;
  local installer33697080bytes SHA256
  `f35776f60a073df66f55afbb929105fee4f5c94b754b6bcb9bf165d4702f8be8`.
  Local Inno6.7.3 and hosted6.7.1 builds have separate verified hashes; they are
  not a bit-for-bit reproducibility claim. Source/version/identities match.
- Both current and preserved previous local payloads were checked file by file:
  394/394 hashes match each corresponding frozen source publish directory.
  Independent reviewer also checked the actual replay index/disk and raw TRX;
  no remaining source Critical/Important/Minor findings at this checkpoint.
- Server workflow398346754 was read back active with cron `17 */6 * * *`.
  Actual scheduled runs40593240955 and40639466001 subsequently completed
  successfully. The latter passed helper tests/source detection; build and
  deliver were correctly skipped because there was no pending stable source.
  These prove real scheduled checks, not a future upstream-version promotion.

Evidence: `.artifacts/controller-v3-local-final.json`,
`.artifacts/controller-v3-csharp-check.json`, `.artifacts/v3-publication.log`,
`.artifacts/cloud-live/rev3-observer-40553514453/verification-summary.json` and
that directory's original logs, CI TRX, receipts, public assets and frozen archive.
Successful native jobs do not upload full payloads/native TRX/retail summaries;
their evidence is the original successful logs, strict contracts and downloaded
receipts/installers. CI raw TRX and Controller raw TRX were directly parsed.

## GUI smoke correction and actual recovery

The revision3 launcher supplied `DESKCUE_DEV_DATA_ROOT`, which is Debug-only.
Retail FullNativeAOT reads `DESKCUE_AOT_PREVIEW_DATA_ROOT`, independently of the
smoke-harness switch. Therefore PID44068 used the default local application
profile. The recorded requested F path was not its effective data root; that
isolation claim is withdrawn. Original script/evidence are preserved, with the
correction in `.artifacts/runtime-v3/isolation-correction.json`.

Actual GUI facts remain valid: DeskCue1.5.9.3 rendered; the real OneClickUpdate
button was invoked and returned current/latest1.5.9.3; a second observed launch
exited0 and left only the original PID. Images/UIA/commands are under runtime-v3.

Read-only audit identified this smoke's first-run standard Run registration
(initial effective state NotRegistered), new default JSON/layout/ledger,
empty managed folder and one automatic recovery ZIP. There was no configured
desktop shortcut/automatic organization; native notification support returned
before SDK registration. The pre-existing database, its WAL/SHM, old settings,
existing application root/data parent and existing log must remain untouched.
The exact prior Run raw value was not saved; a prior empty/whitespace value
cannot be excluded. The audit proves a newly enabled effective registration,
not byte-for-byte knowledge of every previous registry value.

The earlier Screen-saver input desktop/cursor error5 prevented automated exit.
After reporting that real tray right-click also failed, the user explicitly
authorized force-exit of that test. At2026-10-28T08:37:58Z the Controller checked
PID44068's exact path, start time and EXE hash, then ended only that instance.
Original DeskBox PID45252 remained intact. This is a recorded one-instance
exception, not a normal-exit claim or permanent change to the project rule.

Fresh preflight found that the originally empty managed child was already
absent; the parent remained the same attributed, ordinary empty directory.
The narrowly updated restoration tool permits only that exact missing leaf,
records it separately, and blocks other missing/unknown/reappearing entries.
Current settings/layout bytes had later edits and were preserved as current
data, rather than described as unused defaults. Tool SHA256:
`1F23E01F0167FFF3A388FD1322161D8238D54CAA528451DF67C33B81EB1E4F70`.
Parser/9 all-F synthetic cases and independent scoped review passed0C/0I/0M.

The Controller then actually ran fresh clear PlanOnly and Execute. All6 current
files were copied to a private F archive and hash-verified before any cleanup.
Exactly6 files and4 existing empty directories were removed; the already absent
leaf was not counted as deleted. Only the exact incident Run command was
removed. All7 pre-existing file bytes and unrelated Run fingerprints matched
before/after cleanup. Original profile/data parents were kept. The existing
log, including its smoke entries, was preserved rather than overwritten from
an older backup. The unknown prior raw Run empty/whitespace limit remains;
sequential guards are not OS atomic compare-and-delete.

Recovery evidence: `.artifacts/runtime-v3/forced-exit-authorized.json`,
`.artifacts/smoke-restore-plan/controller-final-pre-execute-plan.json`, and the
private `.artifacts/runtime-v3-default-profile-restored/` manifest, verified
copies and receipt. Receipt SHA256:
`977B17A9B6B5034DEA57A3A8CE74DA32C18FFB19D52595595E36CDC92EF0FC0D`.
These private files and logs are ignored by Git and were not uploaded.

## Correctly isolated revision3 runtime acceptance

On the accessible Default desktop, the reviewed launcher supplied the retail
`DESKCUE_AOT_PREVIEW_DATA_ROOT` and an explicit F managed root. PID52264 ran the
unchanged verified retail EXE. Newly written F log, data settings/layout and
startup ledger prove the effective root; actual settings kept startup, backup,
organization, shortcut, update notifications and global hotkey disabled.
Native notification bootstrap reported unsupported before registration; a
settings flag alone is not proof of no OS registration.

- Actual About rendered DeskCue1.5.9.3. Manual OneClickUpdateButton was observed
  disabled/checking, then enabled with current/latest1.5.9.3 and16:52 local check.
- An observed second process52924 exited0 and left only primary52264.
- One injected OS mouse right-click on the actual Shell DeskCue icon produced
  visible owned menu items. This is automated Shell input, not a synthetic
  callback message or a human test. A later such right-click followed by the
  real visible Exit item's Invoke completed normal shutdown at09:00:30Z.
  The log records ExitApplication, the F ledger records clean-exit, and actual
  process enumeration confirms no DeskCue remains. Its exit code was unavailable
  (null); no zero exit-code assertion is made for this normal-exit observation.
- The first exit helper searched only UIA root children and missed the flyout;
  the bounded helper enumerated visible HWNDs owned by the exact app PID before
  locating Exit. This was a test-helper correction, not a product-code fix.
- All7 original file hashes, all Run values, absence of C managed/recovery
  directories and original DeskBox identity matched the restored baseline after
  launch and normal exit. No all-system-zero-change claim is made.

Evidence: `.artifacts/runtime-v3-isolated/controller-verification-summary.json`,
original launch/UIA/images/update/single-instance/Shell-click/Exit records,
before/after known-profile fingerprints, and `.artifacts/runtime-v3-isolated-data/`.
The user's earlier tray failure was not reproduced in this fresh instance.
Its root cause remains unknown; one successful fresh-session test does not
prove that an intermittent or long-running failure has been fixed.

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
  passed. Retail/native dualarch/cloud evidence is above; recovery and corrected
  runtime acceptance passed. Fresh final independent sign-off passed0C/0I/0M.

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
- Revision3 complete local retail publication: PASS5967/0/0.
- Revision3 actual dualarch cloud release/feed/hash verification: PASS.
- Revision3 mistaken default-profile smoke: isolation claim withdrawn; user-
  authorized one-instance force-exit and reviewed guarded recovery completed.
- Revision3 corrected F-profile About/own-feed/single-instance/Shell right-click/
  normal Exit and known-default-profile preservation: PASS.
- Controller fresh management108/108, current EXE/installer hashes and product
  tree equality: PASS; no product code changed after the full published build.
- Actual scheduled checks: two successful scheduled events observed.
- Fresh final independent review: PASS0Critical/0Important/0remainingMinor.
  The local/cloud architecture wording Minor was corrected and re-reviewed.
  Reviewer independently checked1697 replay entries, raw local/CI TRX, native
  cloud logs,9 public asset hashes,6 archive copies/7 live original hashes and
  actual GUI/Exit evidence. Earlier tray symptom remains a recorded unresolved
  root-cause limit, not an asserted fix. Private final-review receipt:
  `.artifacts/runtime-v3-isolated/final-independent-review.json`.
- User visual/platform acceptance and manual boundaries above: not performed.
