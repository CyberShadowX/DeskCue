"""Validate local/cloud retail evidence before advancing a DeskCue receipt.

Only the compact receipt is public metadata. Run results retain local evidence
locations for the local publisher and must not be uploaded as release assets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET


class ReleaseContractError(ValueError):
    pass


HASH = re.compile(r"[0-9a-fA-F]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
REQUIRED_PE = (
    "DeskCue.exe", "DeskCue.Updater.exe", "DeskCue.ThumbnailProxy.exe",
    "deskcue_native.dll", "EverythingSdk.dll",
    "Microsoft.WindowsAppRuntime.Insights.Resource.dll",
)
REQUIRED_PAYLOAD = (*REQUIRED_PE, "DeskCue.pri", "Microsoft.UI.Input.dll",
                    "Microsoft.ui.xaml.dll", "Microsoft.WindowsAppRuntime.dll",
                    "DeskCue.InstallManifest.txt", "ThirdParty/Everything/LICENSE.txt",
                    "LICENSE", "UPSTREAM.md")
FORBIDDEN = {name.casefold() for name in (
    "coreclr.dll", "clrjit.dll", "hostfxr.dll", "hostpolicy.dll", "System.Private.CoreLib.dll",
    "DeskCue.dll", "DeskCue.deps.json", "DeskCue.runtimeconfig.json",
    "DeskCue.Updater.dll", "DeskCue.Updater.deps.json", "DeskCue.Updater.runtimeconfig.json",
)}


def require(condition, message):
    if not condition:
        raise ReleaseContractError(message)


def safe_path(path, root=None):
    """Check lexical containment and every existing component before resolving.

    Resolve alone conceals the junction/symlink that caused an escape. Check
    lstat from the filesystem anchor through the leaf, including root aliases,
    then independently check the resolved location. Missing output leaves are
    permitted; an existing ancestor must always be an ordinary directory/file.
    """
    def lexical(value):
        value = Path(value)
        require(".." not in value.parts, "parent traversal is not a safe release path")
        text = os.fspath(value)
        require(not text.startswith(("\\\\?\\", "\\\\.\\")), "device path aliases are not allowed")
        return Path(os.path.abspath(text))

    def inspect(value):
        for component in (*reversed(value.parents), value):
            try:
                info = component.lstat()
            except FileNotFoundError:
                continue
            require(not stat.S_ISLNK(info.st_mode) and not (getattr(info, "st_file_attributes", 0) & 0x400),
                    "release path contains a symlink, junction, or reparse point")
        resolved = value.resolve(strict=False)
        require(os.path.normcase(str(resolved)) == os.path.normcase(str(value)),
                "release path resolves through an alias")
        return resolved

    candidate = lexical(path)
    boundary = lexical(root) if root is not None else candidate.parent
    try:
        common = os.path.commonpath((str(boundary), str(candidate)))
    except ValueError as exc:
        raise ReleaseContractError("release path escaped its intended root") from exc
    require(os.path.normcase(common) == os.path.normcase(str(boundary)), "release path escaped its intended root")
    resolved_root = inspect(boundary)
    resolved_candidate = inspect(candidate)
    require(os.path.normcase(os.path.commonpath((str(resolved_root), str(resolved_candidate))))
            == os.path.normcase(str(resolved_root)), "resolved release path escaped its intended root")
    return candidate


def release_run_layout(run_root, frozen_source, platform=None):
    """Pair canonical evidence with a short, independently guarded checkout."""
    run = safe_path(run_root)
    require(len(run.parents) >= 5 and run.parent.name == "runs"
            and re.fullmatch(r"r-[0-9a-f]{16}", run.name), "invalid canonical release run layout")
    rid = run.parent.parent.name
    require(rid in ("win-x64", "win-arm64"), "invalid release run architecture")
    if platform is not None:
        require(rid == ("win-arm64" if platform == "ARM64" else "win-x64"), "release run platform mismatch")
    workspace = safe_path(run.parents[4], run.parents[4])
    release = safe_path(workspace / ".artifacts/deskcue-release" / rid, workspace)
    require(run == release / "runs" / run.name, "release run escaped its canonical evidence root")
    frozen = safe_path(frozen_source, workspace)
    expected = safe_path(workspace / ".artifacts/b" / run.name, workspace)
    require(frozen == expected, "frozen source must use the paired short checkout layout")
    return {"workspaceRoot": workspace, "runRoot": run, "releaseRoot": release, "frozenSource": frozen}


def sha256(path):
    path = safe_path(path)
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON field: {key}")
        result[key] = value
    return result


def load_json(path):
    path = safe_path(path)
    try:
        result = json.loads(Path(path).read_text(encoding="utf-8-sig"), object_pairs_hook=_json_object)
        require(isinstance(result, dict), "JSON evidence must be an object")
        return result
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseContractError(f"cannot read JSON evidence: {Path(path).name}") from exc


def _integer(value, name, minimum=0):
    require(type(value) is int and value >= minimum, f"invalid {name}")
    return value


def _version(value, count):
    require(isinstance(value, str) and re.fullmatch(r"(?:0|[1-9]\d*)(?:\.(?:0|[1-9]\d*)){" + str(count - 1) + "}", value),
            "version must have bounded numeric components")
    require(all(int(part) <= 65535 for part in value.split(".")), "version component exceeds 65535")


def validate_metadata(source_root, source_commit):
    root = safe_path(source_root, source_root)
    require(isinstance(source_commit, str) and COMMIT.fullmatch(source_commit), "invalid source commit")
    config = load_json(root / "deskcue/config.json")
    provenance = load_json(root / "deskcue/provenance.json")
    require(config.get("schemaVersion") == 1, "unsupported configuration schema")
    for name, expected in (("productName", "DeskCue"), ("repository", "CyberShadowX/DeskCue"),
                           ("upstreamRepository", "Tianyu199509/DeskBox")):
        require(config.get(name) == expected, f"invalid {name}")
    _version(config.get("productVersion"), 4)
    _version(config.get("upstreamVersion"), 3)
    revision = _integer(config.get("brandingRevision"), "brandingRevision", 1)
    require(revision <= 65535 and config["productVersion"] == f'{config["upstreamVersion"]}.{revision}',
            "product version differs from upstream version and branding revision")
    require(isinstance(config.get("upstreamCommit"), str) and COMMIT.fullmatch(config["upstreamCommit"]),
            "invalid upstream commit")
    require(config.get("upstreamRef") == "v" + config["upstreamVersion"], "upstream tag/version mismatch")
    for key, expected in config.items():
        require(provenance.get(key) == expected, f"provenance mismatch: {key}")
    for field, path in (("recipeSha256", root / "deskcue/brand.py"), ("configSha256", root / "deskcue/config.json")):
        require(provenance.get(field) == sha256(path), f"provenance mismatch: {field}")
    require(isinstance(provenance.get("sourceTreeSha256"), str) and HASH.fullmatch(provenance["sourceTreeSha256"]),
            "invalid source tree provenance hash")
    _integer(provenance.get("sourceFileCount"), "sourceFileCount", 1)
    return {**config, "sourceCommit": source_commit}


def assert_clean_source(source_root, source_commit):
    root = safe_path(source_root, source_root)
    def git(*args):
        command = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8")
        require(command.returncode == 0, "Git source inspection failed")
        return command.stdout.strip()
    require(safe_path(git("rev-parse", "--show-toplevel")) == root, "source must be the repository root")
    require(git("rev-parse", "HEAD") == source_commit, "source commit changed during build")
    require(not git("status", "--porcelain=v1", "--untracked-files=all"), "source must be clean")


def validate_trx(paths):
    paths = list(paths)
    require(bool(paths), "no completed TRX test results")
    total = 0
    namespace = {"t": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}
    for path in paths:
        path = safe_path(path)
        try:
            document = ET.parse(path)
        except (OSError, ET.ParseError) as exc:
            raise ReleaseContractError("cannot read completed TRX evidence") from exc
        summary = document.find("t:ResultSummary", namespace)
        require(summary is not None and summary.get("outcome") == "Completed", "TRX did not complete")
        counters = summary.find("t:Counters", namespace)
        require(counters is not None, "TRX counters missing")
        try:
            values = {key: int(value) for key, value in counters.attrib.items()}
        except ValueError as exc:
            raise ReleaseContractError("TRX counters are not numeric") from exc
        count = values.get("total", 0)
        require(count > 0 and values.get("executed") == count and values.get("passed") == count,
                "TRX total/executed/passed counts differ")
        require(all(values.get(key) == 0 for key in ("failed", "error", "timeout", "aborted", "notExecuted")),
                "TRX failed, aborted, or incomplete tests")
        require(all(value >= 0 for value in values.values()), "negative TRX counters")
        require(all(value == 0 for key, value in values.items() if key not in ("total", "executed", "passed", "completed")),
                "TRX contains non-passing counters")
        results = document.findall("t:Results/t:UnitTestResult", namespace)
        require(len(results) == count and all(result.get("outcome") == "Passed" for result in results),
                "TRX counters do not match Passed test results")
        total += count
    return {"total": total, "passed": total, "failed": 0, "skipped": 0}


def validate_management_results(path):
    value = load_json(path)
    require(value.get("schemaVersion") == 1 and value.get("status") == "passed", "management tests did not pass")
    total = _integer(value.get("total"), "management test total", 1)
    require(type(value.get("passed")) is int and value["passed"] == total and value.get("failed") == 0
            and value.get("skipped") == 0, "management tests must all pass")
    return {"total": total, "passed": total, "failed": 0, "skipped": 0}


def pe_machine(path):
    path = safe_path(path)
    try:
        with Path(path).open("rb") as stream:
            header = stream.read(64)
            require(len(header) == 64 and header[:2] == b"MZ", "invalid PE image")
            offset = struct.unpack_from("<I", header, 0x3C)[0]
            require(64 <= offset <= Path(path).stat().st_size - 6, "invalid PE header offset")
            stream.seek(offset)
            image = stream.read(6)
            require(image[:4] == b"PE\0\0", "invalid PE signature")
            return struct.unpack_from("<H", image, 4)[0]
    except OSError as exc:
        raise ReleaseContractError(f"missing PE image: {Path(path).name}") from exc


def _relative_name(name):
    require(isinstance(name, str) and bool(name) and "\\" not in name and ":" not in name,
            "unsafe manifest path")
    relative = PurePosixPath(name)
    require(not relative.is_absolute() and all(part not in ("", ".", "..") for part in name.split("/")),
            "unsafe manifest path")
    return relative


def safe_tree_files(directory):
    """Validate a child before descending; never enumerate through a junction."""
    root = safe_path(directory, directory)
    def visit(folder):
        safe_path(folder, root)
        with os.scandir(folder) as entries:
            children = sorted(entries, key=lambda entry: entry.name)
        for entry in children:
            path = safe_path(entry.path, root)
            if entry.is_dir(follow_symlinks=False):
                yield from visit(path)
            else:
                require(entry.is_file(follow_symlinks=False), "release tree contains a non-regular file")
                yield path
    yield from visit(root)


def payload_inventory(payload):
    result = {}
    payload = safe_path(payload, payload)
    for path in safe_tree_files(payload):
        result[path.relative_to(payload).as_posix()] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    return result


def check_retail_snapshot(evidence_path):
    evidence_path = safe_path(evidence_path)
    evidence = load_json(evidence_path)
    layout = release_run_layout(evidence_path.parent, evidence["sourceRoot"])
    payload = safe_path(evidence["payloadDirectory"], layout["frozenSource"])
    require(payload_inventory(payload) == evidence["files"],
            "payload changed during installer packaging")


def validate_retail(source_root, summary_path, platform, source_commit):
    source_root = safe_path(source_root, source_root)
    summary_path = safe_path(summary_path, source_root)
    require(platform in ("x64", "ARM64"), "unsupported platform")
    rid = "win-arm64" if platform == "ARM64" else "win-x64"
    expected_machine = 0xAA64 if platform == "ARM64" else 0x8664
    summary = load_json(summary_path)
    expected = {
        "schemaVersion": 1, "productProfile": "retail", "deploymentProfile": "full",
        "configuration": "Release", "smokeHarnessEnabled": False, "selfContained": True,
        "windowsAppSdkSelfContained": True, "gitCommit": source_commit, "gitDirty": False,
        "sourceStableDuringPublish": True, "platform": platform, "runtimeIdentifier": rid,
        "unexpectedWarningCodes": [], "smokeHarnessBinaryMatches": [],
    }
    for key, value in expected.items():
        actual = summary.get(key)
        require(actual == value and type(actual) is type(value), f"retail summary rejected: {key}")
    require(isinstance(summary.get("publishDirectory"), str), "retail publish directory missing")
    payload = safe_path(summary["publishDirectory"], source_root)
    require(payload.is_dir(), "retail payload missing")
    manifest = payload / "DeskCue.InstallManifest.txt"
    require(isinstance(summary.get("installManifest"), str) and safe_path(summary["installManifest"], payload) == manifest,
            "retail install manifest location mismatch")
    inventory = payload_inventory(payload)
    for name in REQUIRED_PAYLOAD:
        require(name in inventory, f"required retail file missing: {name}")
    manifest_names = safe_path(manifest, payload).read_text(encoding="utf-8-sig").splitlines()
    for name in manifest_names:
        _relative_name(name)
    require(len({name.casefold() for name in manifest_names}) == len(manifest_names), "duplicate manifest entry")
    require(set(manifest_names) == set(inventory), "install manifest differs from actual payload files")
    require(summary.get("installManifestFileCount") == len(inventory) and summary.get("publishFileCount") == len(inventory),
            "retail manifest file count differs")
    for name in inventory:
        basename = PurePosixPath(name).name.casefold()
        require(basename not in FORBIDDEN and not basename.endswith(".pdb"), "retail includes managed/JIT/symbol files")
        require(not (basename.endswith((".exe", ".dll")) and "deskbox" in basename), "foreign DeskBox executable in retail")
    for name in ("LICENSE", "UPSTREAM.md"):
        require(sha256(Path(source_root) / name) == inventory[name]["sha256"], f"retail {name} differs from source")
    license_text = safe_path(payload / "LICENSE", payload).read_text(encoding="utf-8-sig")
    require("GNU GENERAL PUBLIC LICENSE" in license_text and "Version 3" in license_text, "GPL-3 license missing")
    require("Tianyu199509/DeskBox" in safe_path(payload / "UPSTREAM.md", payload).read_text(encoding="utf-8-sig"),
            "upstream attribution missing")
    entries = summary.get("peFiles")
    require(isinstance(entries, list) and all(isinstance(entry, dict) for entry in entries), "retail PE evidence missing")
    names = [entry.get("file") for entry in entries]
    require(len(set(names)) == len(names) and set(REQUIRED_PE).issubset(names), "retail PE evidence incomplete")
    for entry in entries:
        name = entry["file"]
        _relative_name(name)
        require(name in inventory, "retail PE evidence references absent file")
        require(pe_machine(payload / name) == expected_machine, f"PE machine/architecture mismatch: {name}")
        require(entry.get("machine", "").casefold() == f"0x{expected_machine:04x}", "PE evidence machine mismatch")
        require(entry.get("bytes") == inventory[name]["bytes"], f"PE bytes mismatch: {name}")
        require(isinstance(entry.get("sha256"), str) and entry["sha256"].lower() == inventory[name]["sha256"],
                f"PE hash mismatch: {name}")
    native = summary.get("rustNative", {})
    require(native.get("publishMatchesStaging") is True and isinstance(native.get("sha256"), str)
            and native["sha256"].lower() == inventory["deskcue_native.dll"]["sha256"], "Rust native staging/hash mismatch")
    return {"sourceRoot": str(source_root), "payloadDirectory": str(payload), "files": inventory}


def create_receipt(source_root, summary_path, installer_path, trx_paths, management_path, platform, source_commit):
    metadata = validate_metadata(source_root, source_commit)
    tests = validate_trx(trx_paths)
    management = validate_management_results(management_path)
    tests = {key: tests[key] + management[key] for key in tests}
    validate_retail(source_root, summary_path, platform, source_commit)
    installer = safe_path(installer_path)
    architecture = "arm64" if platform == "ARM64" else "x64"
    require(installer.name == f'DeskCue_Setup_{metadata["productVersion"]}_{architecture}.exe',
            "installer must have the exact DeskCue version/platform filename")
    require(pe_machine(installer) in (0x14C, 0x8664, 0xAA64), "unsupported installer PE machine")
    return {
        "schemaVersion": 1, "status": "passed", "platform": platform,
        "runtimeIdentifier": "win-arm64" if platform == "ARM64" else "win-x64",
        "version": metadata["productVersion"], "sourceCommit": source_commit,
        "upstreamRepository": metadata["upstreamRepository"], "upstreamCommit": metadata["upstreamCommit"],
        "brandingRevision": metadata["brandingRevision"],
        "installer": {"fileName": installer.name, "path": installer.name,
                      "bytes": installer.stat().st_size, "sha256": sha256(installer)},
        "tests": tests, "retailSummarySha256": sha256(summary_path),
    }


def verify_receipt(receipt, installer):
    installer = safe_path(installer)
    require(receipt.get("schemaVersion") == 1 and receipt.get("status") == "passed", "invalid release receipt")
    platform = receipt.get("platform")
    require(platform in ("x64", "ARM64"), "invalid receipt platform")
    rid = "win-arm64" if platform == "ARM64" else "win-x64"
    require(receipt.get("runtimeIdentifier") == rid, "receipt platform/RID mismatch")
    _version(receipt.get("version"), 4)
    require(COMMIT.fullmatch(receipt.get("sourceCommit", "")) and COMMIT.fullmatch(receipt.get("upstreamCommit", "")),
            "invalid receipt source provenance")
    require(receipt.get("upstreamRepository") == "Tianyu199509/DeskBox", "invalid receipt upstream repository")
    require(receipt["version"].split(".")[-1] == str(_integer(receipt.get("brandingRevision"), "branding revision", 1)),
            "receipt branding revision/version mismatch")
    require(HASH.fullmatch(receipt.get("retailSummarySha256", "")), "invalid retail summary hash")
    tests = receipt.get("tests", {})
    total = _integer(tests.get("total"), "test total", 1)
    require(tests.get("passed") == total and tests.get("failed") == 0 and tests.get("skipped") == 0, "receipt tests did not pass")
    item = receipt.get("installer", {})
    arch = "arm64" if platform == "ARM64" else "x64"
    expected = f'DeskCue_Setup_{receipt["version"]}_{arch}.exe'
    require(item.get("fileName") == expected and item.get("path") == expected and Path(installer).name == expected,
            "invalid receipt installer path/name")
    require(Path(installer).is_file() and item.get("bytes") == Path(installer).stat().st_size,
            "installer bytes differ from receipt")
    require(isinstance(item.get("sha256"), str) and item["sha256"].lower() == sha256(installer),
            "installer hash differs from receipt")
    require(pe_machine(installer) in (0x14C, 0x8664, 0xAA64), "invalid installer PE")


def atomic_write(path, data):
    path = safe_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    safe_path(path, path.parent)
    descriptor, temp = tempfile.mkstemp(prefix=f".{path.name}-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        safe_path(temp, path.parent)
        safe_path(path, path.parent)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            safe_path(temp, path.parent)
            os.unlink(temp)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def promote_receipt(release_root, receipt, installer_path):
    """Publish the pointer last. An existing named installer is immutable."""
    verify_receipt(receipt, installer_path)
    root = safe_path(release_root, release_root)
    target = safe_path(root / receipt["installer"]["fileName"], root)
    checksum = safe_path(root / (target.name + ".sha256"), root)
    receipt_path = safe_path(root / "receipt.json", root)
    root.mkdir(parents=True, exist_ok=True)
    safe_path(root, root)
    checksum_bytes = f'{receipt["installer"]["sha256"]}  {target.name}\n'.encode("ascii")
    if target.exists():
        require(sha256(target) == receipt["installer"]["sha256"], "existing immutable installer has different bytes")
    if checksum.exists():
        require(safe_path(checksum, root).read_bytes() == checksum_bytes, "existing checksum has different bytes")
    if not target.exists():
        descriptor, temp = tempfile.mkstemp(prefix=".installer-", suffix=".tmp", dir=root)
        os.close(descriptor)
        try:
            shutil.copyfile(safe_path(installer_path), safe_path(temp, root))
            require(sha256(temp) == receipt["installer"]["sha256"], "installer changed during copy")
            safe_path(temp, root)
            safe_path(target, root)
            os.replace(temp, target)
        finally:
            if os.path.exists(temp):
                safe_path(temp, root)
                os.unlink(temp)
    if not checksum.exists():
        atomic_write(checksum, checksum_bytes)
    verify_receipt(receipt, target)
    atomic_write(receipt_path, json_bytes(receipt))


def run_management_tests(source_root, output):
    source_root = safe_path(source_root, source_root)
    tests_root = safe_path(source_root / "deskcue/tests", source_root)
    list(safe_tree_files(tests_root))
    suite = unittest.TestLoader().discover(str(tests_root), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    failures = len(result.errors) + len(result.failures) + len(result.unexpectedSuccesses)
    skipped = len(result.skipped) + len(result.expectedFailures)
    value = {"schemaVersion": 1, "status": "passed" if result.wasSuccessful() and not skipped else "failed",
             "total": result.testsRun, "passed": result.testsRun - failures - skipped,
             "failed": failures, "skipped": skipped}
    atomic_write(output, json_bytes(value))
    validate_management_results(output)


def stage_local(result_path, destination):
    """Prepare an independently verified directory; never modify the old release."""
    result_path = safe_path(result_path)
    run_root = result_path.parent
    result = load_json(result_path)
    layout = release_run_layout(run_root, result["frozenSource"])
    receipt_path = safe_path(result["receipt"], run_root)
    installer = safe_path(result["installer"], run_root)
    frozen = layout["frozenSource"]
    retail = safe_path(result["retailSummary"], frozen)
    target = safe_path(destination, run_root)
    receipt = load_json(receipt_path)
    verify_receipt(receipt, installer)
    require(sha256(retail) == receipt["retailSummarySha256"], "retail summary changed since receipt")
    evidence = validate_retail(frozen, retail, receipt["platform"], receipt["sourceCommit"])
    require(evidence["files"] == result["payloadFiles"], "payload changed since receipt")
    require(not target.exists(), "local staging destination already exists")
    target.mkdir()
    for name in evidence["files"]:
        source = safe_path(Path(evidence["payloadDirectory"]) / name, frozen)
        copy = safe_path(target / name, target)
        copy.parent.mkdir(parents=True, exist_ok=True)
        safe_path(copy, target)
        shutil.copyfile(source, copy)
    require(payload_inventory(target) == result["payloadFiles"], "local staged payload hash mismatch")
    shutil.copyfile(safe_path(installer, run_root), safe_path(target / installer.name, target))
    verify_receipt(receipt, target / installer.name)
    safe_path(target / (installer.name + ".sha256"), target).write_text(
        f'{receipt["installer"]["sha256"]}  {installer.name}\n', encoding="ascii")
    atomic_write(target / "receipt.json", json_bytes(receipt))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    guard = commands.add_parser("guard-path")
    guard.add_argument("--root", type=Path, required=True)
    guard.add_argument("--path", type=Path, required=True)
    metadata = commands.add_parser("metadata")
    metadata.add_argument("--source-root", type=Path, required=True)
    metadata.add_argument("--commit", required=True)
    management = commands.add_parser("management-tests")
    management.add_argument("--source-root", type=Path, required=True)
    management.add_argument("--output", type=Path, required=True)
    tests = commands.add_parser("test-contract")
    tests.add_argument("--trx-dir", type=Path, required=True)
    tests.add_argument("--management-results", type=Path, required=True)
    for name in ("retail", "complete"):
        command = commands.add_parser(name)
        command.add_argument("--source-root", type=Path, required=True)
        command.add_argument("--retail-summary", type=Path, required=True)
        command.add_argument("--platform", choices=("x64", "ARM64"), required=True)
        command.add_argument("--commit", required=True)
        command.add_argument("--output", type=Path, required=True)
        if name == "complete":
            command.add_argument("--installer", type=Path, required=True)
            command.add_argument("--trx-dir", type=Path, required=True)
            command.add_argument("--management-results", type=Path, required=True)
            command.add_argument("--release-root", type=Path, required=True)
            command.add_argument("--retail-evidence", type=Path, required=True)
    snapshot = commands.add_parser("check-retail-snapshot")
    snapshot.add_argument("--evidence", type=Path, required=True)
    stage = commands.add_parser("stage-local")
    stage.add_argument("--result", type=Path, required=True)
    stage.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "guard-path":
            safe_path(args.path, args.root)
        elif args.command == "metadata":
            assert_clean_source(args.source_root, args.commit)
            list(safe_tree_files(args.source_root))
            print(json.dumps(validate_metadata(args.source_root, args.commit)))
        elif args.command == "management-tests":
            run_management_tests(args.source_root, args.output)
        elif args.command == "test-contract":
            tests = validate_trx(path for path in safe_tree_files(args.trx_dir) if path.suffix.lower() == ".trx")
            management = validate_management_results(args.management_results)
            print(json.dumps({key: tests[key] + management[key] for key in tests}))
        elif args.command == "retail":
            args.output = safe_path(args.output)
            layout = release_run_layout(args.output.parent, args.source_root, args.platform)
            args.source_root = layout["frozenSource"]
            assert_clean_source(args.source_root, args.commit)
            validate_metadata(args.source_root, args.commit)
            evidence = validate_retail(args.source_root, args.retail_summary, args.platform, args.commit)
            atomic_write(args.output, json_bytes(evidence))
        elif args.command == "complete":
            args.output = safe_path(args.output)
            run_root = args.output.parent
            layout = release_run_layout(run_root, args.source_root, args.platform)
            args.source_root = layout["frozenSource"]
            args.installer = safe_path(args.installer, run_root)
            args.trx_dir = safe_path(args.trx_dir, run_root)
            args.management_results = safe_path(args.management_results, run_root)
            args.retail_evidence = safe_path(args.retail_evidence, run_root)
            args.release_root = safe_path(args.release_root, args.release_root)
            require(args.release_root == layout["releaseRoot"],
                    "canonical release root does not own the selected run")
            assert_clean_source(args.source_root, args.commit)
            check_retail_snapshot(args.retail_evidence)
            receipt = create_receipt(args.source_root, args.retail_summary, args.installer,
                                     (path for path in safe_tree_files(args.trx_dir) if path.suffix.lower() == ".trx"),
                                     args.management_results, args.platform, args.commit)
            evidence = validate_retail(args.source_root, args.retail_summary, args.platform, args.commit)
            require(evidence == load_json(args.retail_evidence), "payload differs from verified pre-installer retail evidence")
            # Write local evidence first, then the canonical successful receipt.
            run_receipt = args.output.with_name("receipt.json")
            result = {"schemaVersion": 1, "frozenSource": str(args.source_root),
                      "payloadDirectory": evidence["payloadDirectory"], "payloadFiles": evidence["files"],
                      "retailSummary": str(safe_path(args.retail_summary, args.source_root)),
                      "receipt": str(safe_path(run_receipt, run_root)), "installer": str(args.installer)}
            atomic_write(run_receipt, json_bytes(receipt))
            atomic_write(args.output, json_bytes(result))
            promote_receipt(args.release_root, receipt, args.installer)
            print(json.dumps(receipt))
        elif args.command == "check-retail-snapshot":
            check_retail_snapshot(args.evidence)
        else:
            stage_local(args.result, args.destination)
        return 0
    except (ReleaseContractError, OSError, KeyError, TypeError) as exc:
        print(f"release validation error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
