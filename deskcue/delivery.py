#!/usr/bin/env python3
"""DeskCue source candidates and immutable GitHub delivery (Python standard library)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from urllib.error import HTTPError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


OWN_REPOSITORY = "CyberShadowX/DeskCue"
UPSTREAM_REPOSITORY = "Tianyu199509/DeskBox"
CANDIDATE_REF = "refs/heads/deskcue-candidate"
SHA = re.compile(r"^[0-9a-f]{40}$")
HASH = re.compile(r"^[0-9a-f]{64}$")
PROVENANCE_KEYS = ("repository", "upstreamRepository", "upstreamRef", "upstreamCommit",
                   "upstreamVersion", "brandingRevision", "sourceCommit", "version", "forkPatches")


class DeliveryError(RuntimeError):
    """A failed delivery gate; never recover by overwriting a release or source."""


def git(root, *args, data=None, env=None):
    command = ["git", "-C", str(root), "-c", "core.hooksPath=", *map(str, args)]
    result = subprocess.run(command, input=data, capture_output=True, env=env)
    if result.returncode:
        # Do not echo command arguments: authenticated remote URLs must not leak.
        raise DeliveryError(f"Git {args[0]} failed (exit {result.returncode}).")
    return result.stdout


def git_text(root, *args, **kwargs):
    return git(root, *args, **kwargs).decode("utf-8").strip()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (ValueError, OSError) as exc:
        raise DeliveryError(f"Cannot read JSON: {Path(path).name}.") from exc


def version_parts(value, components):
    if not isinstance(value, str) or not re.fullmatch(r"(?:0|[1-9][0-9]*)(?:\.(?:0|[1-9][0-9]*)){" + str(components - 1) + "}", value):
        raise DeliveryError("Version must have canonical numeric components.")
    result = tuple(map(int, value.split(".")))
    if any(part > 65535 for part in result):
        raise DeliveryError("Version component exceeds Windows version limits.")
    return result


def validate_identity(value):
    if not isinstance(value, dict):
        raise DeliveryError("Source identity must be a JSON object.")
    if value.get("repository") != OWN_REPOSITORY or value.get("upstreamRepository") != UPSTREAM_REPOSITORY:
        raise DeliveryError("Repository identity is outside the authorized fork/upstream pair.")
    if not SHA.fullmatch(str(value.get("upstreamCommit", ""))):
        raise DeliveryError("Upstream commit is not a full SHA.")
    upstream = value.get("upstreamVersion")
    version_parts(upstream, 3)
    revision = value.get("brandingRevision")
    if type(revision) is not int or revision < 1 or revision > 65535:
        raise DeliveryError("Branding revision must be a positive Windows version component.")
    if value.get("upstreamRef") != "v" + upstream:
        raise DeliveryError("Upstream ref must match its stable version.")
    version = value.get("version", value.get("productVersion"))
    version_parts(version, 4)
    if version != f"{upstream}.{revision}":
        raise DeliveryError("Product version disagrees with upstream/branding revision.")
    patches = value.get("forkPatches")
    if (not isinstance(patches, list) or not patches or
            any(not isinstance(name, str) or not re.fullmatch(r"[0-9A-Za-z][0-9A-Za-z._-]*\.patch", name) for name in patches) or
            len({name.casefold() for name in patches}) != len(patches)):
        raise DeliveryError("Configuration must declare the exact required fork patch filenames.")


def clean_repository(root):
    root = Path(root).resolve()
    if Path(git_text(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise DeliveryError("Source root must be the Git top-level directory.")
    if git_text(root, "status", "--porcelain", "--untracked-files=normal"):
        raise DeliveryError("Source must be committed and clean before delivery.")
    return root


def head_config(root):
    config = json.loads(git(root, "show", "HEAD:deskcue/config.json"))
    validate_identity(config)
    return config


class GitHubApi:
    """Only GitHub's API and its own release-upload endpoint receive credentials."""

    def __init__(self, token=None):
        self.token = token or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

    def request(self, path, method="GET", body=None, binary=False, missing_ok=False):
        url = path if path.startswith("https://") else "https://api.github.com/" + path.lstrip("/")
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname not in {"api.github.com", "uploads.github.com"} or parsed.username or parsed.password:
            raise DeliveryError("Refusing credentials outside GitHub API hosts.")
        headers = {"User-Agent": "DeskCue-delivery", "X-GitHub-Api-Version": "2022-11-28",
                   "Accept": "application/octet-stream" if binary else "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        if body is not None:
            if isinstance(body, bytes):
                payload = body
                headers["Content-Type"] = "application/octet-stream"
            else:
                payload = json_bytes(body)
                headers["Content-Type"] = "application/json"
        else:
            payload = None
        try:
            with build_opener(SafeGitHubRedirect()).open(Request(url, data=payload, headers=headers, method=method), timeout=120) as response:
                content = response.read()
                return content if binary else (json.loads(content) if content else None)
        except HTTPError as exc:
            if missing_ok and exc.code == 404:
                return None
            raise DeliveryError(f"GitHub API {method} failed (HTTP {exc.code}).") from None

    def releases(self, repository):
        releases = []
        for page in range(1, 11):
            batch = self.request(f"repos/{repository}/releases?per_page=100&page={page}")
            releases.extend(batch)
            if len(batch) < 100:
                return releases
        raise DeliveryError("Release history exceeds the bounded inspection limit.")

    def resolve_tag(self, repository, tag):
        ref = self.request(f"repos/{repository}/git/ref/tags/{quote(tag, safe='')}")["object"]
        for _ in range(8):
            if ref["type"] == "commit" and SHA.fullmatch(ref["sha"]):
                return ref["sha"]
            if ref["type"] != "tag" or not SHA.fullmatch(ref["sha"]):
                break
            ref = self.request(f"repos/{repository}/git/tags/{ref['sha']}")["object"]
        raise DeliveryError("Release tag did not resolve to a bounded commit object.")

    def find_release(self, tag):
        matches = [release for release in self.releases(OWN_REPOSITORY) if release.get("tag_name") == tag]
        if len(matches) > 1:
            raise DeliveryError("Multiple releases share the requested DeskCue tag.")
        return matches[0] if matches else None

    def create_release(self, metadata):
        return self.request(f"repos/{OWN_REPOSITORY}/releases", "POST",
                            {"tag_name": "v" + metadata["version"], "target_commitish": metadata["sourceCommit"],
                             "name": "DeskCue " + metadata["version"], "body": release_body(metadata),
                             "draft": True, "prerelease": False})

    def upload_asset(self, release_id, path):
        if type(release_id) is not int or release_id < 1:
            raise DeliveryError("Invalid GitHub release ID.")
        return self.request(f"https://uploads.github.com/repos/{OWN_REPOSITORY}/releases/{release_id}/assets?name={quote(path.name, safe='')}",
                            "POST", path.read_bytes())

    def download_asset(self, asset_id, path):
        if type(asset_id) is not int or asset_id < 1:
            raise DeliveryError("Invalid GitHub asset ID.")
        path.write_bytes(self.request(f"repos/{OWN_REPOSITORY}/releases/assets/{asset_id}", binary=True))

    def delete_incomplete_asset(self, asset_id):
        if type(asset_id) is not int or asset_id < 1:
            raise DeliveryError("Invalid incomplete GitHub asset ID.")
        return self.request(f"repos/{OWN_REPOSITORY}/releases/assets/{asset_id}", "DELETE")

    def asset_sha256(self, asset):
        if (not isinstance(asset, dict) or asset.get("state") != "uploaded" or
                type(asset.get("size")) is not int or asset["size"] < 1):
            raise DeliveryError("Release asset is not a completed nonempty upload.")
        identifier = asset.get("id")
        if type(identifier) is not int or identifier < 1:
            raise DeliveryError("Invalid GitHub asset ID.")
        digest = asset.get("digest", "")
        if isinstance(digest, str) and digest.startswith("sha256:") and HASH.fullmatch(digest[7:]):
            return digest[7:]
        if digest not in (None, ""):
            raise DeliveryError("Release asset SHA256 descriptor is malformed.")
        return hashlib.sha256(self.request(f"repos/{OWN_REPOSITORY}/releases/assets/{identifier}", binary=True)).hexdigest()

    def publish_release(self, release_id):
        return self.request(f"repos/{OWN_REPOSITORY}/releases/{int(release_id)}", "PATCH",
                            {"draft": False, "prerelease": False, "make_latest": "true"})


class SafeGitHubRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlsplit(newurl)
        allowed = {"api.github.com", "uploads.github.com", "release-assets.githubusercontent.com",
                   "objects.githubusercontent.com", "github-releases.githubusercontent.com"}
        if parsed.scheme != "https" or parsed.hostname not in allowed or parsed.username or parsed.password:
            raise DeliveryError("GitHub download redirected outside its allowed hosts.")
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected and parsed.hostname not in {"api.github.com", "uploads.github.com"}:
            redirected.remove_header("Authorization")
        return redirected


def stable_releases(releases, repository, components):
    valid = []
    for release in releases:
        if release.get("draft") or release.get("prerelease"):
            continue
        tag = release.get("tag_name", "")
        try:
            parts = version_parts(tag.removeprefix("v"), components)
        except DeliveryError:
            continue
        if tag != "v" + ".".join(map(str, parts)):
            continue
        if release.get("html_url") != f"https://github.com/{repository}/releases/tag/{tag}":
            raise DeliveryError("Release URL belongs to a foreign repository.")
        valid.append((parts, release))
    return [release for _, release in sorted(valid, key=lambda item: item[0], reverse=True)]


def release_body(metadata):
    public = {key: metadata[key] for key in PROVENANCE_KEYS if key in metadata}
    public["version"] = metadata.get("version", metadata.get("productVersion"))
    return (f"DeskCue {public['version']}\n\n"
            f"Built from {public['upstreamRepository']} {public['upstreamRef']} "
            f"({public['upstreamCommit']}); branding revision {public['brandingRevision']}.\n"
            "Install the package for your Windows architecture. GPL-3.0-only; upstream attribution is preserved.\n\n"
            "<!-- deskcue-provenance: " + json.dumps(public, sort_keys=True, separators=(",", ":")) + " -->\n")


def release_provenance(release):
    match = re.search(r"<!-- deskcue-provenance: (\{[^\r\n]*\}) -->", release.get("body", ""))
    if not match:
        raise DeliveryError("Published DeskCue release has no source provenance marker.")
    try:
        metadata = json.loads(match.group(1))
        validate_identity(metadata)
        if not SHA.fullmatch(metadata.get("sourceCommit", "")) or release["tag_name"] != "v" + metadata["version"]:
            raise DeliveryError("Release source/tag provenance disagrees.")
        return metadata
    except (ValueError, KeyError) as exc:
        raise DeliveryError("Malformed published release provenance.") from exc


def validate_release_identity(release, version):
    if not isinstance(release, dict):
        raise DeliveryError("Release API response is missing or malformed.")
    identifier = release.get("id")
    if (type(identifier) is not int or identifier < 1 or release.get("tag_name") != "v" + version or
            release.get("url") != f"https://api.github.com/repos/{OWN_REPOSITORY}/releases/{identifier}" or
            release.get("prerelease")):
        raise DeliveryError("Release API identity/tag is outside the authorized stable fork release.")
    # GitHub gives drafts an untagged-... HTML URL even when tag_name exists.
    # Only the authenticated API repository/id/tag and provenance identify a draft.
    if not release.get("draft") and release.get("html_url") != f"https://github.com/{OWN_REPOSITORY}/releases/tag/v{version}":
        raise DeliveryError("Published release URL is not the fork's canonical version URL.")


def archive_name(version):
    version_parts(version, 4)
    return f"DeskCue_Delivery_{version}.zip"


def incomplete_first_archive(release, version):
    assets = release.get("assets", [])
    return (bool(release.get("draft")) and len(assets) == 1 and
            assets[0].get("name") == archive_name(version) and assets[0].get("state") == "starter" and
            assets[0].get("size") == 0 and not assets[0].get("digest"))


def draft_resume_plan(plan, releases, api):
    drafts = [release for release in releases if release.get("draft") and release.get("tag_name") == "v" + plan["version"]]
    if len(drafts) > 1:
        raise DeliveryError("Multiple pending drafts share one DeskCue version.")
    if not drafts:
        return plan
    draft = drafts[0]
    validate_release_identity(draft, plan["version"])
    provenance = release_provenance(draft)
    if (plan["mode"] != "head" or provenance["sourceCommit"] != plan["baseCommit"] or
            any(provenance.get(key) != plan.get(key) for key in PROVENANCE_KEYS if key != "sourceCommit")):
        raise DeliveryError("Pending draft does not match the current reviewed source; refusing reconstruction.")
    assets = draft.get("assets", [])
    if not assets or incomplete_first_archive(draft, plan["version"]):
        return {**plan, "reason": "retry-before-completed-freeze"}
    archives = [asset for asset in assets if asset.get("name") == archive_name(plan["version"])]
    if len(archives) != 1 or archives[0].get("state") != "uploaded" or archives[0].get("size", 0) < 1:
        raise DeliveryError("Pending draft has completed assets without one valid frozen delivery archive.")
    asset = archives[0]
    digest = api.asset_sha256(asset)
    if type(asset.get("id")) is not int or asset["id"] < 1 or not HASH.fullmatch(digest):
        raise DeliveryError("Frozen delivery archive has invalid ID/SHA256.")
    return {**plan, "mode": "resume", "rebuild": False, "reason": "resume-frozen-delivery",
            "sourceCommit": provenance["sourceCommit"], "draftReleaseId": draft["id"],
            "archiveAssetId": asset["id"], "archiveSha256": digest, "archiveName": asset["name"]}


def detect(root, api):
    root = clean_repository(root)
    config = head_config(root)
    base = git_text(root, "rev-parse", "HEAD")
    upstreams = stable_releases(api.releases(UPSTREAM_REPOSITORY), UPSTREAM_REPOSITORY, 3)
    if not upstreams:
        return {"schemaVersion": 1, "build": False, "reason": "no-stable-upstream"}
    upstream = upstreams[0]
    own_all = api.releases(OWN_REPOSITORY)
    own = stable_releases(own_all, OWN_REPOSITORY, 4)
    plan = {"schemaVersion": 1, "build": True, "rebuild": True, "mode": "head", "baseCommit": base,
            "version": config["productVersion"], **{key: config[key] for key in PROVENANCE_KEYS if key in config}}
    if not own:
        plan["reason"] = "initial-reviewed-head"
        return draft_resume_plan(plan, own_all, api)
    latest = release_provenance(own[0])
    if version_parts(latest["version"], 4) > version_parts(config["productVersion"], 4):
        raise DeliveryError("Published version is newer than the reviewed source configuration.")
    if version_parts(config["productVersion"], 4) > version_parts(latest["version"], 4):
        plan["reason"] = "pending-delivery"
        return draft_resume_plan(plan, own_all, api)
    if (latest["upstreamCommit"], latest["brandingRevision"]) != (config["upstreamCommit"], config["brandingRevision"]):
        raise DeliveryError("Current version collides with different published source provenance.")
    upstream_version = upstream["tag_name"][1:]
    if version_parts(upstream_version, 3) < version_parts(config["upstreamVersion"], 3):
        raise DeliveryError("Upstream stable release history regressed.")
    resolved = api.resolve_tag(UPSTREAM_REPOSITORY, upstream["tag_name"])
    if not SHA.fullmatch(str(resolved)):
        raise DeliveryError("Upstream tag did not resolve to a full commit SHA.")
    if upstream_version == config["upstreamVersion"]:
        # The initial reviewed source is one documentation-only commit after v1.5.9.
        # Check the originally recorded release tag separately when it is available.
        original_tag = config.get("upstreamReleaseCommit", config["upstreamCommit"])
        if resolved != original_tag:
            raise DeliveryError("Previously adopted upstream stable tag moved.")
        return {**plan, "build": False, "reason": "already-published"}
    plan.update(mode="upstream", reason="new-stable-upstream", upstreamRef=upstream["tag_name"],
                upstreamVersion=upstream_version, upstreamCommit=resolved,
                version=f"{upstream_version}.{config['brandingRevision']}")
    return draft_resume_plan(plan, own_all, api)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise DeliveryError("Artifact path is not a safe relative path.")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"..", "."} for part in path.parts) or str(path) != value:
        raise DeliveryError("Artifact path escapes its declared directory.")
    return path


