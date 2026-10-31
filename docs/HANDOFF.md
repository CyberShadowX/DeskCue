# DeskCue migration handoff

## Current checkpoint (2026-10-31): startup elevation repair1.5.9.7

Approved with `方案确认，开始执行`. Product source
`0cdb78b959928aae51abe989ecf776987cc76193`, branding revision7, DeskBox v1.5.9/
`1fdf0bd9f84affe889318173a7f3141843c79604`; GPL and upstream attribution retained.

The actual boot started DeskCue about three seconds before Explorer. Its missing
token was collapsed to false and cached, causing a false AppAboveShell/Exit-only
notice. Current-session DeskCue, Explorer and MyDockFinder are all High. The fix
preserves Unknown, probes the real session shell, and performs bounded asynchronous
assessment before widget initialization plus fresh later decisions. Unknown cannot
trigger compatibility-flag removal/relaunch. A repairable relaunch checks the exact
opened shell parent token and preserves startup/wait arguments; no unverified
ShellExecute fallback. Isolated test profiles cannot perform automatic repair.

The explicit startup repair tool defaults to Preview. Apply accepts only the exact
owned enabled legacy task, backs up declaration-correct XML, creates and verifies
the supported task before deleting the old one, and journals rollback evidence.
Actual Apply returned Repaired; after launching from that canonical task, fresh
Preview returned AlreadyRepaired. The production backend recognized and reconciled
ScheduledTask and removed its owned legacy Run entry. No account/UAC changes.
The raw settings autoStart snapshot is not authoritative; settings UI reads the
startup service. This task did not drive that settings toggle.

### Fresh local verification and replacement

Controller shared Native x64 run `r-c08e97aa9fd74f79`: **5939 C# +162 management
=6101/6101**, zero failed/skipped. Full AOT/offline runtime394 files, smoke harness
disabled. Official publisher reused the exact verified build and revalidated its
complete payload. All394 installed runtime files were independently rehashed.
Local EXE SHA256 `12d1b1ff8e2e0c469fb840f88013e74bda749ec85d80b23b17f08f22f111a089`.
Local Inno6.7.3 installer33714817 bytes, SHA256
`7d218f07590bacd31020a4f42ce45d3415dc8bac7872497b555510b7d15dd059`.

Exact Native synthetic admin/startup fixture: High/High, mismatch=None, startup
0degraded/0failed. Physical input verified add/save, single-click note editor focus,
Chinese note persistence, deletion and height437→491→437, and a modern picker
importing a generic attachment. Deletion persisted as isDeleted:true; post-relaunch
visibility was not exercised. Fixture exited normally through its attested Finder
menu. No production business content was used as test input.

Production replacement used a different exit path: ordinary Windows Restart Manager
shutdown(flags0) requested the app's query/end-session settings flush but returned351
with the old process alive. The user then separately authorized force-closing only
that precisely identified old DeskCue process. Three profile files were privately
backed up inside the project; only that process was ended, without its children.
Do not describe production teardown as a normal exit. Todo hashes matched before
and after replacement and after starting installed7 from the repaired task.
Production7 startup logged High/High, mismatch=None,42steps/0degraded/0failed.

### Cloud delivery and review

