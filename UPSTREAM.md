# Upstream attribution and fork identity

DeskCue is a modified distribution of [DeskBox](https://github.com/Tianyu199509/DeskBox)
by Tianyu Zhu (朱天雨), maintained as a fork by
[CyberShadowX](https://github.com/CyberShadowX/DeskCue).

Original copyright notices and the GPL-3.0-only license remain in effect. See
[LICENSE](LICENSE) and the retained third-party notices packaged with the app.
The DeskCue name and delivery changes do not claim independent original authorship
of the upstream application's implementation, artwork, or features.

Initial source: `1fdf0bd9f84affe889318173a7f3141843c79604`, based on DeskBox1.5.9.
The stable tag `v1.5.9` resolves to `4cae1d4ebb0e416af7d66a764f52f6ccaafdda3a`;
the later initial source commit only corrects the release documentation test count.
Current machine-readable source/version/transformation pins are in
`deskcue/config.json` and `deskcue/provenance.json`.

Fork-specific changes include coordinated product/application/native names,
distinct installer/notification/package/data/IPC identities, fork-only update
downloads, user-directed GitHub feedback, and shared cloud/local build delivery.
Original author-controlled feedback, payment, Store listing and signing services
are not DeskCue services and are not reused as the fork's own identities.

The historical architecture, articles, release notes and screenshots inherited
from DeskBox document upstream work. Mechanical path/name changes do not turn
their historical test counts or platform evidence into DeskCue verification.
Current fork verification and limitations are recorded in `docs/HANDOFF.md`.

DeskCue binaries must be distributed with the applicable GPL and corresponding
source. Each DeskCue release records the exact source and provides its source
alongside the packages. The original upstream's signature is not transferred.
