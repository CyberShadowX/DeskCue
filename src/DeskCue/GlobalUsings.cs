// Global usings must not cover module-boundary namespaces (DeskCue.Platform,
// DeskCue.FileSafety, DeskCue.Features, DeskCue.Sync): a global import would
// let a file reach the domain without the namespace string appearing in its
// source, silently bypassing the ratchet's reference checks. Every Platform
// call site carries its own explicit `using DeskCue.Platform;` — that string
// in the file is exactly what the boundary tests enforce on.
