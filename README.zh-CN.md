# DeskCue

DeskCue 是基于 [DeskBox](https://github.com/Tianyu199509/DeskBox) 的 Windows 桌面组件与文件整理工具，由 [CyberShadowX](https://github.com/CyberShadowX/DeskCue) 维护。

版本与上游来源以本仓库 Releases、`deskcue/config.json` 为准。采用 **GPL-3.0-only**，原作者版权和第三方许可保留，详见 [UPSTREAM.md](UPSTREAM.md) 与 [LICENSE](LICENSE)。

提供文件/文件夹格子、格子组、待办与提醒、随记、搜索、日期农历、天气、音乐、胶囊模式、多显示器布局以及备份等上游能力。文件搜索可对接单独安装的 Everything。

软件更新仅下载本仓库发布的 DeskCue 安装包。上游版本经过统一改名、测试、构建与校验后，才成为可安装更新。软件不需要 GitHub 凭据来下载公开更新。原作者的商店、付款及反馈服务器不作为 DeskCue 的服务。

本地零售构建的统一入口：

```powershell
.\tools\Publish-DeskCue.ps1 -Platform x64
```

需要 .NET SDK10.0.402、Rust1.96.0、对应 MSVC/Windows SDK 和 Inno Setup6。云端与本地使用同一套 `deskcue/` 脚本。Full Native AOT 安装包包含私有运行时；它是完整运行目录与安装器，不是旧 WPF 单文件程序。

上游源码来源、DeskCue 修订号和固定应用身份记录在 `deskcue/config.json`；生成来源收据位于 `deskcue/provenance.json`。日常操作见 [使用与更新](deskcue/使用与更新.md)，实际验证状态见 [HANDOFF.md](docs/HANDOFF.md)。旧 DeskCue 数据未自动导入，个人数据不上传到源码仓库。
