# Contributing to DeskCue

## English

DeskCue is a fork of [DeskBox](https://github.com/Tianyu199509/DeskBox) maintained in [CyberShadowX/DeskCue](https://github.com/CyberShadowX/DeskCue). Preserve the original copyright, GPL-3.0-only license, third-party notices, and [upstream attribution](UPSTREAM.md).

Report bugs and discuss proposals through this fork's [Issues](https://github.com/CyberShadowX/DeskCue/issues). Pull requests to this fork are reviewed and merged at the maintainer's discretion; discuss substantial changes first. This does not promise review capacity, acceptance, or a future upstream roadmap. Do not send changes to the upstream repository as part of DeskCue's delivery process.

Use your own configured Git author identity (a GitHub noreply address is an option). Never impersonate the upstream author or copy their Git identity. Keep commits focused, describe the resulting behavior, and include relevant test evidence. Build and test through the fork's documented [entry points](deskcue/使用与更新.md); do not bypass release checks.

The files under `deskcue/` and the fork policy files are replayed during stable upstream adoption. Application changes outside that overlay must have a reviewed replay patch declared in `deskcue/config.json`, so the next adoption retains them. Follow [AGENTS.md](AGENTS.md) for repository development rules.

Security reports follow [SECURITY.md](SECURITY.md); keep vulnerability details and private data out of public Issues and pull requests.

---

## 中文

DeskCue 是 [DeskBox](https://github.com/Tianyu199509/DeskBox) 的派生分支，由 [CyberShadowX/DeskCue](https://github.com/CyberShadowX/DeskCue) 维护。请保留原作者版权、GPL-3.0-only 许可证、第三方声明和[上游归属](UPSTREAM.md)。

请通过本分支的 [Issues](https://github.com/CyberShadowX/DeskCue/issues) 反馈问题和讨论方案。发往本分支的 Pull Request 由维护者自行评估是否审查、合并；较大变更请先讨论。本文不承诺审查能力、接受结果或上游未来路线图。DeskCue 的交付流程不向上游仓库提交变更。

请使用自己配置的 Git 作者身份，也可选择 GitHub noreply 地址。不要冒用上游作者或复制其 Git 身份。提交应聚焦单个目标，说明实际行为及相关测试证据。构建和测试使用本分支的[文档入口](deskcue/使用与更新.md)，不绕过发布检查。

稳定上游同步会重放 `deskcue/` 下的文件及本分支政策文件。该覆盖范围之外的应用修改，必须通过 `deskcue/config.json` 声明的已审查补丁保留，防止下次同步丢失。仓库开发规则见 [AGENTS.md](AGENTS.md)。

安全问题遵循 [SECURITY.md](SECURITY.md)，不要在公开 Issue 或 Pull Request 中发布漏洞细节或私人数据。
