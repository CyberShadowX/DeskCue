# DeskCue adoption progress

Plan: docs/superpowers/plans/2026-10-27-deskcue-upstream-adoption.md
Todo plan: docs/superpowers/plans/2026-10-29-todo-ux.md

## Current checkpoint (2026-10-31): startup elevation1.5.9.7

- Plan: docs/superpowers/plans/2026-10-31-startup-elevation.md.
- Product source0cdb78b959928aae51abe989ecf776987cc76193; unknown-shell startup
  misclassification fixed with bounded/current-session assessment. Administrator
  account and UAC preserved. Explicit owned startup normalization applied and
  independently validated; actual canonical-task invocation succeeded.
- Fresh main shared6101/6101 tests;394-file Native x64 payload and real synthetic
  admin/startup GUI passed. Notes, add/delete/height and modern attachment import
  checked. Installed7 matches exact accepted build; userTodo hashes unchanged.
- Production ordinary shutdown returned351; only after separate user permission
  was the precisely identified old process force-closed. Fixture teardown normal.
- Source CI41190238550 and four-job delivery41190303508 passed. Native x64/ARM64
  each6101/6101. Release429862962/v1.5.9.7: all9 public assets, frozen
  source/receipts/installers and stable/latest feed verified. See HANDOFF hashes.
- Exact7/future8 patch replay passed;75paths/343190B/SHA312bb9f7c59d016d82019eda19818b92567c5415c9c80b0569c80fbd0eb83e17.
  Final whole-delivery review PASS0Critical/0Important/0Minor.
- Real reboot/logon, settings toggle GUI, liveARM64 GUI, elevated XAML drag/native
  notification actions and installer execution remain unverified. No universal
  administrator compatibility claim; private evidence stays inside this project.

## Historical Todo UX checkpoint (2026-10-29):1.5.9.6

- Approved Todo natural height, max-two-line note previews and single-click note
  editing are implemented. Empty-list Footer avoids Add overlap; retained
  history6/5/4/3 survives regeneration and future version sorting.
- Product source `3d6705d9091c3b26d684c6eb7c53e2b8539029df`, complete patch230356 bytes,
  SHA256 f50396319f94dbac75c0ac69dbb59bbec7309413b72c58df7a95498fca78977a.
  Mechanical6 replay equals all five product trees; synthetic7 replay differs
  only at seven version anchors. Upstream/recipe/inventory/identity pins unchanged.
- Main shared Native x64 build r-227e1afca15943e5:5912C#+132helpers=6044PASS,
  zero fail/skip,394-file FullAOT/offline payload/harnessfalse. Official publisher
  reused exact verified binaries; production6 runs and userTodo hashes unchanged.
  Old/test processes normally exited, Finder unaffected, no force-kill.
- Fresh6 real Add-center/editor-focus/first-save and empty-footer separation;
  four rows340x437/two-line previews/collapsed empty state. Historical unchanged5
  paths additionally cover grow/shrink/wrapping/body+blank clicks/links/checks/
  drag/cap+scroll. See HANDOFF for exact evidence and GUI limits.
- Independent final source/local reviewPASS0C/0I/0M. Source CI40865623447 passed
  5912 C# tests; native x64+ARM64 delivery40865627627 passed6044 tests per
  architecture. Publicv1.5.9.6/release
  427805859; all9 public assets, feed, source bundle and both receipts
  freshly rehashed/verified. Exact cloud/local installer hashes in HANDOFF.
- Revision5 immutable, superseded after late zero-list overlap finding. No live
  ARM64 GUI/mixedDPI, valid attachment launch, keyboard link, selection-highlight,
  independent autosave timing or installer installation proof. Private evidence
  stays inside project; no personal data or logs uploaded.

## Historical project-local compiler environment (2026-10-29)

- Parent `.archives` and `.deskcue-tools` were manually deleted and verified
  absent. Old legacy recovery archives are no longer available.
- Tools now live ONLY in `F:/AI/AIProjects/DeskCue/.deskcue-tools`, shared by
  main/nested worktrees through the canonical common Git root. Scoped caches,
  downloads and temporary files remain inside the project; new ignore rules
  cover local tools and future explicitly requested private archives.
