# DeskCue migration handoff

Status: product/local-build code verified and reviewed; actual retail/cloud
execution, runtime acceptance and workspace cutover remain in progress.

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
- Fresh checked patch replay reproduces all1697 product index entries across
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
 repaired; the watcher timing failure was not root-caused or code-fixed, and
 later green runs do not erase that historical risk.

## Final acceptance sign-off

- Product/identity migration: scoped code/fixture reviewPASS0C/0I/0M.
- Fork-owned update/service boundaries and replayable patch: scopedPASS0C/0I/0M.
- Shared local retail build and safe publishing: scopedPASS0C/0I/0M; actual retail
 packaging is still pending.
- Actual cloud source/package/release cycle: pending.
- Fresh Controller verification and fresh final review: pending.
- User visual/physical Windows platform acceptance: not performed.