def is_link(path):
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def new_path(path, root):
    candidate = Path(path).absolute()
    if any(is_link(parent) for parent in (candidate, *candidate.parents)):
        raise DeliveryError("Staging paths cannot traverse symbolic links.")
    candidate = candidate.resolve()
    if candidate == root or root.is_relative_to(candidate) or candidate.parent == candidate:
        raise DeliveryError("Staging cannot replace the repository or an ancestor/root.")
    if candidate.exists():
        raise DeliveryError("Staging destination already exists; select a new directory.")
    return candidate


def tracked_overlay(root, ref):
    prefixes = ("deskcue/", "tools/", "docs/superpowers/")
    fork_policies = {"SECURITY.md", "CODE_OF_CONDUCT.md", "CONTRIBUTING.md", "SUPPORT.md",
                     ".github/PULL_REQUEST_TEMPLATE.md", "docs/code-signing.md",
                     ".github/workflows/distribution-audit.yml"}
    single = {".gitignore", "AGENTS.md", "README.md", "README.zh-CN.md", "UPSTREAM.md", "docs/HANDOFF.md",
              ".github/workflows/deskcue-upstream.yml"} | fork_policies
    entries = []
    for entry in git(root, "ls-tree", "-rz", ref).split(b"\0"):
        if not entry:
            continue
        descriptor, raw_path = entry.split(b"\t", 1)
        path = raw_path.decode("utf-8")
        if path == "deskcue/provenance.json" or not (path.startswith(prefixes) or path in single):
            continue
        safe_relative(path)
        mode, kind, blob = descriptor.decode("ascii").split()
        if mode not in {"100644", "100755"} or kind != "blob":
            raise DeliveryError("Management overlay contains a symlink or non-file entry.")
        entries.append((path, blob))
    if not fork_policies.issubset(path for path, _ in entries):
        raise DeliveryError("A required tracked fork policy is missing; upstream policy defaults cannot be released.")
    return entries


