# MyDockFinder tray compatibility repair

Authorization: after clarifying the actual top Finder tray, the user explicitly
instructed the Controller to start fixing it on 2026-10-28. This proceeds within
that direct instruction without another internal-plan approval.

Baseline: main d05c31cf, published product b05395c1, DeskCue 1.5.9.3.
Implementation worktree: codex/finder-tray-compat. Source writes stay isolated.

1. Reproduce the old retail app using an explicit F AOT preview data root and F
   managed root. Disable startup, organization, backup, hooks and notifications
   in the fixture. Locate the real top Finder icon. Observe the target's callback,
   menu bounds, foreground owner, DWM cloaking and hit-test ownership. Do not
   close/restart MyDockFinder or the separate DeskBox. Preserve default data.
2. Write focused behavioral regressions for the actual failure. Relevant seam:
   src/DeskCue/App.Tray.cs placement/recovery, its platform window helpers, and
   tests/DeskCue.Tests/TrayContextMenuResilienceTests.cs. Extract a small pure
   policy only if needed to test coordinate/visibility decisions. Observe RED,
   implement the smallest correction, then focused GREEN plus relevant suite.
3. Independently review the exact source/test delta. Fix/re-review every Critical
   or Important finding before delivery work.
4. Persist the fix in the complete fork patch. Bump branding revision/product
   version to 4/1.5.9.4 with unchanged identities/upstream commit/tool pins.
   Generate a new mechanical base; verify clean patch replay over all product
   subtrees. Review this delivery delta before integration.
5. Integrate reviewed commits, run the shared local full publisher and actual
   native x64/ARM64 cloud workflow. Retain the previous package until verified.
6. Test the repaired retail app directly through the top Finder tray: visible
   usable menu, Settings and Exit. Also check native Windows tray, update state,
   single-instance and unchanged known default profile/startup. Record honest
   limits and a fresh independent final review in HANDOFF before completion.