- Local reviewed commits02dce4e5/a28c1d56 add initializer/shared environment/build
  resolution. Actual initialization, validation, idempotent reuse and nested
  worktree validation passed: SDK10.0.402/Rust1.96.0/Rustup1.29.2/Inno6.7.3.
- Main fresh132 environment/helper tests PASS0fail/skip; actual x64Release
  app/nativeRust compilation0errors/20existingwarnings. ActualNuGetcache inside
  project. All394 formal runtime hashes and five product trees unchanged.
- Only one obsolete rawUserPATH entry removed; rawpercent expressions/kind and
  every other segment preserved. No newPATH entry; subsequent12persisted values
  unchanged and16process variables restored. Source tooling changes remain local;
  published1.5.9.4/tag847 and remote repository were not changed.
- Scopedreview0C/0I/0M after twoImportant/oneMinor fixes. Fresh finalwhole-task
  reviewPASS0C/0I/0remainingMinor. FullC#runtime tests/AOTpublication/installer/GUI/ARM64compile notrun;
  existing shared system prerequisites and appuserdata were not relocated.

## Historical checkpoint (2026-10-28): published1.5.9.4

- Product/tag8472699a23166a179ae36bbab08b26eb288bc417, revision4; actual top-Finder
  failure reproduced on1593(cloaked2/offscreen), repaired through click-origin
  validation and bounded positive-DWM recovery to nativePopupMenu. Shutdown
  race review Important fixed/re-reviewed0C/0I/0M. No third-party process change.
- Version-independent release-history patch/test review Important fixed;
  complete164663-byte patch e701d684...65cf215 exactly replays1700 product
  entries over BASE4eec0a5e8. SAME patch applies over private futureBASE5;
  future5 neverpublished. Identities/upstream/toolpins unchanged.
- Controller actualsharedPublishr-797b5b2816d04aef PASS5885C#+108=5993/0/0,
  FullNativeAOT394/offlineinstaller/harnessfalse. Fresh actualTRX5885records
  allPassed;394current+394previous/frozenhashes andbothinstallers verified.
- CI40682608024 SUCCESS5885/0/0. Delivery40682612368 all4jobsSUCCESS; each
  native5993/0/0,394x64/390ARM64. Publiclatest/tagv1.5.9.4/release426624916,
  published12:13:11Z. All9publicbytes/API/delivery/frozen/source/receipts/
  checksums/feed verified; Controller independently fetchedlatest/tag/stable
  andrehashcheckedall9. NativeTRX/payload inventory limits remain explicit.
- Retail43992/Froot: actualOSFinder rightclick→native12rows/8commandsDWM0,
  fullworkarea/allrowhitproof; physicalSettings→ownedvisibleSettings;
  About1594/secondary21844exit0; physicalFinderExit→exit0/absence, noforcekill.
  Known8Cprofilefiles/Run andDeskBox45252/Dock4816identities preserved forGUI.
- ExistingRelease tests appended/rotated defaultCApp.Log beforefixedGUI.
  Original5227490logbytes preservedasprefix in.log.1, hashd0e8ead6...9c1b3f;
  allnonloghashes unchanged. No whole-test-period C-untouched claim. Logsprivate.
- Extra1608/Froot: Shellrightclickworked/full12/8DWM0, but3commands physically
  coveredbyrunningDock; nativeWindowsPARTIAL, nofullclickPASSclaim. Public
  JumpList--open-settings secondary3312exit0 openedSettings; actualupdatebutton
  disabledwhilechecking thenenabled/latest1594. Afteruserpausedmouse, fresh
  physicalFinderExit→exit0/noCue/clean-exitledger12:35:03Z. All8Cfiles/allRun/
  originalBoxandFinderidentitypreserved. Fresh final independentreviewPASS
  0C/0I/0M; Mainadditional108helpers/UTF8/docslinksPASS, product5treesunchanged.

## Historical revision3 checkpoint

- Product source b05395c1f8a433391dbf30df6e5af46de1ec1cbe is published asv1.5.9.3.
  Main actuallocalPublish runr-38a424ccb8544121 PASS5859C#+108helpers=5967/0/0,
  full394-fileAOT/offlineinstaller. ActualCI40553510130 PASS5859/0/0;
  actualdelivery40553514453 all4jobsSUCCESS, eachnative5967/0/0, payload394/390.
  All9publicassetbytes/digests/frozeninventory/source/packages verified.