def patch_inventory(root, ref, config):
    validate_identity(config)
    declared = config["forkPatches"]
    found = {}
    for entry in git(root, "ls-tree", "-rz", ref, "--", "deskcue/patches/").split(b"\0"):
        if not entry:
            continue
        descriptor, raw_path = entry.split(b"\t", 1)
        path = raw_path.decode("utf-8")
        mode, kind, blob = descriptor.decode("ascii").split()
        name = path.removeprefix("deskcue/patches/")
        if name not in declared or mode not in {"100644", "100755"} or kind != "blob":
            raise DeliveryError("Tracked fork patch inventory contains an undeclared/non-file entry.")
        found[name] = hashlib.sha256(git(root, "cat-file", "blob", blob)).hexdigest()
    if set(found) != set(declared):
        raise DeliveryError("A required tracked fork patch is missing; upstream defaults cannot be released.")
    return found


def bundle_candidate(root, commit, destination):
    # A separate object database gives the bundle one fixed ref and no prerequisites.
    with tempfile.TemporaryDirectory(prefix=".bundle-", dir=destination.parent) as temporary:
        bare = Path(temporary)
        git(bare, "init", "--bare")
        git(bare, "fetch", "--no-tags", str(root), f"{commit}:{CANDIDATE_REF}")
        git(bare, "-c", "pack.threads=1", "-c", "pack.window=0", "bundle", "create", str(destination), CANDIDATE_REF)


