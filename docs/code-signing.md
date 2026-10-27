# DeskCue code signing

DeskCue is a fork of [DeskBox](https://github.com/Tianyu199509/DeskBox), maintained in [CyberShadowX/DeskCue](https://github.com/CyberShadowX/DeskCue). Original authorship and GPL attribution remain in [UPSTREAM.md](../UPSTREAM.md).

## Current fork status

No DeskCue signing provider, certificate, or signing authorization is configured. DeskCue installers are unsigned unless a specific future release records independently verified signing evidence. A successful build, checksum, or upstream signature does not establish a DeskCue signature.

The authoritative delivery workflow is [deskcue-upstream.yml](../.github/workflows/deskcue-upstream.yml), with the shared local entry [Publish-DeskCue.ps1](../tools/Publish-DeskCue.ps1). It does not submit signing requests. The inherited [distribution-audit.yml](../.github/workflows/distribution-audit.yml) is retained as a disabled audit-contract reference; its jobs cannot run and its SignPath submission and verification jobs have been removed.

The original SignPath organization, API credentials, certificates, project identity, and Store identities are not owned or reused by this fork. Introducing signing later requires separate authorization and configuration owned by the fork maintainer.

## Historical upstream evidence

The upstream signing document reported a test-certificate verification dated **2026-10-08** and listed Tianyu Zhu (Simon) as its committer, reviewer, and approver. Those statements describe the upstream project only. They have not been reverified here and are not evidence of DeskCue signing, fork team roles, or service authorization. The upstream author's signature and signing-service sponsorship do not transfer to DeskCue.

## Checking a downloaded installer

```powershell
Get-AuthenticodeSignature .\DeskCue_Setup_x.y.z.r_x64.exe |
    Format-List Status, SignerCertificate, TimeStamperCertificate
Get-FileHash .\DeskCue_Setup_x.y.z.r_x64.exe -Algorithm SHA256
```

Compare the hash with the matching sidecar from this fork's [release](https://github.com/CyberShadowX/DeskCue/releases). A matching hash confirms equality to that published checksum; it is not a certificate or a signing-service claim. `NotSigned` is the expected signature status for an unsigned DeskCue installer.

## Feedback privacy

The fork's in-app feedback entry opens public GitHub Issues. It does not automatically upload diagnostics. Review attachments before posting; see [SUPPORT.md](../SUPPORT.md) and [SECURITY.md](../SECURITY.md).