- Controller GUI smoke launcher used Debug-only DEV_DATA_ROOT in retailAOT;
  effectiveprofile was defaultLocalAppData, so its isolation claim is withdrawn.
  Correct variable is DESKCUE_AOT_PREVIEW_DATA_ROOT. RealAbout/ownupdate/latest/
  secondlaunch0 observed, but unintendednewvalidRun/newdefaultprofile/recovery
  required guarded recovery. User later explicitly authorized force-exit of
  stucktest44068; Controller checked exactPID/path/start/hash and ended only it.
  DeskBox45252 untouched. Correctedrestore1F23E01F...EB1E4F70 passed9Fsynthetic
  cases and independentreview0C0I0M; main freshclearPlan and actualExecute
  archived/hash-verified6currentfiles before deleting6files/4emptydirs;1known
  leaf alreadyabsent separatelyrecorded. ExactincidentRun removed;7oldfiles,
  profileparents and unrelatedRun fingerprints preserved. RawpriorRun baseline
  unknown, no OSatomicity claim. Private restore receipt977B17A9...EF0FC0D.
- CorrectAOT_PREVIEW/Fmanaged-root run52264: effectiveFfiles/log/ledger proven;
  actualAbout1.5.9.3/ownfeedcurrent/updatebuttonstates/secondlaunch52924exit0
  passed. OS-injectedrightclick on actualShellDeskCueicon displayed menu;
  visibleExit Invoke completed normalshutdown and actualPIDabsence09:00:30Z.
  NormalExit code unavailable/null, not asserted0. Defaultprofile/allRunvalues/
  Box identity matched afterlaunch/exit. EarlierUIArootchild helper missed
  flyout, fixedtesthelper uses exactPID-ownedHWNDs; productunchanged. Earlier
  usertrayfailure rootcause unknown/notreproduced here; no productfix claim.
  Evidence runtime-v3-isolated/controller-verification-summary.json.
- Main freshmanagement108/108PASS0fail/skip; EXE/installer hashes unchanged,
  product5trees unchangedb053. Actualscheduled40593240955/40639466001 success;
  lattertestedhelpers/detectednopendingstable and skippedbuild/deliver asdesigned.
  Fresh final independent review PASS0Critical/0Important/0remainingMinor;
  architecturewording Minor corrected and re-reviewed. Manualplatform/installed
  upgrade limits remain. No privateprofiles/logs/archive uploaded.

## Historical revision3 preparation (superseded by checkpoint above)

