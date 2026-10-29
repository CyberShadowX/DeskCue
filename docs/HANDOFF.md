# DeskCue migration handoff

## Current checkpoint (2026-10-28): revision4

The complete DeskBox-based fork remains at `F:/AI/AIProjects/DeskCue`, branch
`main`, own origin `CyberShadowX/DeskCue`. Version **1.5.9.4**, branding revision4,
is published locally and on GitHub for native x64/ARM64. Product source/tag is
`8472699a23166a179ae36bbab08b26eb288bc417`.

The actual MyDockFinder top-Finder failure was reproduced and repaired. Real OS
mouse input verified a visible usable menu, Settings and normal Exit. The
separately installed DeskBox and MyDockFinder were not closed or changed.
The update button was subsequently invoked in the actual retail app: checking
disabled the button, then own-feed1.5.9.4/latest re-enabled it.

Native Windows Shell entry was also checked under the running bottom Dock:
the callback and complete uncloaked menu worked, but Dock covered three command
centers. This is a PARTIAL check, not full physical Windows-tray acceptance.
The extra update-test instance also exited normally through the actual top
Finder menu. Post-teardown known profile/startup/process preservation checks
passed. Fresh final independent review passed0Critical/0Important/0Minor;
Controller's additional108 helper checks and docs checks also passed. Later
documentation commits do not change the frozen published product source847.

## Revision4 local build and source verification

The user clarified that the failing entry was MyDockFinder's top Finder tray,
then explicitly instructed the Controller to proceed. Revision3's earlier
Shell/UIA check did not measure compositor visibility or accept the Finder path.

Actual revision3 Finder input reached the callback, but the WinUI host was
DWM-cloaked2 and the popup extended above the monitor. Revision4 validates the
captured click against the Shell icon rectangle and originating monitor, then
checks the loaded host through public XamlRoot/AppWindow APIs. A positively
cloaked host switches to the existing native PopupMenu. Unknown evidence keeps
the existing mode; MyDockFinder's presence alone does not force a fallback.
Recovery is bounded, generation-scoped and suppressed during shutdown.

- Source review blocked a deferred-menu/shutdown race; the fix and re-review
  passed0Critical/0Important/0Minor. Metadata review blocked version-pinned
  patch/history tests; the final additive history merge is independent of the
  next mechanical version and also passed0C/0I/0M.
- Source tree `e27d0f37d8a27d3cef55e3b48387bf8930516b29`; upstream remains
  `1fdf0bd9f84affe889318173a7f3141843c79604`. Identities, toolchain pins,
  GPL/attribution and native third-party inputs are unchanged.
- Mechanical BASE4 `eec0a5e83017d6f3b5d4106ff4a6a08687144485`; complete patch
  164663bytes SHA256
  `e701d68457d6e72c11c815f224ccc532fcdb32a8082429cb6700f33d265cf215`.
  Actual replay matches all1700 indexed entries across five product trees. The
  SAME patch checked/applied over private mechanical revision5, which was never
  published. Arbitrary future upstream conflicts remain a delivery boundary.
- Controller ran the authoritative local publisher on the clean frozen source:
  `r-797b5b2816d04aef`,5885 C# plus108 helpers=5993passed,0fail/skip.
  FullNativeAOT/offline x64 payload394files, smoke harness false. Controller
  independently parsed5885 raw TRX records and checked394 current plus394
  preserved previous runtime files against their corresponding frozen payloads,
  and both installer hashes. No bare retail publish was used.
- Local EXE SHA256
  `248e95c3b0862f3aae8be89edfa53a8f0600e883c62ae360f09a6c712a1ef409`;
  local x64 installer33717764bytes SHA256
  `80a177b4a03a5340dd78467a44c1d91d9809f0a605de4754e632f2c90528223d`.

## Revision4 actual cloud publication

- CI40682608024 succeeded; the downloaded original TRX contains5885Passed,
  0fail/skip. Delivery40682612368 completed candidate122796861597,
  x64122798246548, ARM64122798246484 and deliver122807960501 successfully.
  Each native job passed5993/0/0, with394x64/390ARM64 payload files and smoke
  harness false. SDK10.0.402/Rust1.96.0/Inno6.7.1; ARM64 was built on ARM64.