def prepare(root, plan, destination, output_dir, *, upstream_url=None, brand_runner=None, api=None):
    root = clean_repository(root)
    if not plan.get("build") or plan.get("mode") not in {"head", "upstream", "resume"}:
        raise DeliveryError("Only a pending reviewed source plan can be prepared.")
    validate_identity(plan)
    base = git_text(root, "rev-parse", "HEAD")
    if base != plan.get("baseCommit"):
        raise DeliveryError("Reviewed source HEAD changed since candidate detection.")
    if plan["mode"] == "resume":
        return resume_candidate(root, plan, output_dir, api or GitHubApi())
    destination = new_path(destination, root)
    output_dir = new_path(output_dir, root)
    if destination == output_dir or output_dir.is_relative_to(destination):
        raise DeliveryError("Candidate output cannot be inside its mutable source checkout.")
    config = head_config(root)
    patch_hashes = patch_inventory(root, base, config)
    if plan["mode"] == "head" and any(plan.get(key) != config.get(key) for key in PROVENANCE_KEYS if key in config):
        raise DeliveryError("Current HEAD does not match the pending source plan.")
    output_dir.mkdir(parents=True)
    created_worktree = False
    try:
        source = base
        if plan["mode"] == "upstream":
            tag_ref = "refs/deskcue/upstream/" + plan["upstreamCommit"]
            git(root, "fetch", "--no-tags", upstream_url or f"https://github.com/{UPSTREAM_REPOSITORY}.git",
                f"refs/tags/{plan['upstreamRef']}:{tag_ref}")
            source = git_text(root, "rev-parse", tag_ref + "^{commit}")
            if source != plan["upstreamCommit"]:
                raise DeliveryError("Fetched release tag disagrees with the detected commit.")
        git(root, "-c", "core.autocrlf=false", "-c", "core.eol=lf",
            "worktree", "add", "--detach", str(destination), source)
        created_worktree = True
        if plan["mode"] == "upstream":
            config.update({key: plan[key] for key in PROVENANCE_KEYS if key in plan and key != "sourceCommit"})
            config.pop("version", None)
            config["productVersion"] = plan["version"]
            config["upstreamReleaseCommit"] = source
            recipe = output_dir / "brand.py"
            recipe.write_bytes(git(root, "show", f"{base}:deskcue/brand.py"))
            configuration = output_dir / "config.json"
            configuration.write_bytes(json_bytes(config))
            command = [sys.executable, str(recipe), "--root", str(destination), "--config", str(configuration)]
            if brand_runner:
                brand_runner(command)
            else:
                result = subprocess.run(command, capture_output=True)
                if result.returncode:
                    raise DeliveryError(f"Branding recipe failed (exit {result.returncode}); candidate was not promoted.")
            for path, blob in tracked_overlay(root, base):
                target = destination / path
                if any(is_link(parent) for parent in (target, *target.parents)):
                    raise DeliveryError("Overlay target traverses a symlink.")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(git(root, "cat-file", "blob", blob))
            (destination / "deskcue/config.json").write_bytes(json_bytes(config))
            for name in config["forkPatches"]:
                patch = destination / "deskcue/patches" / name
                if sha256(patch) != patch_hashes[name]:
                    raise DeliveryError("Required fork patch changed during candidate replay.")
                git(destination, "apply", "--check", str(patch))
                git(destination, "apply", str(patch))
            git(destination, "-c", "core.autocrlf=false", "add", "--all")
            tree = git_text(destination, "write-tree")
            seconds = max(int(git_text(root, "show", "-s", "--format=%ct", base)),
                          int(git_text(root, "show", "-s", "--format=%ct", source))) + 1
            environment = {**os.environ, "GIT_AUTHOR_NAME": "DeskCue Source Builder",
                           "GIT_AUTHOR_EMAIL": "deskcue-builder@users.noreply.github.com",
                           "GIT_COMMITTER_NAME": "DeskCue Source Builder",
                           "GIT_COMMITTER_EMAIL": "deskcue-builder@users.noreply.github.com",
                           "GIT_AUTHOR_DATE": f"@{seconds} +0000", "GIT_COMMITTER_DATE": f"@{seconds} +0000"}
            message = f"Adopt {UPSTREAM_REPOSITORY} {plan['upstreamRef']} as DeskCue {plan['version']}\n"
            source = git_text(destination, "commit-tree", tree, "-p", base, "-p", source,
                              data=message.encode("utf-8"), env=environment)
            git(destination, "checkout", "--detach", source)
        provenance = destination / "deskcue/provenance.json"
        provenance_value = read_json(provenance)
        validate_identity(provenance_value)
        if any(provenance_value.get(key) != config.get(key) for key in PROVENANCE_KEYS if key in config):
            raise DeliveryError("Branding provenance disagrees with the chosen source configuration.")
        if read_json(destination / "deskcue/config.json") != config:
            raise DeliveryError("Candidate configuration changed during preparation.")
        if git_text(root, "rev-parse", "HEAD") != base:
            raise DeliveryError("Source HEAD changed while preparing the candidate.")
        clean_repository(root)
        bundle = output_dir / "candidate.bundle"
        bundle_candidate(root, source, bundle)
        metadata = {"schemaVersion": 1, "mode": plan["mode"], "baseCommit": base,
                    "sourceCommit": source, "sourceTree": git_text(destination, "rev-parse", "HEAD^{tree}"),
                    "version": plan["version"], **{key: config[key] for key in PROVENANCE_KEYS if key in config},
                    "provenanceSha256": sha256(provenance),
                    "forkPatchSha256": patch_hashes,
                    "bundle": {"fileName": "candidate.bundle", "ref": CANDIDATE_REF, "sha256": sha256(bundle)}}
        verify_candidate(metadata, bundle)
        (output_dir / "candidate.json").write_bytes(json_bytes(metadata))
        (output_dir / "provenance.json").write_bytes(provenance.read_bytes())
        return metadata
    except Exception:
        if created_worktree:
            git(root, "worktree", "remove", "--force", str(destination))
        raise


def verify_candidate(metadata, bundle):
    validate_identity(metadata)
    if metadata.get("schemaVersion") != 1 or metadata.get("mode") not in {"head", "upstream"}:
        raise DeliveryError("Unknown source candidate schema/mode.")
    if any(not SHA.fullmatch(str(metadata.get(key, ""))) for key in ("sourceCommit", "sourceTree", "baseCommit")):
        raise DeliveryError("Candidate commit/tree/base must be full Git object IDs.")
    bundle = Path(bundle).resolve()
    declared = metadata.get("bundle", {})
    if declared.get("fileName") != "candidate.bundle" or declared.get("ref") != CANDIDATE_REF or sha256(bundle) != declared.get("sha256"):
        raise DeliveryError("Source bundle hash/ref/name mismatch.")
    with tempfile.TemporaryDirectory(prefix=".verify-", dir=bundle.parent) as temporary:
        bare = Path(temporary)
        git(bare, "init", "--bare")
        git(bare, "bundle", "verify", str(bundle))
        heads = git_text(bare, "bundle", "list-heads", str(bundle)).splitlines()
        if heads != [f"{metadata['sourceCommit']} {CANDIDATE_REF}"]:
            raise DeliveryError("Source bundle does not contain exactly the declared candidate ref.")
        git(bare, "fetch", "--no-tags", str(bundle), f"{CANDIDATE_REF}:{CANDIDATE_REF}")
        ref = metadata["sourceCommit"]
        if git_text(bare, "rev-parse", ref + "^{tree}") != metadata["sourceTree"]:
            raise DeliveryError("Source candidate tree mismatch.")
        git(bare, "merge-base", "--is-ancestor", metadata["baseCommit"], ref)
        if metadata["mode"] == "upstream":
            if git_text(bare, "show", "-s", "--format=%P", ref).split() != [metadata["baseCommit"], metadata["upstreamCommit"]]:
                raise DeliveryError("Reconstructed candidate must retain fork/upstream parents.")
        config = json.loads(git(bare, "show", f"{ref}:deskcue/config.json"))
        if patch_inventory(bare, ref, config) != metadata.get("forkPatchSha256"):
            raise DeliveryError("Candidate required fork patch inventory/SHA256 mismatch.")
        provenance_bytes = git(bare, "show", f"{ref}:deskcue/provenance.json")
        provenance = json.loads(provenance_bytes)
        if hashlib.sha256(provenance_bytes).hexdigest() != metadata.get("provenanceSha256"):
            raise DeliveryError("Source provenance hash mismatch.")
        for record in (config, provenance):
            validate_identity(record)
            for key in PROVENANCE_KEYS:
                expected = metadata[key]
                actual = record.get("productVersion") if key == "version" else record.get(key)
                if key != "sourceCommit" and actual != expected:
                    raise DeliveryError("Candidate source configuration/provenance mismatch.")
        recipe_bytes = git(bare, "show", f"{ref}:deskcue/brand.py")
        config_bytes = git(bare, "show", f"{ref}:deskcue/config.json")
        if (provenance.get("recipeSha256") != hashlib.sha256(recipe_bytes).hexdigest() or
                provenance.get("configSha256") != hashlib.sha256(config_bytes).hexdigest() or
                not HASH.fullmatch(provenance.get("sourceTreeSha256", ""))):
            raise DeliveryError("Branding recipe/config/source hashes are not consistent with candidate source.")
    return metadata


