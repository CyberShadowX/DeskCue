#!/usr/bin/env python3
"""Deterministically brand a fresh, committed DeskBox checkout as DeskCue.

Only Git-tracked inputs participate. All validation and collision detection run
before writes; governance, build outputs, legal notices and binary bytes survive.
Service ownership policy is a separate overlay; unknown author URLs stay intact.
"""
from __future__ import annotations

import argparse
import codecs
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import uuid


IDENTITIES = (
    "5E052824-3456-427E-9759-3BCAE078A1D3",
    "3B75AA4A-2433-4F71-9CC1-B644B26F474A",
    "7bb59608-421d-4fd4-8f12-8929f87d086a",
    "4D54EEC6-13BE-4C8F-A8F7-81FE72F4B2C9",
)
EXCLUDED = {".git", "bin", "obj", "artifacts", "testresults", "target", ".vs", "__pycache__"}
TEXT_SUFFIXES = {
    ".cs", ".xaml", ".xml", ".json", ".resw", ".props", ".targets", ".csproj",
    ".sln", ".h", ".rs", ".toml", ".lock", ".ps1", ".md", ".txt", ".yml",
    ".yaml", ".iss", ".isl", ".islu", ".config", ".manifest", ".appxmanifest",
    ".csv", ".c", ".cpp", ".bat", ".cmd", ".pubxml", ".ruleset", ".svg",
}
NAMES = (("DeskBox", "DeskCue"), ("Deskbox", "DeskCue"), ("deskBox", "deskCue"), ("deskbox", "deskcue"), ("DESKBOX", "DESKCUE"))
CRITICAL = {
    "DeskBox.sln": "src\\DeskBox\\DeskBox.csproj",
    "src/DeskBox/DeskBox.csproj": "<Version>",
    "src/DeskBox/Package.appxmanifest": "D1FC332A.DeskBoxWidgets",
    "src/DeskBox/Services/DeskBoxDataPathService.cs": '"7F3A9B2E"',
    "src/DeskBox/Services/AppUpdateService.cs": "https://deskbox.fun/update/stable.json",
    "src/DeskBox/Services/ReleaseNotesService.cs": "KnownReleaseVersions",
    "native/Cargo.toml": '"deskbox-native"',
    "native/deskbox-native/Cargo.toml": 'name = "deskbox_native"',
    "native/include/deskbox_native.h": "DESKBOX_NATIVE_DLL_NAME",
    "installer/DeskBox.iss": IDENTITIES[0],
    "installer/DeskBox.arm64.iss": IDENTITIES[0],
    "scripts/Test-DeskBoxDirectReleaseConsistency.ps1": '"$projectVersion.0"',
}


class BrandingError(ValueError):
    """An unsupported input must leave the source tree untouched."""


