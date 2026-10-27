# DeskCue adoption progress

Plan: docs/superpowers/plans/2026-10-27-deskcue-upstream-adoption.md

## Latest authoritative checkpoint

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
