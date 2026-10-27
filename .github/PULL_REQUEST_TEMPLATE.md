## Note for external contributors / 外部贡献者请注意

This is the DeskBox-derived DeskCue fork. Please read [CONTRIBUTING.md](../CONTRIBUTING.md). The fork maintainer decides whether to review and merge a pull request. Submit only to CyberShadowX/DeskCue and preserve GPL, copyright, and upstream attribution.

这是派生自 DeskBox 的 DeskCue 分支。请阅读 [CONTRIBUTING.md](../CONTRIBUTING.md)，由本分支维护者评估是否审查、合并。仅向 CyberShadowX/DeskCue 提交，并保留 GPL、版权和上游归属。

---

## Maintainer checklist / 维护者自查

- [ ] `dotnet test .\tests\DeskCue.Tests\DeskCue.Tests.csproj --no-restore --verbosity:minimal -p:Platform=x64` all green
- [ ] Serialization/boundary changes → ratchet updated on both layers (baseline count + AotStage literals)
- [ ] `DESKCUE_NATIVE_AOT` files touched → AOT retail publish verified, `packages.lock.json` restored after
- [ ] Commits use each contributor's own configured Git author identity; no upstream-author impersonation
- [ ] Changes outside the tracked fork overlay have a reviewed replay patch declared in `deskcue/config.json`
- [ ] Docs/version numbers updated if user-visible (changelog, READMEs, freeze counts for UI contract tests)