def verify_artifacts(metadata, artifacts):
    root = Path(artifacts).resolve()
    result = {}
    for platform, rid in (("x64", "win-x64"), ("ARM64", "win-arm64")):
        folder = root / rid
        if any(is_link(path) for path in (folder, *folder.parents)) or not folder.is_dir() or is_link(folder / "receipt.json"):
            raise DeliveryError("Both architecture artifact directories must be regular directories.")
        receipt = read_json(folder / "receipt.json")
        expected = {"schemaVersion": 1, "status": "passed", "platform": platform, "runtimeIdentifier": rid,
                    "sourceCommit": metadata["sourceCommit"], "version": metadata["version"],
                    "upstreamRepository": metadata["upstreamRepository"], "upstreamCommit": metadata["upstreamCommit"],
                    "brandingRevision": metadata["brandingRevision"]}
        if any(receipt.get(key) != value for key, value in expected.items()):
            raise DeliveryError("Architecture receipt does not match the verified source candidate.")
        tests = receipt.get("tests", {})
        if (any(type(tests.get(key)) is not int for key in ("total", "passed", "failed", "skipped")) or
                tests["total"] < 1 or tests["total"] != tests["passed"] or tests["failed"] != 0 or tests["skipped"] != 0):
            raise DeliveryError("Receipt does not prove a complete successful test run.")
        if not HASH.fullmatch(str(receipt.get("retailSummarySha256", "")).lower()):
            raise DeliveryError("Retail publish evidence has no SHA256.")
        installer = receipt.get("installer", {})
        name = f"DeskCue_Setup_{metadata['version']}_{platform.lower()}.exe"
        relative = safe_relative(installer.get("path"))
        if str(relative) != name or installer.get("fileName") != name:
            raise DeliveryError("Installer must use the fork's versioned architecture name.")
        path = folder / relative
        checksum = folder / (name + ".sha256")
        if any(is_link(value) or not value.is_file() for value in (path, checksum)):
            raise DeliveryError("Installer/checksum must be regular files.")
        expected_hash = str(installer.get("sha256", "")).lower()
        if not HASH.fullmatch(expected_hash) or sha256(path) != expected_hash or path.stat().st_size != installer.get("bytes"):
            raise DeliveryError("Installer bytes/hash disagree with the successful build receipt.")
        if checksum.read_text(encoding="utf-8-sig").strip().lower() != f"{expected_hash}  {name}".lower():
            raise DeliveryError("Installer checksum sidecar disagrees with the package.")
        with path.open("rb") as stream:
            if stream.read(2) != b"MZ":
                raise DeliveryError("Installer is not a Windows executable.")
        result[platform.lower()] = {"path": path, "receipt": receipt, "fileName": name,
                                    "sha256": expected_hash, "size": path.stat().st_size,
                                    "runtimeIdentifier": rid}
    return result


def render_release(metadata, bundle, artifacts, release_dir):
    verify_candidate(metadata, bundle)
    packages = verify_artifacts(metadata, artifacts)
    target = Path(release_dir).absolute()
    if target.exists() or any(is_link(parent) for parent in (target, *target.parents)):
        raise DeliveryError("Release assembly requires a new path without symlinks.")
    tag = "v" + metadata["version"]
    release_url = f"https://github.com/{OWN_REPOSITORY}/releases/tag/{tag}"
    download_base = f"https://github.com/{OWN_REPOSITORY}/releases/download/{tag}/"
    source_name = f"DeskCue_Source_{metadata['version']}.bundle"
    architectures = {key: {"fileName": package["fileName"], "downloadUrl": download_base + package["fileName"],
                           "sha256": package["sha256"], "size": package["size"],
                           "runtimeIdentifier": package["runtimeIdentifier"]} for key, package in packages.items()}
    manifest = {"schemaVersion": 1, "channel": "stable", "version": metadata["version"], "mandatory": False,
                "downloadUrl": architectures["x64"]["downloadUrl"], "sha256": architectures["x64"]["sha256"],
                "size": architectures["x64"]["size"], "arm64DownloadUrl": architectures["arm64"]["downloadUrl"],
                "arm64Sha256": architectures["arm64"]["sha256"], "arm64Size": architectures["arm64"]["size"],
                "manualDownloadUrl": release_url, "releaseNotesUrl": release_url, "architectures": architectures,
                "source": {"commit": metadata["sourceCommit"], "tree": metadata["sourceTree"],
                           "upstreamRepository": metadata["upstreamRepository"], "upstreamRef": metadata["upstreamRef"],
                           "upstreamCommit": metadata["upstreamCommit"], "brandingRevision": metadata["brandingRevision"],
                           "provenanceSha256": metadata["provenanceSha256"], "forkPatchSha256": metadata["forkPatchSha256"]},
                "sourceBundle": {"fileName": source_name, "downloadUrl": download_base + source_name, "sha256": sha256(bundle)},
                "summary": {"zh-CN": "DeskCue 稳定版，基于上游源码构建，包含离线运行依赖。",
                            "en-US": "DeskCue stable release, rebuilt from upstream source with offline runtime dependencies."}}
    target.mkdir(parents=True)
    for package in packages.values():
        shutil.copyfile(package["path"], target / package["fileName"])
        if sha256(target / package["fileName"]) != package["sha256"]:
            raise DeliveryError("Installer changed while assembling release assets.")
        (target / (package["fileName"] + ".sha256")).write_bytes(
            f"{package['sha256']}  {package['fileName']}\n".encode("ascii"))
    shutil.copyfile(bundle, target / source_name)
    if sha256(target / source_name) != metadata["bundle"]["sha256"]:
        raise DeliveryError("Source bundle changed while assembling release assets.")
    (target / "stable.json").write_bytes(json_bytes(manifest))
    (target / "provenance.json").write_bytes(json_bytes({key: metadata[key] for key in (*PROVENANCE_KEYS, "sourceTree", "provenanceSha256", "forkPatchSha256")}))
    checksums = "".join(f"{sha256(path)}  {path.name}\n" for path in sorted(target.iterdir()))
    (target / "SHA256SUMS.txt").write_bytes(checksums.encode("ascii"))
    return {path.name: path for path in target.iterdir()}