- Public [v1.5.9.4](https://github.com/CyberShadowX/DeskCue/releases/tag/v1.5.9.4),
  release426624916, published2026-10-28T12:13:11Z, stable/latest and direct tag
  at847 above. All9 public asset bytes match GitHub API digests and delivery
  output. Source bundle, both installers/receipts/checksum sidecars, all7 checksum
  records and frozen archive restoration/inventory were verified.
- Public x64 installer33931089bytes SHA256
  `3d6028ac04a90cbe59a179d8ead55d6c45537c83a6335a353866d00574e56a29`;
  ARM64 installer33139481bytes SHA256
  `77774a4db9285945806bc9919054b4a2ca15baf5141f887c5a2da629493580e4`.
- Source bundle149800832bytes SHA256
  `542f7792d8108ab037a43924ca67763bdaaeeba6fbd29cce97b3ce1fadbb52d2`;
  frozen ZIP216877736bytes SHA256
  `adab20347b566f893a4fde61a1af25be260b8ac0929800d693099e5ed96522ed`.
  Controller separately fetched latest/tag and stable.json, checked the stable
  download against its API digest and rehashed all9 actual public files against
  that fresh API response. Local Inno6.7.3 and cloud6.7.1 hashes are distinct;
  there is no bit-for-bit local/cloud reproducibility claim.

Private evidence: `.artifacts/finder-tray-fix/controller-v4-local-final.json`,
`controller-public/verification.json`, `cloud-v4/verification-summary.json`,
`native-verification.json`, `ci-trx-verification.json` and original logs/assets.
Successful native jobs do not upload original native TRX, retail summaries or
full payload inventories: native counts/completion are evidenced by complete
raw logs, enforced contracts and downloaded receipts. CI and local original TRX
were directly parsed. No private profiles or diagnostic logs were uploaded.

## Revision4 actual GUI acceptance and limits

FullNativeAOT43992 used explicit F AOT-preview data and managed roots, with
startup, organization, backup, hooks and notifications disabled in the fixture.
Actual top-Finder right-click produced DWM0; all12 native entries including4
separators were read, all8 command centers hit43992 and the complete menu fit
the clicked monitor work area. Physical Settings opened a unique owned visible
uncloaked Settings window. About rendered1.5.9.4. Secondary21844 exited0 while
the primary remained. A fresh actual Finder right-click and physical Exit
normally ended43992 with exit0/no remaining DeskCue/forceKillfalse.

Evidence: `fixed-finder-settings-2-action.json`, `fixed-finder-exit-1-action.json`,
their input records and actual CopyFromScreen PNGs,
`fixed-evidence/single-instance.json`, `.artifacts/finder-tray-fix-settings/`.
Private helper pre-use review closed an incomplete-native-enumeration/UIA
fallback finding; final helper90088...773A passed0C/0I/0M. UIA visibility or
PrintWindow alone is not accepted as physical Finder accessibility.

The additional1608 process used a new `windows-data` F fixture. Actual generated
F settings/layout/log/startup-ledger and disabled action flags were checked;
the initial launch record's unverified flag is retained, with separate proof in
`windows-evidence/effective-root.json`. The native Windows Shell DeskCue button
was identified through unique Explorer UIA identity. An initial helper guard
correctly sent no input when FromPoint exposed only the containing Shell pane;
an exact host-HWND/runtime/class/DWM guard was reviewed before retry.

The retry delivered a real Shell-icon right-click: complete12/8 native menu,
DWM0 and full work-area bounds. Five command centers hit1608, but three bottom
commands hit MyDockFinder4816, so physical Settings/Exit clicks were blocked.
`windows-shell-settings-2-action.json` remains PARTIAL, not PASS. Subsequent
pointer/hover guards also stopped on changing or occluded targets. MyDockFinder
was not hidden/stopped to manufacture acceptance. A later stale-coordinate
screen crop is not owned-current-menu proof and is excluded from acceptance.

The existing public `--open-settings` JumpList activation then opened Settings
without global mouse input: secondary3312 exited0, primary1608 retained. UIA
selected About and invoked the actual OneClickUpdateButton. The captured state
was checking/button-disabled, followed by latest/button-enabled and1.5.9.4.
Evidence: `windows-evidence/open-settings-jumplist.json` and
`.artifacts/finder-tray-v4-update-{ready,invoked,completed}/windows.json`.
This accepts update-button behavior, not an installer execution or Windows
Shell physical click. After the user paused mouse activity, a freshly verified
DeskCue Finder tooltip and the reviewed fixture wrapper produced another fully
accessible8-command native menu. Physical Exit normally ended1608 with exit0,
no remaining DeskCue and a clean-exit ledger at2026-10-28T12:35:03Z. All8 known
default-C files/all Run fingerprints and original DeskBox45252/Dock4816 exact
path/start identities matched the pre-extra-GUI snapshot. Evidence:
`final-finder-exit-1608-action.json`, `known-default-state-after-windows.json`
and `controller-v4-final-runtime.json`. Fresh final independent review checked
the exact source, replay/future probe, raw tests, both payload versions, cloud
logs/public bytes, actual GUI and these documented limits: PASS0C/0I/0M.
Controller subsequently ran108 helper tests again (144.533s,0fail/skip), checked
UTF-8/local documentation links and confirmed the five product trees unchanged.
Private review receipt: `.artifacts/finder-tray-fix/final-review/verdict.json`.

### Default-profile logging boundary

The correctly isolated43992 GUI preserved the known eight default-C profile
file hashes and all Run-value fingerprints from immediately before launch
through normal Exit. Ordinary Release C# test hosts earlier used the existing
default App.Log path: they appended and rotated DeskCue.log at the existing5MiB
limit, creating DeskCue.log.1 BEFORE fixed-GUI launch. The original5227490 log
bytes remain in order as the exact prefix of DeskCue.log.1, SHA256
`d0e8ead69054234e118ec2c6e434354a2c90ad1cd514f9c1c068ece05d9c1b3f`.
All original nonlog database/JSON hashes remain unchanged. Neither log was
deleted/restored. Individual writer PIDs/each appended byte were not traced;
the whole implementation/test period is not claimed to leave C untouched.
For the existing default-C profile, only hashes/lengths were inspected and its
personal contents were not printed or uploaded. F diagnostic evidence remains
private and is excluded from source commits and public release assets.

## Historical revision3 release

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

The migration originally preserved the former WPF tree/history and an independent
EXE/SQLite/source-bundle archive. The user subsequently manually deleted the
legacy/migration working directories, then explicitly accepted deleting the old
archive and parent-level portable tools. On2026-10-29 the Controller verified
that both `F:/AI/AIProjects/.archives` and `F:/AI/AIProjects/.deskcue-tools` are
absent. Those old recovery copies must not be advertised as available. No old
data was automatically imported or uploaded. The historical cutover receipt is
`.artifacts/cutover-result.json`; historical preservation claims describe that
earlier checkpoint only.

`tools/Publish-DeskCue.ps1` builds the complete offline runtime and installer,
verifies source/tests/package bytes, preserves the previous release and blocks
replacement while its app is running. It never kills, installs or starts apps.
Project-owned portable tools now belong under
`F:/AI/AIProjects/DeskCue/.deskcue-tools`; the canonical common-Git project root
is shared by linked worktrees. Downloads, tool homes, dependency caches and
temporary build files stay under the project. New private backups, if explicitly
requested, belong under its ignored `.archives`; deleted old backups are not
recreated. Shared existing OS/VS/Windows SDK prerequisites and app user data are
not relocated. The former WPF single-file EXE contract no longer applies.

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
startup/relogin, toast delivery, ARM64 GUI, Windows10, physical DPI/multiple monitors,
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

## Historical revision3 acceptance sign-off

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