[Source CI](https://github.com/CyberShadowX/DeskCue/actions/runs/41190238550) passed.
[Native x64/ARM64 delivery](https://github.com/CyberShadowX/DeskCue/actions/runs/41190303508)
passed all four jobs with6101 tests per architecture. Public
[v1.5.9.7](https://github.com/CyberShadowX/DeskCue/releases/tag/v1.5.9.7),
release429862962, published2026-10-31T10:20:58Z.
All9 public assets, frozen ZIP entries, exact source-bundle head, both Native
receipts, installer sidecars, checksum inventory and stable/latest feed were freshly
verified against downloaded bytes. Cloud uses pinned Inno6.7.1; hashes differ from
the local6.7.3 package and are recorded separately.

- Cloud x64: 33702587 bytes, SHA256 `d7b72cb008438830d8a38d35f1feb1ece4547f5710440b98a24bc108c4866664`.
- Cloud arm64: 33152488 bytes, SHA256 `2c8f4ff885489ff24de7c667e8c9ab7ddbd05b6b27098b345aa9e8bf0aa78161`.

Complete75-path fork patch343190 bytes, SHA256
`312bb9f7c59d016d82019eda19818b92567c5415c9c80b0569c80fbd0eb83e17`.
Mechanical7 replay matches all five product trees; future8 changes only seven
version anchors. History7/6/5/4/3 retained, upstream/recipe/inventory/identity pins
unchanged. Final whole-delivery review PASS0Critical/0Important/0Minor.

Limits: **physical reboot/logon acceptance remains pending**. Starting the real
canonical task once does not prove the early-logon timing scenario. No live ARM64
GUI, elevated XAML StartDragAsync recovery, native drag-in, notification actions,
post-relaunch deletion visibility or installer execution was established. Existing
Todo editing/modern pickers/tray-balloon fallback are retained; platform-limited
drag and native notification actions are not advertised as universally repaired.
All13 notice locales accurately state these limits.

Private evidence stays under `.artifacts/elevation-controller/` and project-owned
`.archives`, including local/cloud acceptance, exact transaction XML/journal,
production-data hashes, authorized close trace, synthetic UIA/screenshots and shared
build receipts. Personal data, backup XML, logs and credentials were not uploaded.

## Historical Todo UX checkpoint (2026-10-29): published1.5.9.6

The user explicitly approved these Todo changes with `方案确认，开始执行`.
Reviewed product source is `3d6705d9091c3b26d684c6eb7c53e2b8539029df`, branding revision6, based on
DeskBox v1.5.9/`1fdf0bd9f84affe889318173a7f3141843c79604`.
GPL-3.0-only, original copyright and upstream attribution are retained.

- The Todo host preserves width and adjusts height to rendered content, including
  wrapped titles/notes. It caps to the current display work area and then scrolls;
  active-content, size-lock, capsule and transition guards remain. A reused hidden
  row uses the real ItemTemplate; live rows stay virtualized. Work-area changes
  and delayed filter-header reveal invalidate the cached measurement.
- Each task shows a smaller secondary note preview, at most two lines with
  ellipsis; empty notes collapse. Plain-body/blank single-click enters the existing
  focused editor. Raw Markdown and the save pipeline remain. Per-reader gesture
  state preserves hyperlink/attachment activation, checkbox and drag handling.
- Revision6 places the empty state in the ListView Footer, below the Add card,
  fixing an overlap found by actual Native AOT zero-item testing after revision5.
  Release history retains6/5/4/3, with future-version sorting/deduplication tests.
- Release test processes now inject a unique project-owned data root before
  static service initialization; concurrent log verification uses shared reads.
  All project tools, worktrees, fixtures and evidence remain inside this project.

### Local build and acceptance

Controller shared build `r-227e1afca15943e5` froze the exact clean source and
passed **5912 C# +132 management =6044/6044 tests**, zero failed/skipped.
Full Native AOT x64/offline runtime has394 files; smoke harness is disabled.
Local EXE SHA256 `1d9794fafcbbf3ef1dd629c60255c3b0a637f41bebdef5dd4fac1d12dfe4bd1b`.
Local Inno6.7.3 installer 33702096 bytes, SHA256
`c34c2208f37b62f269eae9e2c4af802cb892e4811f4e60f982cbf1415351d2d8`. Cloud uses its pinned Inno6.7.1 and therefore
has separately verified installer hashes below.

Native6 synthetic zero-item fixture: Add card center physically clicked and
DetailTitleTextBox focused; empty title y371/description y394 are below the card.
Saving a generic first task changed340x268 to340x255 because the empty panel
collapsed. Four-task fixture remains340x437, note rows render14/28px previews,
and the empty Footer is collapsed. The unchanged revision5 interaction paths
were physically checked at source3f94e52e: add/delete437→491→437, wrapping447,
body/blank editor focus, raw Chinese Markdown save, real link activation without
editing, checkbox persistence, drag without editing, and70-task cap1416px/y24
with item70 reachable by scrolling. These are explicitly historical5 input
checks, supplemented by fresh6 checks for the changed Footer and full runtime.

`tools/Publish-DeskCue.ps1` reused the exact verified build through BuildOperation
and performed normal staging/hash/move validation. All394 published payload
files and the installer were independently rehashed. Old production and test
processes exited normally through real Finder menu Exit after PID/row ownership
checks. Production1.5.9.6 launched from the published directory; existing Todo
JSON hashes stayed unchanged. MyDockFinder was left running. No force-kill,
personal-data fixture, installer execution, startup change or auto-organization
was used. Previous runtime remains in the contained release run.

Task reviews fixed link activation, work-area invalidation, header reveal,
empty layout and release-history findings. Fresh final whole-source/local x64
review: **PASS,0Critical/0Important/0Minor**. Reviewer independently checked
runtime hashes, source/patch, receipts, geometry and live process identities.
Fresh final integrated delivery/document review also passed0Critical/0Important/
0remainingMinor. Two documentation findings (stale guide version and ambiguous
CI test counts) were corrected and re-reviewed. The follow-up changes are
documentation only; product source and published binaries remain unchanged.

### Cloud delivery and source replay

Own source CI [40865623447](https://github.com/CyberShadowX/DeskCue/actions/runs/40865623447)
and delivery [40865627627](https://github.com/CyberShadowX/DeskCue/actions/runs/40865627627)
passed. Both native architectures passed6044/6044 tests. Public
[v1.5.9.6](https://github.com/CyberShadowX/DeskCue/releases/tag/v1.5.9.6), release
427805859, published `2026-10-29T11:56:16Z`. Controller downloaded and
rehashed all9 public assets against GitHub digests; stable.json, checksums,
source bundle head, frozen delivery and both architecture receipts agree.

- Cloud x64 installer: 33709967 bytes, SHA256 `e963ebb1dbe5847cb48ce7695e6ee1560f174f86e7897d9f9c8e4bca2499a2dd`.
- Cloud ARM64 installer: 33145243 bytes, SHA256 `54581667e19ab78e58aa3997296c80017006ec2c831dd4fe5e000b4101e7f844`.
- Complete fork patch:230356 bytes, SHA256
  `f50396319f94dbac75c0ac69dbb59bbec7309413b72c58df7a95498fca78977a`.
  Independently replayed all65 paths against mechanical6 and synthetic7;
  all five6 product trees match, and7 differs only at seven version anchors.
- Config SHA256 `6d19f17b3d6e0df5e3079f4d1c08a0bf69224c083d383ccdb3dc58001531f56b`.
  Recipe, original1930-file inventory, application identities and upstream pins
  remain unchanged. Only CyberShadowX/DeskCue receives source/releases; upstream
  push remains disabled. Private logs, backups and personal data are not uploaded.

Limits: no live ARM64 GUI or mixed-DPI transition test. Valid attachment shell
launch, keyboard link activation, selected-text highlight and independently
observed600ms autosave timing were not established. Saved raw Markdown and the
unchanged shared paths have source/unit evidence; these are not GUI proof.
Installer installation and system integration were not executed for smoke.
Private evidence is under `.artifacts/todo-ux-controller/`, including
`final-product-acceptance-v6.json`, `final-review-v6.json`,
`shared-build-result-v6.json`, `local-publish-result-v6.json`,
`production-launch-v6.json`, `revision6-final-replay.json`,
`cloud-acceptance-v6.json` and isolated fixture UIA records. The shared run contains
TRX, management results, retail inventory, receipt and command logs.

### Superseded revision5

Revision5/source3f94e52e9b2423c4754053eb47b41c3f6cbe9550 remains immutable.
CI40854152837 and delivery40854299433 passed; public release427723591 was
published2026-10-29T10:28:49Z. Local6042/6042 and positive GUI cases passed,
but subsequent zero-list acceptance found the overlap fixed above. Revision6
supersedes5; the earlier whole-task review did not cover that empty case.

## Historical project-local environment checkpoint (2026-10-29)

The user manually deleted the old sibling `.archives` and `.deskcue-tools`,
then explicitly required all project-owned development files to stay inside
`F:/AI/AIProjects/DeskCue` and authorized rebuilding the compiler environment.
The Controller verified both sibling directories absent before and after setup.
Old recovery archives were not recreated. That tooling-only task left published1.5.9.4 unchanged.

- Reviewed local commits `02dce4e5` and `a28c1d56` add canonical-root resolution,
  process-scoped environment management and repeatable verified initialization.
  Main checkout and nested worktrees share ONE
  `F:/AI/AIProjects/DeskCue/.deskcue-tools`; no duplicate worktree tool folders
  exist. Toolchain, downloads, tool homes, NuGet/Cargo caches and temporary paths
  are contained in the project. Existing shared OS/VS/Windows SDK/Git/Python/
  PowerShell prerequisites and application user data are not relocated.
- Actual initializer passed, then `-ValidateOnly`, ordinary reuse and a
  post-compilation `-ValidateOnly` invoked from the nested implementation
  worktree all passed. Exact tools: .NET SDK10.0.402, Rust1.96.0,
  Rustup1.29.2, Inno6.7.3. Rust x64 and ARM64 standard-library targets are present.
  Official pinned download hashes, Inno vendor signature and installed immutable
  file manifests are checked before acceptance; no machine-wide installer
  registration or project tool PATH addition is used.
- One obsolete User PATH segment pointing to the deleted parent tool directory
  was removed with a private recovery snapshot and compare-before-write guard.
  Other raw entries, percent-variable expressions and ExpandString kind were
  preserved. The first read-only-handle write failed without changing the value;
  the corrected writable-handle operation was independently reviewed and verified.
  Bootstrap blocks .NET first-use PATH addition. Subsequent actual setup/reuse/
  compilation left all12 recorded persisted environment values unchanged;
  before/after checks also verified restoration of16 process variables.
- Controller freshly ran132 Python/PowerShell environment and delivery tests:
  all passed in152.859s,0fail/skip. Task reviews closed two Important findings
  (containment before any write; Rust directory/executable-link validation) and
  one Minor (restrict file-link exception to Rust shims). Scoped verdicts0C/0I/0M.
- Real compile used the short contained checkout `.artifacts/e/compile` at
  `a28c1d565b012ab4c9ce2afa8c64e9647924d89d`. Restore exited0; actual x64
  Release application/native Rust build exited0,20 existing warnings/0errors.
  NuGet's actual `project.assets.json` package folder is exclusively
  `F:/AI/AIProjects/DeskCue/.deskcue-tools/nuget/packages`.
- All394 published runtime files still match the original accepted retail
  manifest. Five product trees (`src/tests/native/scripts/installer`) are
  unchanged from79f960e; no product/GUID/version/patch changes, installer execution,
  application replacement, force-kill, release or remote push occurred.

Evidence is private under `.artifacts/local-environment-controller/`:
`initialize.log`, `validate-only.log`, `initialize-reuse.log`,
`validate-after-compile.log`, `main-helper-tests.log`, `compile-run/{result.json,
restore.log,build.log}`, `commissioning-verification.json`,
`initialization-process-environment.json`, `persistent-environment-verification.json`.
PATH snapshots contain private environment data and must never be printed or
uploaded. Task RED/GREEN/review evidence remains inside the implementation
worktree's ignored `.artifacts`. Fresh final whole-task review passed
0Critical/0Important/0remainingMinor after correcting the stale archive wording.
The reviewer independently checked394 runtime hashes, all3 cached distribution
digests, persisted/raw environment values, current process identities and final
documentation. Private verdict: `final-review.json` in the Controller evidence.

Not re-executed for this tooling task: full C# runtime test suite, NativeAOT retail
publication, installer installation/update, GUI acceptance or ARM64 compilation.
Ordinary Release C# tests have an existing App.Log path into the real app profile;
this task deliberately verified tools and real compilation without invoking that
unrelated runtime behavior or expanding the product patch. ARM64 compilation
still requires the corresponding installed VS C++ components. No warning cleanup
or shared system prerequisite relocation is claimed.

## Historical checkpoint (2026-10-28): revision4

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