def remote_refs(root, remote):
    refs = {}
    for line in git_text(root, "ls-remote", remote, "refs/heads/main", "refs/tags/v*", "refs/tags/v*^{}").splitlines():
        sha, ref = line.split("\t", 1)
        refs[ref] = sha
    return refs


def push_candidate(root, remote, metadata, bundle, *, before_push=None):
    tag = "refs/tags/v" + metadata["version"]
    candidate = metadata["sourceCommit"]
    refs = remote_refs(root, remote)
    current = refs.get("refs/heads/main")
    if current not in {metadata["baseCommit"], candidate}:
        raise DeliveryError("Remote main advanced since candidate review; no source or release was overwritten.")
    existing_tag = refs.get(tag + "^{}", refs.get(tag))
    if existing_tag and existing_tag != candidate:
        raise DeliveryError("Existing release tag points to different source; refusing replacement.")
    git(root, "fetch", "--no-tags", str(Path(bundle).resolve()), CANDIDATE_REF)
    git(root, "merge-base", "--is-ancestor", current, candidate)
    with tempfile.TemporaryDirectory(prefix=".push-guard-", dir=Path(bundle).resolve().parent) as temporary:
        hooks = Path(temporary)
        expected = {"refs/heads/main": current, tag: refs.get(tag, "0" * 40)}
        guard = hooks / "guard.py"
        guard.write_bytes(("import sys\nexpected=" + repr(expected) + "\ncandidate=" + repr(candidate) +
                           "\nfor line in sys.stdin:\n p=line.split()\n if len(p)!=4 or p[2] not in expected or p[3]!=expected[p[2]] or p[1]!=candidate:\n  sys.exit('Remote refs changed during promotion; fast-forward aborted.')\n").encode("utf-8"))
        executable = shlex.quote(sys.executable.replace("\\", "/"))
        script = shlex.quote(str(guard).replace("\\", "/"))
        hook = hooks / "pre-push"
        hook.write_bytes(f"#!/bin/sh\nexec {executable} {script}\n".encode("utf-8"))
        hook.chmod(0o755)
        if before_push:
            before_push()
        # No force option. The hook checks advertised old OIDs; atomic receive checks
        # the same OIDs under lock, closing the inspection-to-push race.
        git(root, "-c", f"core.hooksPath={hooks}", "push", "--atomic", remote,
            f"{candidate}:refs/heads/main", f"{candidate}:{tag}")
    confirmed = remote_refs(root, remote)
    if confirmed.get("refs/heads/main") != candidate or confirmed.get(tag + "^{}", confirmed.get(tag)) != candidate:
        raise DeliveryError("Remote source/tag readback does not match the verified candidate.")


def release_asset_names(version):
    names = {"stable.json", "provenance.json", "SHA256SUMS.txt", f"DeskCue_Source_{version}.bundle"}
    for architecture in ("x64", "arm64"):
        name = f"DeskCue_Setup_{version}_{architecture}.exe"
        names.update({name, name + ".sha256"})
    return names


