# Independent design check

Review was read-only; no implementation acceptance is claimed.

Initial verdict: 0 Critical / 3 Important / 0 Minor. All three are explicit
implementation obligations and remain open until tested/reviewed:

1. Manifest download compatibility must reject DeskBox/unknown filenames even
   when hosted under our own release path. Asset enumeration alone is insufficient.
2. Four-part DeskCue versions require complete project/Inno/history/release-gate
   adaptation. In particular, do not append .0 to an already four-part version.
3. Git source/tag promotion and GitHub publication are not atomic. Maintain a
   retryable pending delivery after partial failure; the published release is the
   installed-product authority, and different bytes under an existing version
   cannot overwrite matching historical assets.

Two clarified requirements are included in the design pending implementation:
all runtime/test customizations replay as checked patches, and both architectures
build from the same frozen candidate source commit/bundle.
