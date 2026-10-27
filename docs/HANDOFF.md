# DeskCue migration handoff

Status: workspace cutover complete; source9b local retail and GUI preflight
verified; cross-environment fixes and first public1.5.9.2 delivery remain in progress.

Rev2 candidate is now frozen and independently CODE-reviewedPASS0C/0I/0M.
Fresh Controller management108/108 passed; version/fixture/reminder/architecture
scoped reviews passed. Fresh LF generation exactly reproduced mechanicalBASE2
fc0c25bd2c02a761fb2a3fcd3a4c49dbe7d39ede; complete patch121962bytes,
SHA256E130AEB5882D53498367B12CD4820579822AFE025C5CC4F6B1D82E6AB7E68BC7,
reproduces all1697 indexed productentries exactly after checkedapplication.
The next clean commit must pass full local and dualarchitecture cloud gates;
the earlier ARM search hang remains unproven until an actual diagnostic rerun.

Current workspace is F:/AI/AIProjects/DeskCue onmain, trackingCyberShadowX/DeskCue.
Legacy contents/history remain in F:/AI/AIProjects/DeskCue-legacy-20261027; the
earlier separate bundle/EXE/SQLite backup is also preserved. Source9b full local
publication passed5927/5927(5820C#+107helpers),0skips; actual WinUI settings
rendered DeskCue1.5.9.1, single-instance forwarding and normal UIA trayExit passed.
This is a preflight of9b, not acceptance of the later cache-fix candidate.

Latest actual cloudCI40526959569 passed5820/0/0; delivery40526968013 did not
publish. It revealed culture/drive fixture assumptions, x64-only ARMfixtures,
and an actual stale reminder snapshot bug. Scoped corrections are verified;
ARM's incomplete run also timed out with Search recommendation lastactive,
which does not identify its rootcause. Failure diagnostics are being retained
for the next actual run. Current authoritative task ledger:deskcue/progress.md.

First public revision is1.5.9.2; the earlier validated1.5.9.1 artifacts remain
immutable. Versionmetadata/replay/fullpublication/cloud/GUI must complete before
the final acceptance sign-off below can be advanced.

First real retail attempt at f0a028d stopped in the Rust linker before tests or
packaging: the frozen-source output path was 264 characters (LNK1104).
The same source compiled successfully with a shorter Cargo output path.
The builder now uses the guarded short checkout `.artifacts/b/<run-id>` while
keeping canonical logs and receipts unchanged. All 34 focused builder fixtures
passed in the Controller session; scoped independent re-review passed
0 Critical / 0 Important / 0 Minor. A new complete retail attempt follows.
No complete retail publication, stable EXE replacement or running-app
acceptance is claimed yet.

At reviewed03bb09b, the second full local attempt passed its Release build but
stopped on the historical 43200-second watcher-delay fixture (5819 passed,
1 failed,0 skipped). Its cause is under controlled investigation. A separate
private run passed FullNativeAOT publish, byte validation and Inno compilation
(394 payload files,131.3MiB); it is diagnostic-only until all release gates pass.
The own-main push succeeded. First actual cloud delivery run40521404850 passed
candidate/helpers101 but both builders rejected ISCC's0.0.0.0 FileVersion;
delivery was skipped. Inherited CI selected SDK10.0.403 and failed locked restore.
Compiler-engine version detection and exact SDK selection are being corrected.

Current retry source: the watcher timeout was reproduced with a real FSW
Created/Changed delivery latch. A late Changed after the fixture's multi-hour
clock jump correctly re-armed another full interval. The fix controls only the
long-preset fixture's initial event pair; production is unchanged and live FSW
tests remain. Focused4/4 and10repeat rounds40/40 passed, no skips; independent
reviewPASS0C/0I/0M. The rejected Start-baseline proposal and all earlier failures
remain in private evidence.

The complete checked patch now includes that fixture fix and the exact-SDK
contract expectation:102536bytes,
SHA2567D4321C47D4D80D1A55166EC12FDF06B958C18313B1E36CCB615D8069C576455.
Fresh LF-source generation and application reproduced all1697 indexed product
entries across src/tests/native/scripts/installer exactly. Cloud fixes preserve
the strict6.7.1 engine pin, SDK10.0.402/rollForwarddisable, locked restore and
owned CI/global.json overlays. Worker helper suite107/107 passed; Controller
new probe fixtures5/5, actual engine probe and SDK-overlay candidate test passed.
Full retail/cloud reruns follow the new reviewed commit.

The full local720239d retry passed5819/5820; the sole failure was the inherited
AotPublishContractTests expectation `latestPatch` after the intentional SDK
policy changed to `disable`. The expectation is now corrected and included in
the complete patch. A private-index checked application of the updated patch
to the final mechanical base reproduces all1697 entries exactly. No failure
was skipped or reclassified as a successful publication.
The corrected contract passed a fresh Controller targeted run1/1,0 skipped;
independent scoped re-reviewPASS0C/0I/0M. Both actual cloud native-builder/SDK/
Inno engine gates passed at720239d. That old run is being cancelled before
known stale contract work; a new clean source rerun will exercise all gates.

The final source review's two Important and two Minor policy findings are
resolved: fork-owned security/conduct/support/contribution/signing policies,
disabled legacy distribution jobs and the operator guide are now preserved
across upstream replay. The policy re-review found no remaining C/I/M; real
candidate replay and missing-policy rejection fixtures passed.

## Authorized scope

On2026-10-27 the user approved full replacement of former WPF DeskCue with the
DeskBox-based CyberShadowX/DeskCue fork, complete product renaming and both cloud
and explicit local build/update routes. No old WPF implementation is integrated
into this product. GPL/upstream/third-party attribution is preserved.

## Verified baseline

Unmodified upstream1fdf0bd: locked restore exit0; x64/win-x64 Release build exit0,
20 warnings/0 errors; complete test run5804 passed/5804 total,0 failed/0 skipped.
This is upstream baseline evidence, not acceptance of the rebranded application.
Portable .NET10.0.402/Rust1.96.0/Inno6.7.3 were verified and prepared under F.
Existing VS2022 x64 C++/Windows SDK prerequisites were used without global changes.

Legacy e98b255 history, stable EXE and consistent SQLite snapshot are preserved
in the private local archive and are not uploaded to this public fork. No legacy
task/settings import or desktop-file organization has been performed.

## Current product checks

- Mechanical generation fixture suite and real fresh-source replay passed.
- The first fork-boundary RED run compiled successfully;12 tests executed,
 5 failed/7 passed, demonstrating the original trust/feedback boundaries.
- Controller full fork validation:5820/5820passed,0failed,0skipped; Release build
 18warnings/0errors. Evidence retained locally under .artifacts/fork-r5-full.
- Earlier checked patch replay reproduced all1697 product index entries across
 src/tests/native/scripts/installer exactly. PatchSHA256:
 8307279b6002b930b138be33f24a4354fd608a0e18f0cd91f628e0974ac632ef.
- Task1 recipe/identity round2PASS0C/0I/0M, including true junction tests and
 clean export of all14 original DLL inputs. Task2 boundary round2PASS0C/0I/0M,
 including real corrupt-download cleanup/prior-installer preservation and13locale
 source/feedback disclosures. Task3 local-build round2PASS0C/0I/0M, including31
 fixtures and an actual wrapper second-move-failure/byte-identical rollback.
- Original baseline20warnings and current18warnings are retained; no zero-warning
 claim. Native-language human review and actual GUI/platform acceptance are not
 implied by JSON/schema/unit-test success.
- Failed full runs remain recorded: initial14migration fixture failures; later
 three stale update-origin fixtures plus one existing12h watcher-delay timeout;
 then the mechanical copy-test self-rejection. Those migration assertions were
  repaired. The watcher timing failure was initially unresolved; its later
 controlled reproduction and fixture-only correction are recorded above.

## Final acceptance sign-off

- Product/identity migration: scoped code/fixture reviewPASS0C/0I/0M.
- Fork-owned update/service boundaries and replayable patch: scopedPASS0C/0I/0M.
- Shared local retail build and safe publishing: scopedPASS0C/0I/0M; actual retail
 packaging is still pending.
- Actual cloud source/package/release cycle: pending.
- Fresh Controller verification and fresh final review: pending.
- User visual/physical Windows platform acceptance: not performed.