def git(root: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    result = subprocess.run(["git", "-C", str(root), *args], input=input_bytes, capture_output=True)
    if result.returncode:
        raise BrandingError("root must be a readable Git checkout")
    return result.stdout


def reject_reparse(path: Path) -> None:
    """lstat does not follow the junction/symlink being checked."""
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or getattr(metadata, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
        raise BrandingError(f"unsupported link or reparse point: {path}")


def controlled_path(root: Path, path: Path, *, required: bool = False) -> None:
    """Reject every source/output ancestor before content access or mutation."""
    try:
        relative = path.relative_to(root)
    except ValueError as error:
        raise BrandingError("source/output path is outside the controlled root") from error
    current = root
    for part in relative.parts:
        current /= part
        try:
            reject_reparse(current)
        except FileNotFoundError:
            if required:
                raise BrandingError(f"missing tracked input: {path}")
            break
        if current != path and not current.is_dir():
            raise BrandingError(f"source/output parent is not a directory: {path}")
    if not path.resolve(strict=required).is_relative_to(root):
        raise BrandingError(f"resolved source/output path escapes controlled root: {path}")


def load_config(path: Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    config = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(config, dict) or type(config.get("schemaVersion")) is not int or config["schemaVersion"] != 1:
        raise BrandingError("unsupported config schemaVersion")
    for key in ("productName", "repository", "upstreamRepository", "upstreamRef", "upstreamCommit", "upstreamReleaseCommit", "upstreamVersion", "productVersion", "packageIdentity", "productionInstanceScope"):
        if not isinstance(config.get(key), str) or not config[key]:
            raise BrandingError(f"missing or invalid config {key}")
    if config["productName"] != "DeskCue" or config["repository"] != "CyberShadowX/DeskCue" or config["upstreamRepository"] != "Tianyu199509/DeskBox":
        raise BrandingError("config repositories/product do not identify the authorized fork")
    if not re.fullmatch(r"[0-9a-f]{40}", config["upstreamCommit"]):
        raise BrandingError("upstreamCommit must be an exact Git SHA1")
    if not re.fullmatch(r"[0-9a-f]{40}", config["upstreamReleaseCommit"]):
        raise BrandingError("upstreamReleaseCommit must be an exact Git SHA1")
    if not re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", config["upstreamVersion"]):
        raise BrandingError("upstreamVersion must have three numeric components")
    revision = config.get("brandingRevision")
    if type(revision) is not int or not 1 <= revision <= 65535:
        raise BrandingError("brandingRevision must be 1..65535")
    if config["productVersion"] != f'{config["upstreamVersion"]}.{revision}' or any(int(p) > 65535 for p in config["productVersion"].split(".")):
        raise BrandingError("productVersion must equal upstreamVersion.brandingRevision with four bounded components")
    if config["upstreamRef"] != "v" + config["upstreamVersion"]:
        raise BrandingError("upstreamRef must identify the upstream stable version")
    expected = {old: str(uuid.uuid5(uuid.NAMESPACE_DNS, "CyberShadowX.DeskCue." + old)).upper() for old in IDENTITIES}
    if config.get("identityMappings") != expected:
        raise BrandingError("identityMappings must contain exactly the fixed fork-owned GUID mappings")
    if config["packageIdentity"] != "CyberShadowX.DeskCue" or config["productionInstanceScope"] != "0F10D29D":
        raise BrandingError("unexpected package identity or production instance scope")
    return config, raw


def excluded(name: str) -> bool:
    parts = PurePosixPath(name).parts
    lower = tuple(p.lower() for p in parts)
    return (any(p in EXCLUDED for p in lower) or lower[0] == "deskcue"
            or lower[:2] == ("docs", "superpowers")
            or lower[-1] in {"agents.md", "upstream.md", "handoff.md", ".gitignore"})


def protected(name: str) -> bool:
    parts = PurePosixPath(name).parts
    return (any(p.lower() in {"thirdparty", "third-party", "third_party", "vendor", "licenses"} for p in parts)
            or bool(re.match(r"(?:licen[cs]e|notice|copyright|third[-_]?party)(?:[._-]|$)", parts[-1], re.I)))


def rename(value: str) -> str:
    for old, new in NAMES:
        value = value.replace(old, new)
    return value


def decode_text(name: str, data: bytes) -> tuple[str, str, bytes] | None:
    path = PurePosixPath(name)
    if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {".gitignore", ".gitattributes", ".editorconfig", "CODEOWNERS"}:
        return None
    for bom, encoding in ((codecs.BOM_UTF32_LE, "utf-32-le"), (codecs.BOM_UTF32_BE, "utf-32-be"), (codecs.BOM_UTF8, "utf-8"), (codecs.BOM_UTF16_LE, "utf-16-le"), (codecs.BOM_UTF16_BE, "utf-16-be")):
        if data.startswith(bom):
            return data[len(bom):].decode(encoding), encoding, bom
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8"), "utf-8", b""
    except UnicodeDecodeError:
        # A reversible byte mapping preserves legacy Inno language encodings.
        # Branding replacements contain ASCII only, so no codepage is guessed.
        return data.decode("latin-1"), "latin-1", b""


def transform_line(line: str, config: dict) -> str:
    if re.search(r"copyright|SPDX-License-Identifier|\(c\)|©", line, re.I):
        return line
    held: list[str] = []
    own = "https://github.com/" + config["repository"]
    source = "https://github.com/" + config["upstreamRepository"]
    api = "https://api.github.com/repos/"

    def hold(value: str) -> str:
        held.append(value)
        return f"\x01{len(held) - 1}\x02"

    def url(match: re.Match) -> str:
        value = match[0]
        for old, new in ((source, own), (api + config["upstreamRepository"], api + config["repository"]),
                         ("https://deskbox.fun/update/stable.json", own + "/releases/latest/download/stable.json"),
                         ("https://deskbox.fun/download", own + "/releases/latest")):
            if value == old or value.startswith(old + "/") or (value.startswith(old) and value[len(old):len(old)+1] in {"?", "#", ")", "]", "`"}):
                return hold(new + value[len(old):])
        base = "https://deskbox.fun"
        if (value == base or value.startswith(base) and value[len(base):len(base)+1] in {"?", "#", ")", "]", "`"}
                or value.startswith(base + "/") and value[len(base + "/"):] in {"", ")", "]", "`"}):
            return hold(own + value[len("https://deskbox.fun"):])
        # Unknown URLs, including payments/feedback/stats, are not ours.
        return hold(value)

    line = re.sub(r"https?://[^\s\"'<>]+", url, line)
    line = re.sub(r"(?:[A-Za-z0-9-]+\.)*deskbox\.fun", lambda m: hold(m[0]), line, flags=re.I)
    line = line.replace("D1FC332A.DeskBoxWidgets", config["packageIdentity"])
    for old, new in config["identityMappings"].items():
        line = re.sub(re.escape(old), lambda _: new, line, flags=re.I)
    line = line.replace("7F3A9B2E", config["productionInstanceScope"])
    line = rename(line)
    return re.sub(r"\x01(\d+)\x02", lambda m: held[int(m[1])], line)


def transform_text(name: str, text: str, config: dict) -> str:
    text = "".join(transform_line(line, config) for line in text.splitlines(keepends=True))
    version = config["productVersion"]
    publisher = config["repository"].split("/", 1)[0]
    upstream = re.escape(config["upstreamVersion"])
    if name == "src/DeskBox/DeskBox.csproj":
        for tag in ("Version", "AssemblyVersion", "FileVersion", "InformationalVersion"):
            pattern = rf"(<{tag}>){upstream}(?:\.0)?(</{tag}>)"
            text, count = re.subn(pattern, lambda m: m[1] + version + m[2], text)
            if count != 1:
                raise BrandingError(f"missing or ambiguous project version anchor: {tag}")
    if name == "src/DeskBox/Package.appxmanifest":
        text, count = re.subn(rf'(\bVersion="){upstream}\.0(")', lambda m: m[1] + version + m[2], text)
        if count != 1:
            raise BrandingError("missing or ambiguous package version anchor")
        text, count = re.subn(r"(<PublisherDisplayName>)[^<]*(</PublisherDisplayName>)", lambda m: m[1] + publisher + m[2], text)
        if count != 1:
            raise BrandingError("missing or ambiguous package publisher display anchor")
    if name == "src/DeskBox.Updater/DeskBox.Updater.csproj":
        # Upstream leaves updater version metadata at the SDK default 1.0.0.
        metadata = "".join(f"<{tag}>{version}</{tag}>" for tag in ("Version", "AssemblyVersion", "FileVersion", "InformationalVersion"))
        if any(f"<{tag}>" in text for tag in ("Version", "AssemblyVersion", "FileVersion", "InformationalVersion")):
            raise BrandingError("updater metadata changed upstream; review version recipe")
        text, count = re.subn(r"(<PropertyGroup(?:\s[^>]*)?>)", lambda m: m[1] + metadata, text, count=1)
        if count != 1:
            raise BrandingError("missing updater property group")
    if name == "src/DeskBox/app.manifest":
        text, count = re.subn(r'(<assemblyIdentity\s+version=")[^"]+("\s+name="DeskCue")', lambda m: m[1] + version + m[2], text)
        if count != 1:
            raise BrandingError("missing application manifest version anchor")
    if name in {"installer/DeskBox.iss", "installer/DeskBox.arm64.iss"}:
        for key in ("MyAppVersion", "MyAppVersionInfo"):
            text, count = re.subn(rf'(#define {key} "){upstream}(?:\.0)?(")', lambda m: m[1] + version + m[2], text)
            if count != 1:
                raise BrandingError(f"missing or ambiguous installer version anchor: {name} {key}")
        text, count = re.subn(r'(?m)^(#define[ \t]+MyAppPublisher[ \t]+")[^"\r\n]*(")', lambda m: m[1] + publisher + m[2], text)
        if count != 1:
            raise BrandingError(f"missing or ambiguous installer publisher anchor: {name}")
    if name == "scripts/Test-DeskBoxDirectReleaseConsistency.ps1":
        text = text.replace('"$projectVersion.0"', "$projectVersion")
    if name == "src/DeskBox/Services/ReleaseNotesService.cs":
        pattern = r'(KnownReleaseVersions\s*=\s*\[\s*)"' + upstream + r'"'
        text, count = re.subn(pattern, lambda m: m[1] + f'"{version}", "{config["upstreamVersion"]}"', text)
        if count != 1:
            raise BrandingError("unknown current release-notes list anchor")
    return text


def brand(root: Path, config: dict, config_bytes: bytes) -> dict:
    if not root.is_absolute() or root == Path(root.anchor) or ".." in root.parts:
        raise BrandingError("root must be an absolute, controlled repository directory")
    for ancestor in reversed((root, *root.parents)):
        reject_reparse(ancestor)
    if not root.is_dir():
        raise BrandingError("root must be a repository directory")
    root = root.resolve()
    top = Path(os.fsdecode(git(root, "rev-parse", "--show-toplevel")).strip()).resolve()
    if root != top:
        raise BrandingError("root must equal the Git working-tree root")
    if os.fsdecode(git(root, "rev-parse", "HEAD")).strip() != config["upstreamCommit"]:
        raise BrandingError("checkout HEAD does not match configured upstreamCommit")
    if (root / "DeskCue.sln").exists() or not (root / "DeskBox.sln").is_file():
        raise BrandingError("fresh upstream DeskBox.sln sentinel is required")
    names = sorted(os.fsdecode(p) for p in git(root, "ls-files", "-z").split(b"\0") if p)
    selected = [p for p in names if not excluded(p)]
    for name in selected:
        parts = PurePosixPath(name).parts
        if name.startswith("/") or ".." in parts:
            raise BrandingError(f"unsupported source link/path: {name}")
        path = root / name
        controlled_path(root, path, required=True)
        if not path.is_file():
            raise BrandingError(f"missing tracked input: {name}")
    # Validate the complete source inventory before reading any source content.
    originals = {name: (root / name).read_bytes() for name in selected}
    for name, anchor in CRITICAL.items():
        decoded = decode_text(name, originals.get(name, b""))
        if name not in originals or decoded is None or anchor not in decoded[0]:
            raise BrandingError(f"missing critical upstream anchor: {name}")
    package = decode_text("src/DeskBox/Package.appxmanifest", originals["src/DeskBox/Package.appxmanifest"])[0]
    for identity, expected_count in ((IDENTITIES[1], 1), (IDENTITIES[2], 1), (IDENTITIES[3], 2)):
        if len(re.findall(re.escape(identity), package, re.I)) != expected_count:
            raise BrandingError("upstream package ownership/COM identity anchors changed")
    dirty = [os.fsdecode(p) for p in git(root, "diff", "--name-only", "-z", "HEAD").split(b"\0") if p and not excluded(os.fsdecode(p))]
    if dirty:
        raise BrandingError("fresh source required; tracked product files have local changes")
    outputs: dict[str, bytes] = {}
    destination_keys: set[str] = set()
    for name, data in originals.items():
        destination = rename(name)
        key = destination.casefold()
        if key in destination_keys:
            raise BrandingError(f"branding path collision: {destination}")
        destination_keys.add(key)
        if destination != name and (root / destination).exists():
            raise BrandingError(f"branding destination already exists: {destination}")
        decoded = None if protected(name) else decode_text(name, data)
        if decoded is not None:
            text, encoding, bom = decoded
            data = bom + transform_text(name, text, config).encode(encoding)
        outputs[destination] = data
    current_notes = f'docs/releases/v{config["productVersion"]}.md'
    upstream_notes = f'docs/releases/v{config["upstreamVersion"]}.md'
    if upstream_notes not in outputs or (root / current_notes).exists():
        raise BrandingError("missing upstream notes or colliding current release notes")
    outputs[current_notes] = (f'# DeskCue {config["productVersion"]}\n\nDerived from [{config["upstreamRepository"]} {config["upstreamRef"]}]'
                              f'(https://github.com/{config["upstreamRepository"]}/tree/{config["upstreamCommit"]}). '
                              f'Branding revision {config["brandingRevision"]}; original upstream release notes follow.\n\n').encode() + outputs[upstream_notes]
    source_digest = hashlib.sha256()
    for name, data in originals.items():
        source_digest.update(name.encode("utf-8") + b"\0" + hashlib.sha256(data).digest())
    provenance = {**config, "recipeSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  "configSha256": hashlib.sha256(config_bytes).hexdigest(), "sourceTreeSha256": source_digest.hexdigest(),
                  "sourceFileCount": len(originals)}
    provenance_name = "deskcue/provenance.json"
    if (root / provenance_name).exists():
        raise BrandingError("existing provenance would be overwritten")
    outputs[provenance_name] = (json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    for name in outputs:
        controlled_path(root, root / name)
    index_path = Path(os.fsdecode(git(root, "rev-parse", "--git-path", "index")).strip())
    if not index_path.is_absolute():
        index_path = root / index_path
    index_before = index_path.read_bytes() if index_path.exists() else None
    # Every operation has been validated. Roll back owned files on an IO failure.
    touched: set[str] = set()
    index_touched = False
    try:
        for name, data in outputs.items():
            if originals.get(name) == data:
                continue
            touched.add(name)
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        for name in originals.keys() - outputs.keys():
            touched.add(name)
            (root / name).unlink()
        if (index_path.read_bytes() if index_path.exists() else None) != index_before:
            raise BrandingError("Git index changed during generation")
        # Renamed upstream DLLs remain source inputs even when *.dll is ignored.
        # Literal NUL pathspecs avoid wildcard expansion, command-line limits and
        # accidentally staging unrelated ignored files or private build outputs.
        index_touched = True
        git(root, "-c", "core.autocrlf=false", "-c", "core.eol=lf", "--literal-pathspecs",
            "add", "--force", "--pathspec-from-file=-", "--pathspec-file-nul",
            input_bytes=b"".join(name.encode("utf-8") + b"\0" for name in outputs))
    except (OSError, BrandingError):
        for name in touched:
            path = root / name
            if name in originals:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(originals[name])
            elif path.is_file():
                path.unlink()
        if index_touched:
            if index_before is None:
                index_path.unlink(missing_ok=True)
            else:
                index_path.write_bytes(index_before)
        raise
    # Remove only empty original source folders, retaining excluded/user content.
    for parent in sorted({(root / n).parent for n in originals}, key=lambda p: len(p.parts), reverse=True):
        while parent != root:
            try:
                parent.rmdir()
            except OSError:
                break
            parent = parent.parent
    return provenance


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        config, raw = load_config(args.config)
        provenance = brand(args.root, config, raw)
    except (BrandingError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"branding error: {error}", file=sys.stderr)
        return 2
    print(f'DeskCue {provenance["productVersion"]}: branded {provenance["sourceFileCount"]} tracked files')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
