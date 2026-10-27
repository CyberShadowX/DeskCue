# DeskCue adoption progress

Plan: docs/superpowers/plans/2026-10-27-deskcue-upstream-adoption.md

## Current authoritative checkpoint (2026-10-28): candidate1.5.9.3

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

## Current checkpoint

- Legacy archive: F:/AI/AIProjects/.archives/DeskCue/2026-10-27-before-deskbox;
  verified bundle1B9B9050..., old EXE D6AFB867..., SQLite backup quick_check ok.
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