def freeze_delivery(metadata, bundle, artifacts, files, destination):
    """Freeze the tested source and both exact installers BEFORE uploading any installer."""
    if set(files) != release_asset_names(metadata["version"]):
        raise DeliveryError("Frozen delivery must contain the complete expected public asset set.")
    inputs = {"candidate.bundle": files[f"DeskCue_Source_{metadata['version']}.bundle"]}
    for architecture in ("x64", "arm64"):
        rid = "win-" + architecture
        name = f"DeskCue_Setup_{metadata['version']}_{architecture}.exe"
        inputs[f"packages/{rid}/receipt.json"] = Path(artifacts) / rid / "receipt.json"
        inputs[f"packages/{rid}/{name}"] = files[name]
        inputs[f"packages/{rid}/{name}.sha256"] = files[name + ".sha256"]
    metadata_bytes = json_bytes(metadata)
    inventory = {name: {"sha256": sha256(path), "bytes": path.stat().st_size} for name, path in inputs.items()}
    inventory["candidate.json"] = {"sha256": hashlib.sha256(metadata_bytes).hexdigest(), "bytes": len(metadata_bytes)}
    frozen = {"schemaVersion": 1, "version": metadata["version"], "sourceCommit": metadata["sourceCommit"],
              "files": inventory, "publicAssetSha256": {name: sha256(path) for name, path in sorted(files.items())}}
    destination = Path(destination)
    if destination.exists() or any(is_link(path) for path in (destination, *destination.parents)):
        raise DeliveryError("Frozen archive destination must be new and contained.")
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        for name in sorted([*inputs, "candidate.json", "frozen.json"]):
            info = zipfile.ZipInfo(name, date_time=(2000, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o100644 << 16
            with archive.open(info, "w", force_zip64=True) as stream:
                if name == "candidate.json":
                    stream.write(metadata_bytes)
                elif name == "frozen.json":
                    stream.write(json_bytes(frozen))
                else:
                    with inputs[name].open("rb") as source:
                        shutil.copyfileobj(source, stream)
    if destination.stat().st_size > 2 * 1024 ** 3:
        raise DeliveryError("Frozen archive exceeds GitHub's release asset size limit.")
    return destination


def restore_frozen_delivery(archive_path, destination):
    archive_path, destination = Path(archive_path), Path(destination).absolute()
    if (is_link(archive_path) or not archive_path.is_file() or archive_path.stat().st_size > 2 * 1024 ** 3 or
            destination.exists() or any(is_link(path) for path in (destination, *destination.parents))):
        raise DeliveryError("Frozen delivery needs a regular bounded archive and a new extraction directory.")
    try:
        with zipfile.ZipFile(archive_path) as archive:
            entries = archive.infolist()
            names = [entry.filename for entry in entries]
            if (len(entries) > 16 or len({name.casefold() for name in names}) != len(names) or
                    "frozen.json" not in names or sum(entry.file_size for entry in entries) > 2 * 1024 ** 3):
                raise DeliveryError("Frozen archive has an invalid entry count/size/inventory.")
            for entry in entries:
                safe_relative(entry.filename)
                mode = entry.external_attr >> 16
                if (entry.is_dir() or entry.flag_bits & 1 or entry.compress_type != zipfile.ZIP_STORED or
                        (stat.S_IFMT(mode) not in {0, stat.S_IFREG})):
                    raise DeliveryError("Frozen archive contains a link, encrypted or unsupported entry.")
            if archive.getinfo("frozen.json").file_size > 1024 * 1024:
                raise DeliveryError("Frozen archive metadata exceeds its bound.")
            frozen = json.loads(archive.read("frozen.json"))
            if not isinstance(frozen, dict):
                raise DeliveryError("Frozen archive metadata must be a JSON object.")
            inventory = frozen.get("files", {})
            if frozen.get("schemaVersion") != 1 or not isinstance(inventory, dict) or set(names) != set(inventory) | {"frozen.json"}:
                raise DeliveryError("Frozen archive entry inventory mismatch.")
            for name, record in inventory.items():
                if (not isinstance(record, dict) or not HASH.fullmatch(str(record.get("sha256", ""))) or
                        type(record.get("bytes")) is not int or record["bytes"] != archive.getinfo(name).file_size):
                    raise DeliveryError("Frozen archive entry SHA256/size declaration is invalid.")
            if archive.getinfo("candidate.json").file_size > 1024 * 1024:
                raise DeliveryError("Frozen candidate metadata exceeds its bound.")
            metadata = json.loads(archive.read("candidate.json"))
            validate_identity(metadata)
            expected_paths = {"candidate.json", "candidate.bundle"}
            for architecture in ("x64", "arm64"):
                name = f"DeskCue_Setup_{metadata['version']}_{architecture}.exe"
                expected_paths.update({f"packages/win-{architecture}/receipt.json",
                                       f"packages/win-{architecture}/{name}", f"packages/win-{architecture}/{name}.sha256"})
            public = frozen.get("publicAssetSha256", {})
            if (not isinstance(public, dict) or set(inventory) != expected_paths or frozen.get("version") != metadata["version"] or
                    frozen.get("sourceCommit") != metadata["sourceCommit"] or
                    set(public) != release_asset_names(metadata["version"]) or
                    any(not HASH.fullmatch(str(digest)) for digest in public.values())):
                raise DeliveryError("Frozen delivery source/architecture/public asset inventory mismatch.")
            destination.mkdir(parents=True)
            for name, record in inventory.items():
                target = destination / safe_relative(name)
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(name) as source, target.open("xb") as stream:
                    shutil.copyfileobj(source, stream)
                if sha256(target) != record["sha256"]:
                    raise DeliveryError("Frozen archive entry SHA256 mismatch.")
    except (zipfile.BadZipFile, KeyError, ValueError, TypeError) as exc:
        raise DeliveryError("Invalid frozen delivery archive.") from exc
    verify_candidate(metadata, destination / "candidate.bundle")
    verify_artifacts(metadata, destination / "packages")
    return {"metadata": metadata, "bundle": destination / "candidate.bundle", "artifacts": destination / "packages",
            "publicAssetSha256": public}


def resume_candidate(root, plan, output_dir, api):
    output_dir = new_path(output_dir, root)
    config = head_config(root)
    patch_inventory(root, plan["baseCommit"], config)
    release = api.find_release("v" + plan["version"])
    if not release or release.get("id") != plan.get("draftReleaseId"):
        raise DeliveryError("Pending release changed during frozen resume.")
    validate_release_identity(release, plan["version"])
    provenance = release_provenance(release)
    if any(provenance.get(key) != plan.get(key) for key in PROVENANCE_KEYS):
        raise DeliveryError("Pending release source provenance changed during frozen resume.")
    assets = [asset for asset in release.get("assets", []) if asset.get("id") == plan.get("archiveAssetId")]
    if (len(assets) != 1 or assets[0].get("name") != archive_name(plan["version"]) or
            api.asset_sha256(assets[0]) != plan.get("archiveSha256")):
        raise DeliveryError("Frozen archive identity/SHA256 changed during resume.")
    output_dir.mkdir(parents=True)
    archive = output_dir / "frozen-delivery.zip"
    api.download_asset(plan["archiveAssetId"], archive)
    if sha256(archive) != plan["archiveSha256"]:
        raise DeliveryError("Downloaded frozen delivery SHA256 mismatch.")
    restored = restore_frozen_delivery(archive, output_dir / "verified")
    metadata = restored["metadata"]
    if any(metadata.get(key) != plan.get(key) for key in PROVENANCE_KEYS):
        raise DeliveryError("Frozen delivery is not the detected source candidate.")
    if git_text(root, "rev-parse", "HEAD") != plan["baseCommit"]:
        raise DeliveryError("Reviewed source changed while downloading the frozen delivery.")
    clean_repository(root)
    shutil.copyfile(restored["bundle"], output_dir / "candidate.bundle")
    (output_dir / "candidate.json").write_bytes(json_bytes(metadata))
    return metadata


def promote(root, metadata, bundle, artifacts, release_dir, api, *, remote=None, before_push=None, frozen_archive=None):
    release_dir = Path(release_dir).absolute()
    if frozen_archive:
        restored = restore_frozen_delivery(frozen_archive, release_dir.with_name(release_dir.name + "-frozen-input"))
        if restored["metadata"] != metadata:
            raise DeliveryError("Resumed metadata does not equal the frozen original candidate.")
        bundle, artifacts = restored["bundle"], restored["artifacts"]
    files = render_release(metadata, bundle, artifacts, release_dir)
    if frozen_archive:
        if {name: sha256(path) for name, path in files.items()} != restored["publicAssetSha256"]:
            raise DeliveryError("Resumed public assets differ from the frozen delivery; overwrite is forbidden.")
        archive = release_dir / archive_name(metadata["version"])
        shutil.copyfile(frozen_archive, archive)
        if sha256(archive) != sha256(frozen_archive):
            raise DeliveryError("Frozen delivery archive changed while staging the original bytes.")
    else:
        archive = freeze_delivery(metadata, bundle, artifacts, files, release_dir / archive_name(metadata["version"]))
        restored = restore_frozen_delivery(archive, release_dir.with_name(release_dir.name + "-freeze-check"))
        if {name: sha256(path) for name, path in files.items()} != restored["publicAssetSha256"]:
            raise DeliveryError("Frozen delivery does not match the verified public assets.")
    # SHA256SUMS covers the ordinary release files. The archive's own GitHub digest
    # authenticates its transport; including its hash inside itself would be cyclic.
    files[archive.name] = archive
    root = Path(root).resolve()
    if remote is None:
        remote = git_text(root, "remote", "get-url", "origin")
        if remote not in {f"https://github.com/{OWN_REPOSITORY}", f"https://github.com/{OWN_REPOSITORY}.git",
                          f"git@github.com:{OWN_REPOSITORY}.git"}:
            raise DeliveryError("Release writes are restricted to the authorized DeskCue remote.")
        remote = "origin"
    release = api.find_release("v" + metadata["version"])
    if release:
        validate_release_identity(release, metadata["version"])
        existing = release_provenance(release)
        if any(existing.get(key) != metadata[key] for key in PROVENANCE_KEYS):
            raise DeliveryError("Existing release belongs to different source provenance.")
        if incomplete_first_archive(release, metadata["version"]):
            api.delete_incomplete_asset(release["assets"][0]["id"])
            release = api.find_release("v" + metadata["version"])
            validate_release_identity(release, metadata["version"])
            if release.get("assets"):
                raise DeliveryError("Incomplete first upload cleanup did not read back empty; no completed asset is replaced.")
        existing_assets = {asset["name"]: asset for asset in release.get("assets", [])}
        if len(existing_assets) != len(release.get("assets", [])) or set(existing_assets) - set(files):
            raise DeliveryError("Existing release contains duplicate or unexpected assets.")
        starters = {name: asset for name, asset in existing_assets.items()
                    if name != archive.name and asset.get("state") == "starter" and
                    type(asset.get("size")) is int and asset["size"] == 0 and asset.get("digest") in (None, "")}
        if starters:
            if (not release.get("draft") or archive.name not in existing_assets or
                    any(type(asset.get("id")) is not int or asset["id"] < 1 for asset in starters.values()) or
                    api.asset_sha256(existing_assets[archive.name]) != sha256(archive)):
                raise DeliveryError("Incomplete assets require a matching draft and its verified frozen original archive.")
        # Validate every completed/invalid descriptor before deleting any starter.
        # files came from the fully verified frozen inventory; unknown names were rejected above.
        for name, asset in existing_assets.items():
            if name in starters:
                continue
            if api.asset_sha256(asset) != sha256(files[name]):
                raise DeliveryError("Existing release asset has different bytes; replacement is forbidden.")
        if starters:
            completed = {name: asset["id"] for name, asset in existing_assets.items() if name not in starters}
            release_id = release["id"]
            for asset in starters.values():
                api.delete_incomplete_asset(asset["id"])
            release = api.find_release("v" + metadata["version"])
            validate_release_identity(release, metadata["version"])
            if (release["id"] != release_id or not release.get("draft") or
                    any(release_provenance(release).get(key) != metadata[key] for key in PROVENANCE_KEYS)):
                raise DeliveryError("Draft source changed during incomplete asset cleanup.")
            existing_assets = {asset["name"]: asset for asset in release.get("assets", [])}
            if len(existing_assets) != len(release.get("assets", [])) or set(existing_assets) != set(completed):
                raise DeliveryError("Incomplete asset cleanup did not preserve the exact completed asset set.")
            for name, identifier in completed.items():
                if existing_assets[name].get("id") != identifier or api.asset_sha256(existing_assets[name]) != sha256(files[name]):
                    raise DeliveryError("Completed asset changed during incomplete upload recovery.")
        if not release.get("draft") and set(existing_assets) != set(files):
            raise DeliveryError("Published release is missing assets; refusing to mutate it.")
    push_candidate(root, remote, metadata, bundle, before_push=before_push)
    if release is None:
        release = api.create_release(metadata)
    existing_assets = {asset["name"]: asset for asset in release.get("assets", [])}
    if archive.name not in existing_assets:
        api.upload_asset(release["id"], archive)
        readback = api.find_release("v" + metadata["version"])
        validate_release_identity(readback, metadata["version"])
        frozen_assets = [asset for asset in readback.get("assets", []) if asset.get("name") == archive.name]
        if len(frozen_assets) != 1 or api.asset_sha256(frozen_assets[0]) != sha256(archive):
            raise DeliveryError("First frozen archive upload was not confirmed; installer upload is blocked.")
    for name, path in sorted(files.items()):
        if name != archive.name and name not in existing_assets:
            api.upload_asset(release["id"], path)
    release = verified_remote_release(api, metadata, files)
    if release.get("draft"):
        release = api.publish_release(release["id"])
    release = verified_remote_release(api, metadata, files)
    if release.get("draft"):
        raise DeliveryError("Release publication readback is still a draft; retry is safe.")
    return {"status": "published", "version": metadata["version"], "sourceCommit": metadata["sourceCommit"],
            "url": release["html_url"], "assets": {name: sha256(path) for name, path in sorted(files.items())}}


def verified_remote_release(api, metadata, files):
    release = api.find_release("v" + metadata["version"])
    if not release:
        raise DeliveryError("Release readback is missing or has a foreign identity.")
    validate_release_identity(release, metadata["version"])
    provenance = release_provenance(release)
    if any(provenance.get(key) != metadata[key] for key in PROVENANCE_KEYS):
        raise DeliveryError("Release readback source provenance mismatch.")
    assets = release.get("assets", [])
    if len(assets) != len(files) or {asset.get("name") for asset in assets} != set(files):
        raise DeliveryError("Release readback does not contain the complete verified asset set.")
    for asset in assets:
        if api.asset_sha256(asset) != sha256(files[asset["name"]]):
            raise DeliveryError("Release asset readback hash mismatch; draft publication was blocked.")
    return release


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    default_root = str(Path(__file__).resolve().parents[1])
    detector = commands.add_parser("detect", help="Detect pending stable source, using published release history")
    detector.add_argument("--root", default=default_root)
    detector.add_argument("--output", required=True)
    candidate = commands.add_parser("prepare", help="Prepare a reviewed plan without changing its source branch")
    candidate.add_argument("--root", default=default_root)
    candidate.add_argument("--plan", required=True)
    candidate.add_argument("--destination", required=True)
    candidate.add_argument("--output-dir", required=True)
    sync = commands.add_parser("sync", help="Explicitly stage an upstream stable tag for local verification")
    sync.add_argument("--root", default=default_root)
    sync.add_argument("--upstream-ref", required=True)
    sync.add_argument("--upstream-commit")
    sync.add_argument("--version")
    sync.add_argument("--destination", required=True)
    sync.add_argument("--output-dir", required=True)
    for name in ("verify", "render-release", "promote"):
        command = commands.add_parser(name)
        command.add_argument("--metadata", required=True)
        command.add_argument("--bundle", required=True)
        command.add_argument("--artifacts", required=name != "verify")
        if name != "verify":
            command.add_argument("--release-dir", required=True)
        if name == "promote":
            command.add_argument("--root", default=default_root)
            command.add_argument("--output")
            command.add_argument("--resume-archive", help="Publish the already frozen original source/package bytes")
    args = parser.parse_args(argv)
    try:
        if args.command == "detect":
            result = detect(args.root, GitHubApi())
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(json_bytes(result))
        elif args.command == "prepare":
            result = prepare(args.root, read_json(args.plan), args.destination, args.output_dir)
        elif args.command == "sync":
            root = clean_repository(args.root)
            config = head_config(root)
            upstream_version = args.upstream_ref.removeprefix("v")
            version_parts(upstream_version, 3)
            if args.upstream_ref != "v" + upstream_version:
                raise DeliveryError("Local sync requires an explicit stable vX.Y.Z tag.")
            commit = args.upstream_commit or GitHubApi().resolve_tag(UPSTREAM_REPOSITORY, args.upstream_ref)
            plan = {"schemaVersion": 1, "build": True, "mode": "upstream",
                    **{key: config[key] for key in PROVENANCE_KEYS if key in config},
                    "baseCommit": git_text(root, "rev-parse", "HEAD"), "upstreamRef": args.upstream_ref,
                    "upstreamCommit": commit, "upstreamVersion": upstream_version,
                    "version": args.version or f"{upstream_version}.{config['brandingRevision']}"}
            result = prepare(root, plan, args.destination, args.output_dir)
        elif args.command == "verify":
            result = verify_candidate(read_json(args.metadata), args.bundle)
            if args.artifacts:
                verify_artifacts(result, args.artifacts)
        elif args.command == "render-release":
            files = render_release(read_json(args.metadata), args.bundle, args.artifacts, args.release_dir)
            result = {"status": "verified", "files": sorted(files)}
        else:
            result = promote(args.root, read_json(args.metadata), args.bundle, args.artifacts, args.release_dir,
                             GitHubApi(), frozen_archive=args.resume_archive)
            if args.output:
                Path(args.output).write_bytes(json_bytes(result))
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return 0
    except DeliveryError as exc:
        print(f"DeskCue delivery blocked: {exc}", file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError) as exc:
        print(f"DeskCue delivery blocked by invalid input or unavailable dependency ({type(exc).__name__}).", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