- Rev2 source6b6195c2 passed local5935/0/0 (5827C#+108helpers), full394-file
  NativeAOT/offlineinstaller; actualCI40536288571 passed5827/0/0. Delivery40536288591
  x64passed5935/fullAOT/installer; ARM4315PASS then nativehang, no release/tag/feed.
  Previous1591/1592 bytes remain immutable.
- Real ARMminidump/SOS/run40546464968 identify SDK CleanUp->nextSDKcall hang.
  Minimal provider fix must retain original <=1s drain and avoid per-instance
  globalCleanUp/prematuregateDispose. Lostdrain Important is fixed; round2 scoped
  reviewPASS0C0I0M, controlledRED->focused26PASS/5hosts4PASS. OriginalSearchcase/
  timeout unchanged. Historicalnotes route Important fixed:21RED->116GREEN,
  strict knownhistory contentonly upstream, forkfeed/installertrust unchanged;
  finalreviewer scopedre-reviewPASS0C0I0M, no other durableblockingfinding.
- Rev3 metadata scopedreviewPASS0C0I0M; BASE3=32a8074efccc8da8d74ff91f693c80d3177f10bb,
  configSHA211c933ec8ebdda9cee721952ef98dbc5b1820c29c61015d2d665f88b860a2ae,
  recipe/GUIDs/14DLLinputs unchanged. Fresh main management108/108PASS0skip.
  Finalpatch137807bytes SHA c60e809e4b21a730d8a00cb513fbf14688bdba4c327b8acf63cec5a54437d5bf;
  freshLF mechanicalBASE3 and checkedreplay all1697productentries exact.
  Evidence .artifacts/v3-final-product-replay.json.
- User confirmed normalexit1592; read-onlyPID35212absent/noDeskCue, originalBox
  PID45252 unchanged. This is manualevidence, not automatedtrayexit coverage.
- Next: cleancommit, actualfullLocalPublish
  and native dualarchcloud; publicrelease/feed/downloadhashes, finalGUI/update,
  finalHANDOFF and fresh finalindependentreview. No completionclaim yet.

## Historical candidate1.5.9.2 preparation

- Rev2 candidate is frozen and whole CODE delta reviewPASS0C0I0M. All scoped
  reminder/fixture/ARM/diagnostics/version reviews alsoPASS0C0I0M. Main fresh
  management108/108PASS0skip(.artifacts/controller-v2-management.log).
- FinalBASE2 fc0c25bd2c02a761fb2a3fcd3a4c49dbe7d39ede,configSHA
  AEE8BBAE02FC6C2EAB1E3A49F42EADA154947719A5525AB2ACF36C4DEEB7F326;
  recipe unchangedBE428219...,GUIDsunchanged. FreshLFgeneration exactlyBASE2,
  patch121962bytes SHA E130AEB5882D53498367B12CD4820579822AFE025C5CC4F6B1D82E6AB7E68BC7,
  checkedapplication reproduces all1697indexed productentries across5subtrees.
  .artifacts/v2-final-product-replay.json. Brand21PASS/directversionconsistencyPASS.
- Commit this reviewed clean candidate, then run sharedfullPublish and actual
  clouddualarch again. Existing1591successfulinstaller/checksum/receipt/payload
  must remain immutable;1592 has a distinct installerfilename. No DeskCue
  process is running after normalGUIexit. ActualARMsearchhang stillunresolved;
  no release until bothfullbuilds pass, use newlyretaineddiagnostics if it repeats.

## Previous state after9b7b4d78 (evidence preserved)

- Workspace cutover COMPLETE: F:/AI/AIProjects/DeskCue, main tracking ownorigin;
  original20top-level entries preserved in DeskCue-legacy-20261027. Codex held
  the root directory open, so a rollback-capable child-entry rename preserved
  the directory itself;2old/10new owned linked worktrees repaired. Receipt:
  .artifacts/cutover-result.json. All unrelated data/history retained.
- Source9b local fullPublish COMPLETE:5820C#+107helpers=5927PASS0skip,
 394payloadfiles/131.3MiB,installer33702525bytes SHA
 b3ace83fb1d3e8bfea15811a4bf2ac8f42904413b9b7247725a95da4855b7c02.
  NativeGUI preflight rendered DeskCue1.5.9.1 Onboarding+Settings/About; second
  launch exited0 leaving originalPID40396; normal trayExit invoked by UIA,
  process exited without force. OriginalDeskBox45252 unchanged. Finalcandidate
  GUI/update acceptance stillpending. Evidence .artifacts/runtime-acceptance.
- The initial smoke fixture used PascalCase instead of camelCase JSON; defaults
  were used. IsDevelopmentRoot prevented startup registration. Its newly created
  empty C:/Users/Administrator/DeskCue directory was verified by exact creation
  time/emptiness and removed nonrecursively after normalexit. Finalsmoke must use
  camelCase and an explicitFmanagedroot. No OS security/input settings changed.
- Ownrepo Issues+Discussions enabled and independently read back true. Feedback
  routes nowwork; no issue/comment/discussion content was posted.
- LiveCI40526959569 source9bSUCCESS5820/0/0,20warnings0errors. Delivery40526968013
  failed: x645816PASS4FAIL(calendarNLS,TEMPdrive assumptions,real remindercache
  stale metadata); ARMpartial4332PASS6FAIL then5min inactivity abort. SixARM
  failures were x64-only update/DLL fixtures; lastactiveSearchEngineRecommendation
  test does not prove hangcause. No AOT/installer/release from that cloudrun.
- Calendar/cross-volume TESTONLY fixes controlledRED3→GREEN6/fullclasses83PASS,
  independent0C0I0M(.artifacts/cloud-fixture-debug). Reminder realmtime-only cache
  bug fixed by authoritative Load each30s:RED2→GREEN17/repeat170/related43PASS,
  independent0C0I0M(.artifacts/reminder-cache-debug). Duecase proves same mtime+
  same length; completioncase proves same mtime. No new transaction guarantee.
- ARMfixture TESTONLY fixes frozen:93PASS inclbotharchmetadataRED→GREEN;
  productionarch/hashguards unchanged. OriginalSearchcase unmodified, local
  isolated1PASS91ms; actualARMhang remainsunresolved. Evidence arm-fixture-debug.
- Rootadded failure-only one-daycloud logs/TRX/sequence/minidump artifacts and
  explicit mini dump type, preserving5minhangtimeout/fullsuccessgates. Reviewpending.
- Firstpublicdelivery revision is being raised to1.5.9.2/revision2, preserving
  existing1.5.9.1 installerbytes/receipts. Brandingworker owns versionmetadata+
  config/provenance/test_brand only; all identityGUIDs staystable. Root must use
  NEW reviewedmechanicalbase to regenerate completepatch and prove exactreplay.
- Next: version+ARM/diagnosticsreviews, rootnewpatchreplay/freshfulltests+publish,
  pushmain/runactualdualarchcloud and resolveARMhang from captured evidence if
  repeated, verifyrelease/feed/downloadhashes, freshGUI/updatecheck+normalexit,
  accurateHANDOFF and finalfreshindependentreviewer. Do not claimdeliverycomplete.

## Previous execution checkpoint (historical)

- Initial reviewed implementation committed as f0a028d. Task4 delivery round3
  PASS 0C/0I/0M; main focused 45 tests passed; worker full 96 tests passed.
- First actual retail attempt at that commit stopped in Rust link.exe LNK1104:
  frozen checkout made its output path 264 characters long. The same source
  compiled successfully with a short output path (rust-short-path-proof.log).
- Builder now freezes source in guarded `.artifacts/b/<run-id>` and retains
  canonical receipt/log paths. Controller fresh 34 focused tests passed;
  independent scoped re-review PASS 0C/0I/0M, followed by clean commit/full retry.
- Fresh whole-branch review found fork contact/signing policy leftovers, now
  corrected as preserved overlays; fresh policy re-review closed 2I/2M with
  no remaining C/I/M. The operator guide is now under the preserved deskcue
  prefix. No release/runtime/cutover is claimed yet.
- Reviewed03bb09b was pushed to own main. Actual cloud delivery run40521404850:
  candidate succeeded, helpers101/101; both native builders stopped because
  ISCC FileVersion=0.0.0.0, so no retail test/build or delivery occurred. The
  compiler-engine banner is being used for the exact version check instead.
- Inherited CI run40521375317 installed SDK10.0.403 via10.0.x, causing locked
  updater restore NU1004 (ILLink10.0.13 versus10.0.14). Pinning exact10.0.402
  and global.json rollForward=disable; preserving those owned overlays.
- Local retail retry r-f9142abdd24b48b2 passed Release build(20warnings/0errors)
  then stopped at5819/5820 with the same43200-second watcher-delay timeout.
  watcher_debug is investigating a controllable fixture/FSW fakeclock race;
  no blind retry or production watcher fix is claimed.
- The same frozen03bb source separately passed private FullNativeAOT retail
  compile, byte contracts and Inno installer compile. Payload394files/131.3MiB;
  installer33695699bytes. This is diagnostic evidence only, not a release:
  .artifacts/packaging-diagnostic-result.json. No app installed/launched yet.
- Fresh main management suite101/101PASS(.artifacts/controller-management-final.log).
  Actual local publication, cloud release, runtime and cutover remain pending.
- Watcher fixture root cause now confirmed by a real FSW latch RED. Only the
  long-preset initial notification pair is controlled; production unchanged.
  Focused4/4 and10repeat rounds40/40PASS, no skips; independentPASS0C/0I/0M.
  The rejected Start-baseline attempt remains recorded in private evidence.
- Regenerated patch101655bytes SHA4C688E1B7252E5F1F68BB58ED688F06B5868573086D917F8ED3B08026E63CBD6.
  Fresh LF mechanical generation+patch apply reproduces all1697 product entries
  exactly across five subtrees(.artifacts/final-product-replay.json).
- Inno/SDK fixes frozen; worker107/107helpersPASS; main new probe5PASS, actual
 6.7.3 probePASS and SDK/CI overlay candidate1PASS. Scopedreview then actual reruns.
- Actual720239d retry:5819/5820, solely the inherited AotPublishContractTests
  assertion still requiring latestPatch instead of the deliberately fixeddisable.
  Assertion corrected; fresh targeted test and scopedreview follow. New complete
  patch102536bytes SHA7D4321C47D4D80D1A55166EC12FDF06B958C18313B1E36CCB615D8069C576455,
  cached check/apply from77a0d4b reproduces all1697 five-subtree entries exactly
  (.artifacts/sdk-pin-product-replay.json). Watcher cases passed this full run.
- Main targetedSDKcontract1/1PASS, scopedre-review0C/0I/0M; both real cloud
  x64/ARM64 exactSDK+Innoengine gates passed on720239. Cancel old known-stale
  contract run and retry the new clean source, preserving its evidence.

## Earlier checkpoint (superseded by the execution checkpoint above)

- Actual product source remains in F:/AI/AIProjects/DeskCue-migration-20261027,
 branch codex/deskbox-adoption; original workspace not cut over yet. No push yet.
- Final mechanical base77a0d4be49283ec76505d4def6f7d2238ede7069 replaces all
 earlier mechanical trees below. Source/root junctions guarded, all14 tracked
 DLLs preserved (Everything x64/ARM64 included), Deskbox spelling fixed and
 publisher display metadata owned by CyberShadowX. RecipeBE428219...,config602C005C...
 and current rootprovenance match. Task1 round2PASS0C/0I/0M.
- Task2 final checked patch98075bytes SHA256
 8307279b6002b930b138be33f24a4354fd608a0e18f0cd91f628e0974ac632ef.
 Fresh replay from mechanicalbase matches all1697 indexed product entries;
 report .artifacts/task2-replay-verification.json. Original trust/defaultfeedback
 boundary RED exists; corruptdownload preservation and4partversion tests added.
 All13locales have translated credits/publicfeedback disclosure. Mainfull
 .artifacts/fork-r5-full:5820/5820PASS0fail0skip,build18warnings0errors.
 Task2round2PASS0C/0I/0M. Prior watcher timingfailure remains historicalunfixed.
- Task3round2PASS0C/0I/0M after31ownedtests, actualWindowsjunction guards and
 actualPublish-wrapper secondmovefailure/byte-identicalrollback. Mainrecorded
 .artifacts/local-build-review-r2-green.log31PASS. Realretailbuild notrunyet.
- Mainmanagementsuite .artifacts/controller-management-before-package.log
 92/92PASS before lastcloudstarterfix. Latestcloudfix mustgetfreshfocusedcheck.
- Task4round1 had3Important(draftURL,frozenbytereplay,requiredpatchinventory),
 resolvedinround2. Round2 foundordinaryinstaller/checksum zero-bytestarter/null
 digest crash. Cloudworkerfixedboundedcleanupwithverifiedarchive, allotherassets
 validatedbeforedeletion, originalbytesretained; filesfrozenforround3review.
 CurrentdeliverySHA314815E25A57FD9AD6624D11CC736DC61FBE244EACA52B7EA5205A6E1DE85740.
- OnceTask4reviewgreen+freshhelpertests: commitreviewedcleancheckpoint, run real
 tools/Publish-DeskCue.ps1 x64 (portabletoolsautodiscovery), inspectpackage/output,
 freshfinalreview/mainchecks, pushownmain and run actualGitHubActions, resolve
 actualenvironment failures with evidence, verifyrelease/download/updatefeed,
 archive/swapmainworkspace+repairONLYownedmovedworktrees, normalruntime smoke.
 No credential/browserintervention needed sofar: Git pushdryrun ownforkworks.

- Authorized scope includes local replacement, branding, own GitHub source/release
  delivery and both cloud/local routes; no second internal-plan approval.
- Legacy bundle/source/release and SQLite backup verified under the private local
  archive. Initial source SHA1fdf0bd9f84affe889318173a7f3141843c79604.
- Own fork readable/writable; Git push dry-run succeeded without remote changes.
- Ruling: use an independent full clone instead of another worktree; it isolates
  an unrelated-history product replacement and preserves the original workspace.
- Ruling: migrate AGENTS once under the explicitly approved replacement; retain
  user Controller/review rules and discard original author's machine-specific
  paths/identity. Never silently copy their services, Store IDs or payments.
- Tools: portable .NET10.0.402 verified against official SHA512; existing VS x64
  toolchain/SDK usable; portable Rust/Inno being verified independently.
- Network diagnosis: Git did not inherit Windows system proxy; a command/local
  repo-specific proxy fixed access. No global proxy configuration changed.

## Historical initial adoption checkpoint

- Legacy archive: F:/AI/AIProjects/.archives/DeskCue/2026-10-27-before-deskbox;
  verified bundle1B9B9050..., old EXE D6AFB867..., SQLite backup quick_check ok.
  Historical only: the user deleted this archive on2026-10-29 after accepting
  loss of these recovery copies. Current storage policy is project-local.
- Independent clone branch codex/deskbox-adoption, origin own fork, upstream
  push URL DISABLED. Fork source1fdf0bd; tagv1.5.9 commit4cae1d4....
- Portable tools ready; baseline .artifacts/baseline verification5804/5804PASS,
 20 warnings/0errors. Original installed DeskBox PID45252 preserved.
- Mechanical recipe initial applied; final LF replay tree
 34e1623a116b7b15eb72326f309094637924a93d is current Task2 patch base, recorded
 in .artifacts/mechanical-brand-base.tree. Initial pre-fix tree7c944e2... is old.
- Ruling: product rename and endpoint boundary changes are reviewed as a combined
 product migration unit because retained upstream URL fixtures need deliberate
 fork adaptation. Pure recipe/identity review remains a separate scoped check.
- Task2 boundary RED: .artifacts/branding-red compiled;12 tests5failed/7passed.
 Runtime fixes now pin our GitHub release path and product/arch filenames,
 disable default upstream feedback POST, route UI to own Issues, hide upstream
 payment/Store/contact surfaces, show fork maintainer + original author credits
 in13locales, include GPL/UPSTREAM in publish. Capture ALL source/test deltas as
 deskcue/patches/001-fork-boundaries.patch against final reviewed mechanical tree.
- Full fork run1:5816tests,14failed/5802passed, mostly positive fixtures still using
 original product URLs (plus WebDAV expected-name fixtures). Adapted fixtures.
- Full fork run2:5816tests,4failed/5812passed:3remaining old origin InlineData
 (now corrected), plus existing DesktopAutoOrganizationWatcherDelayTests
 LongerPresets...delaySeconds43200 timing failure. Preserve that evidence;
 subsequent green is not root-cause remediation. No watcher production change.
- Management code: brand.py/config/test_brand by branding_recipe; delivery.py,
 Sync-DeskCue.ps1,test_delivery,workflow by cloud_delivery; shared Build,validator,
 tests,tools/Publish by local_build. Last management run65/65PASS before review fixes.
- Task1 reviewer brand_review round1 BLOCK0C/2I/1M: source/root junction escape,
 14renamed trackedDLLs omitted by ignored *.dll (incl both productionEverything
 DLLs), and Deskbox case variant. branding_recipe is fixing with real fixtures
 and a NEW reviewed replay tree/delta/provenance. Do not release34e1623 tree.
- Task3 reviewer local_build_review round1 BLOCK0C/1I/0M: artifact/payload/installer/
 receipt/stable-backup ancestor junctions not rejected before writes/swaps;
 controlled actual Publish rollback test also absent. local_build is fixing.
- cloud_review reviewing frozen delivery/workflow. No remote commits/releases,
 actual cloud executions, retail AOT package, runtime smoke or workspace cutover yet.
- Must finalize recipes/provenance, force-preserve original tracked binaries,
 generate/check replayable Task2 patch, full tests and independent product review,
 commit clean candidate, actual shared local build, review fixes, fresh final
 reviewer/main verification, own-main push+real Actions+release checks, then cutover.
