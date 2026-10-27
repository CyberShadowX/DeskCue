"""Delivery contracts; all source mutations use disposable local Git repositories."""

from __future__ import annotations

import importlib.util
import hashlib
import copy
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request


MODULE = Path(__file__).resolve().parents[1] / "delivery.py"
OWNED_POLICY_FIXTURE = {
    "SECURITY.md": "Private contact through CyberShadowX/DeskCue security; no inherited email.\n",
    "CODE_OF_CONDUCT.md": "DeskCue conduct reports follow the owned security contact policy.\n",
    "CONTRIBUTING.md": "Use your own configured Git author identity; preserve upstream attribution.\n",
    "SUPPORT.md": "Feedback opens public CyberShadowX/DeskCue Issues; no automatic diagnostics upload.\n",
    ".github/PULL_REQUEST_TEMPLATE.md": "Use your own configured Git author identity.\n",
    "docs/code-signing.md": "No DeskCue signing service or certificate is configured.\n",
    ".github/workflows/distribution-audit.yml": "name: Legacy audit\njobs:\n  distribution:\n    if: ${{ false }}\n",
}
if MODULE.exists():
    spec = importlib.util.spec_from_file_location("deskcue_delivery", MODULE)
    delivery = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(delivery)
else:
    delivery = None


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True)
    return result.stdout.decode("utf-8").strip()


class RepositoryCase(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(delivery, "delivery helpers have not been implemented")
        scratch = Path(__file__).resolve().parents[2] / ".artifacts/delivery-tests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="deskcue-delivery-", dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.root = self.home / "fork"
        self.root.mkdir()
        git(self.root, "init", "-b", "main")
        git(self.root, "config", "user.name", "Fixture")
        git(self.root, "config", "user.email", "fixture@example.invalid")
        (self.root / "source.txt").write_text("upstream\n", encoding="utf-8")
        git(self.root, "add", ".")
        git(self.root, "commit", "-m", "upstream")
        self.upstream_sha = git(self.root, "rev-parse", "HEAD")
        git(self.root, "tag", "v1.5.9")
        self.config = {
            "schemaVersion": 1, "productName": "DeskCue",
            "repository": "CyberShadowX/DeskCue", "upstreamRepository": "Tianyu199509/DeskBox",
            "upstreamRef": "v1.5.9", "upstreamCommit": self.upstream_sha,
            "upstreamVersion": "1.5.9", "brandingRevision": 1, "productVersion": "1.5.9.1",
            "forkPatches": ["001-own.patch"],
        }
        (self.root / "deskcue").mkdir()
        (self.root / "deskcue/patches").mkdir()
        (self.root / "deskcue/patches/001-own.patch").write_text(
            "diff --git a/source.txt b/source.txt\n--- a/source.txt\n+++ b/source.txt\n@@ -1 +1 @@\n-DeskCue new\n+own replayed fix\n", encoding="utf-8")
        self.write_config()
        (self.root / "deskcue/provenance.json").write_text(json.dumps(self.config), encoding="utf-8")
        (self.root / "source.txt").write_text("own reviewed fix\n", encoding="utf-8")
        git(self.root, "add", ".")
        git(self.root, "commit", "-m", "reviewed fork")
        self.head = git(self.root, "rev-parse", "HEAD")

    def write_config(self):
        (self.root / "deskcue/config.json").write_text(json.dumps(self.config), encoding="utf-8")

    def release(self, version="1.5.9", commit=None, **extra):
        repo = "CyberShadowX/DeskCue" if len(version.split(".")) == 4 else "Tianyu199509/DeskBox"
        value = {"id": 42, "tag_name": "v" + version, "draft": False, "prerelease": False,
                 "url": f"https://api.github.com/repos/{repo}/releases/42",
                 "html_url": f"https://github.com/{repo}/releases/tag/v{version}", "assets": []}
        if len(version.split(".")) == 4:
            value["body"] = delivery.release_body({**self.config, "sourceCommit": commit or self.head,
                                                    "version": version, "brandingRevision": int(version.split(".")[3]),
                                                    "upstreamVersion": ".".join(version.split(".")[:3])})
        value.update(extra)
        return value


class FakeApi:
    def __init__(self, upstream, own=None, resolved=None):
        self.upstream = upstream
        self.own = own or []
        self.resolved = resolved

    def releases(self, repository):
        return self.own if repository == "CyberShadowX/DeskCue" else self.upstream

    def resolve_tag(self, repository, tag):
        return self.resolved


class DetectionTests(RepositoryCase):
    def test_initial_release_builds_reviewed_head_even_with_new_upstream(self):
        plan = delivery.detect(self.root, FakeApi([self.release("1.6.0")], resolved="a" * 40))
        self.assertEqual((plan["mode"], plan["baseCommit"], plan["version"]),
                         ("head", self.head, "1.5.9.1"))

    def test_draft_and_prerelease_upstream_are_ignored(self):
        api = FakeApi([self.release("1.6.0", draft=True), self.release("1.7.0", prerelease=True),
                       self.release()], [self.release("1.5.9.1")], self.upstream_sha)
        self.assertFalse(delivery.detect(self.root, api)["build"])

    def test_unchanged_successful_release_does_not_rebuild(self):
        api = FakeApi([self.release()], [self.release("1.5.9.1")], self.upstream_sha)
        self.assertEqual(delivery.detect(self.root, api)["reason"], "already-published")

    def test_new_stable_source_requests_reconstruction(self):
        plan = delivery.detect(self.root, FakeApi([self.release("1.6.0")],
                                                 [self.release("1.5.9.1")], "a" * 40))
        self.assertEqual((plan["mode"], plan["version"], plan["upstreamCommit"]),
                         ("upstream", "1.6.0.1", "a" * 40))

    def test_advanced_main_without_published_release_remains_pending(self):
        self.config.update(brandingRevision=2, productVersion="1.5.9.2")
        self.write_config()
        git(self.root, "add", ".")
        git(self.root, "commit", "-m", "pending version")
        plan = delivery.detect(self.root, FakeApi([self.release()],
                                                 [self.release("1.5.9.1", commit=self.head)], self.upstream_sha))
        self.assertEqual((plan["build"], plan["mode"], plan["version"]), (True, "head", "1.5.9.2"))

    def test_foreign_release_url_fails_closed(self):
        own = self.release("1.5.9.1", html_url="https://github.com/Tianyu199509/DeskBox/releases/tag/v1.5.9.1")
        with self.assertRaises(delivery.DeliveryError):
            delivery.detect(self.root, FakeApi([self.release()], [own], self.upstream_sha))

    def test_moved_stable_tag_does_not_silently_rebuild(self):
        with self.assertRaises(delivery.DeliveryError):
            delivery.detect(self.root, FakeApi([self.release()], [self.release("1.5.9.1")], "b" * 40))

    def test_uncommitted_source_is_not_a_release_input(self):
        (self.root / "source.txt").write_text("unreviewed", encoding="utf-8")
        with self.assertRaises(delivery.DeliveryError):
            delivery.detect(self.root, FakeApi([self.release()], resolved=self.upstream_sha))


class SourceCase(RepositoryCase):
    def setUp(self):
        super().setUp()
        self.assertTrue(callable(getattr(delivery, "prepare", None)), "isolated candidate preparation is missing")
        recipe = '''import argparse,json,pathlib,hashlib
p=argparse.ArgumentParser();p.add_argument('--root');p.add_argument('--config');a=p.parse_args()
r=pathlib.Path(a.root);c=json.loads(pathlib.Path(a.config).read_text())
(r/'source.txt').write_text((r/'source.txt').read_text().replace('upstream','DeskCue'),newline='')
(r/'deskcue').mkdir(exist_ok=True)
c.update(recipeSha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),configSha256=hashlib.sha256(pathlib.Path(a.config).read_bytes()).hexdigest(),sourceTreeSha256='d'*64,sourceFileCount=1)
(r/'deskcue/provenance.json').write_text(json.dumps(c))
'''
        (self.root / "deskcue/brand.py").write_text(recipe, encoding="utf-8")
        for path, content in OWNED_POLICY_FIXTURE.items():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        git(self.root, "add", ".")
        git(self.root, "commit", "-m", "recipe")
        provenance = {**self.config, "recipeSha256": hashlib.sha256(git(self.root, "show", "HEAD:deskcue/brand.py").encode()).hexdigest(),
                      "configSha256": hashlib.sha256(git(self.root, "show", "HEAD:deskcue/config.json").encode()).hexdigest(),
                      "sourceTreeSha256": "d" * 64, "sourceFileCount": 1}
        # git() strips the final recipe newline; include its tracked bytes exactly.
        provenance["recipeSha256"] = hashlib.sha256(subprocess.check_output(["git", "-C", str(self.root), "show", "HEAD:deskcue/brand.py"])).hexdigest()
        (self.root / "deskcue/provenance.json").write_text(json.dumps(provenance), encoding="utf-8")
        git(self.root, "add", ".")
        git(self.root, "commit", "-m", "provenance")
        self.head = git(self.root, "rev-parse", "HEAD")
        self.destination = self.home / "candidate"
        self.output = self.home / "output"

    def plan(self, **updates):
        return {"schemaVersion": 1, "build": True, "mode": "head", "baseCommit": self.head,
                "version": "1.5.9.1", **self.config, **updates}

    def next_upstream(self, policies=None):
        self.upstream = self.home / "upstream"
        git(self.home, "clone", "--no-local", str(self.root), str(self.upstream))
        git(self.upstream, "checkout", "--detach", self.upstream_sha)
        git(self.upstream, "config", "user.name", "Upstream")
        git(self.upstream, "config", "user.email", "upstream@example.invalid")
        (self.upstream / "source.txt").write_text("upstream new\n", encoding="utf-8")
        for path, content in (policies or {}).items():
            target = self.upstream / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        git(self.upstream, "add", ".")
        git(self.upstream, "commit", "-m", "new upstream")
        git(self.upstream, "tag", "v1.6.0")
        sha = git(self.upstream, "rev-parse", "HEAD")
        return self.plan(mode="upstream", upstreamRef="v1.6.0", upstreamVersion="1.6.0",
                         upstreamCommit=sha, version="1.6.0.1")


class CandidateTests(SourceCase):
    def test_first_candidate_preserves_exact_reviewed_head_and_bundle(self):
        metadata = delivery.prepare(self.root, self.plan(), self.destination, self.output)
        self.assertEqual(metadata["sourceCommit"], self.head)
        self.assertEqual((self.destination / "source.txt").read_text(), "own reviewed fix\n")
        self.assertEqual(git(self.root, "rev-parse", "HEAD"), self.head)
        verified = delivery.verify_candidate(metadata, self.output / "candidate.bundle")
        self.assertEqual(verified["sourceTree"], git(self.root, "rev-parse", "HEAD^{tree}"))

    def test_new_upstream_receives_reviewed_overlay_and_patch_with_two_parents(self):
        plan = self.next_upstream()
        patchdir = self.root / "deskcue/patches"
        patchdir.mkdir(exist_ok=True)
        (patchdir / "001-own.patch").write_text(
            "diff --git a/source.txt b/source.txt\n--- a/source.txt\n+++ b/source.txt\n@@ -1 +1 @@\n-DeskCue new\n+own replayed fix\n", encoding="utf-8")
        (self.root / "private-user-data.txt").write_text("never copied", encoding="utf-8")
        git(self.root, "add", "deskcue")
        git(self.root, "commit", "--allow-empty", "-m", "reviewed patch")
        (self.root / "private-user-data.txt").unlink()
        plan["baseCommit"] = git(self.root, "rev-parse", "HEAD")
        metadata = delivery.prepare(self.root, plan, self.destination, self.output, upstream_url=str(self.upstream))
        self.assertEqual((self.destination / "source.txt").read_text(), "own replayed fix\n")
        self.assertEqual(git(self.destination, "show", "-s", "--format=%P", "HEAD").split(),
                         [plan["baseCommit"], plan["upstreamCommit"]])
        self.assertFalse((self.destination / "private-user-data.txt").exists())
        self.assertEqual(json.loads((self.destination / "deskcue/config.json").read_text())["productVersion"], "1.6.0.1")
        self.assertEqual(metadata["upstreamCommit"], plan["upstreamCommit"])

    def test_conflicting_replay_does_not_advance_source_or_emit_success_metadata(self):
        plan = self.next_upstream()
        patchdir = self.root / "deskcue/patches"
        patchdir.mkdir(exist_ok=True)
        (patchdir / "001-own.patch").write_text("not a valid patch", encoding="utf-8")
        git(self.root, "add", ".")
        git(self.root, "commit", "-m", "bad patch")
        plan["baseCommit"] = git(self.root, "rev-parse", "HEAD")
        with self.assertRaises(delivery.DeliveryError):
            delivery.prepare(self.root, plan, self.destination, self.output, upstream_url=str(self.upstream))
        self.assertEqual(git(self.root, "rev-parse", "HEAD"), plan["baseCommit"])
        self.assertFalse((self.output / "candidate.json").exists())

    def test_upstream_contacts_and_signing_cannot_replace_owned_policy(self):
        upstream_policies = {
            "SECURITY.md": "Report DeskBox security to 1047078635@qq.com.\n",
            "CODE_OF_CONDUCT.md": "Conduct contact: 1047078635@qq.com.\n",
            "CONTRIBUTING.md": "Only original maintainer contributions accepted.\n",
            "SUPPORT.md": "Submit anonymous diagnostic packages to the original service.\n",
            ".github/PULL_REQUEST_TEMPLATE.md": "Commit as Simon <1047078635@qq.com>.\n",
            "docs/code-signing.md": "DeskBox test signing verified 2026-10-08.\n",
            ".github/workflows/distribution-audit.yml": (
                "organization-id: e4f8de42-d97c-409d-b768-ee383c34c15b\nproject-slug: DeskBox\n"),
        }
        plan = self.next_upstream(upstream_policies)
        metadata = delivery.prepare(self.root, plan, self.destination, self.output, upstream_url=str(self.upstream))
        for path, content in OWNED_POLICY_FIXTURE.items():
            with self.subTest(path=path):
                self.assertEqual((self.destination / path).read_text(encoding="utf-8"), content)
                self.assertEqual(git(self.destination, "show", f"HEAD:{path}"), content.rstrip())
        self.assertEqual(metadata["upstreamCommit"], plan["upstreamCommit"])

    def test_missing_owned_policy_blocks_upstream_candidate(self):
        plan = self.next_upstream({"SECURITY.md": "Original maintainer contact must not reappear.\n"})
        (self.root / "SECURITY.md").unlink()
        git(self.root, "add", "--all")
        git(self.root, "commit", "-m", "lost fork security policy")
        plan["baseCommit"] = git(self.root, "rev-parse", "HEAD")
        with self.assertRaisesRegex(delivery.DeliveryError, "required tracked fork policy"):
            delivery.prepare(self.root, plan, self.destination, self.output, upstream_url=str(self.upstream))
        self.assertEqual(git(self.root, "rev-parse", "HEAD"), plan["baseCommit"])
        self.assertFalse((self.output / "candidate.json").exists())

    def test_destination_cannot_overwrite_repository_or_existing_directory(self):
        for destination in (self.root, self.home, self.root / "deskcue"):
            with self.subTest(destination=destination), self.assertRaises(delivery.DeliveryError):
                delivery.prepare(self.root, self.plan(), destination, self.output)
        self.assertEqual((self.root / "source.txt").read_text(), "own reviewed fix\n")

    def test_concurrent_head_change_aborts_before_success_metadata(self):
        plan = self.next_upstream()

        def advance_root(command):
            subprocess.run(command, check=True, capture_output=True)
            (self.root / "source.txt").write_text("concurrent source", encoding="utf-8")
            git(self.root, "add", ".")
            git(self.root, "commit", "-m", "concurrent")

        with self.assertRaises(delivery.DeliveryError):
            delivery.prepare(self.root, plan, self.destination, self.output,
                             upstream_url=str(self.upstream), brand_runner=advance_root)
        self.assertFalse((self.output / "candidate.json").exists())

    def test_tampered_bundle_or_provenance_fails_verification(self):
        metadata = delivery.prepare(self.root, self.plan(), self.destination, self.output)
        metadata["upstreamCommit"] = "f" * 40
        with self.assertRaises(delivery.DeliveryError):
            delivery.verify_candidate(metadata, self.output / "candidate.bundle")

    def test_missing_required_tracked_patch_blocks_head_candidate(self):
        (self.root / "deskcue/patches/001-own.patch").unlink()
        git(self.root, "add", "--all")
        git(self.root, "commit", "-m", "accidentally lost patch")
        plan = self.plan(baseCommit=git(self.root, "rev-parse", "HEAD"))
        with self.assertRaises(delivery.DeliveryError):
            delivery.prepare(self.root, plan, self.destination, self.output)
        self.assertFalse((self.output / "candidate.json").exists())

    def test_candidate_verification_checks_required_patch_hash_inventory(self):
        metadata = delivery.prepare(self.root, self.plan(), self.destination, self.output)
        metadata["forkPatchSha256"] = {"001-own.patch": "f" * 64}
        with self.assertRaises(delivery.DeliveryError):
            delivery.verify_candidate(metadata, self.output / "candidate.bundle")

    def test_undeclared_tracked_patch_is_not_silently_replayed(self):
        (self.root / "deskcue/patches/999-unreviewed.patch").write_text("must not run", encoding="utf-8")
        git(self.root, "add", ".")
        git(self.root, "commit", "-m", "unexpected patch")
        plan = self.plan(baseCommit=git(self.root, "rev-parse", "HEAD"))
        with self.assertRaises(delivery.DeliveryError):
            delivery.prepare(self.root, plan, self.destination, self.output)

    def test_source_bundle_bytes_are_identical_when_retrying_same_head(self):
        first = delivery.prepare(self.root, self.plan(), self.destination, self.output)
        second = delivery.prepare(self.root, self.plan(), self.home / "candidate-two", self.home / "output-two")
        self.assertEqual(first["bundle"]["sha256"], second["bundle"]["sha256"])
        self.assertEqual((self.output / "candidate.bundle").read_bytes(), (self.home / "output-two/candidate.bundle").read_bytes())

    def test_pre_push_guard_rejects_advertised_intermediate_commit_race(self):
        remote = self.home / "remote.git"
        git(self.home, "init", "--bare", str(remote))
        git(self.root, "push", str(remote), "HEAD:refs/heads/main")
        for number in (1, 2):
            (self.root / "source.txt").write_text(f"change {number}", encoding="utf-8")
            git(self.root, "add", ".")
            git(self.root, "commit", "-m", f"change {number}")
            if number == 1:
                intermediate = git(self.root, "rev-parse", "HEAD")
        candidate = git(self.root, "rev-parse", "HEAD")
        bundle = self.home / "candidate.bundle"
        delivery.bundle_candidate(self.root, candidate, bundle)
        metadata = {"baseCommit": self.head, "sourceCommit": candidate, "version": "1.5.9.1"}

        def advance_after_inspection():
            git(self.root, "push", str(remote), f"{intermediate}:refs/heads/main")

        with self.assertRaises(delivery.DeliveryError):
            delivery.push_candidate(self.root, str(remote), metadata, bundle, before_push=advance_after_inspection)
        self.assertEqual(git(remote, "rev-parse", "refs/heads/main"), intermediate)
        self.assertEqual(git(remote, "tag", "--list"), "")


class DeliveryApi:
    """In-memory GitHub boundary; Git pushes still reach a real local bare remote."""
    def __init__(self, fail_publish=False):
        self.release = None
        self.files = {}
        self.fail_publish = fail_publish
        self.deleted_assets = []

    def find_release(self, tag):
        return self.release

    def create_release(self, metadata):
        tag = "v" + metadata["version"]
        self.release = {"id": 7, "tag_name": tag, "draft": True, "prerelease": False,
                        "url": "https://api.github.com/repos/CyberShadowX/DeskCue/releases/7",
                        "html_url": "https://github.com/CyberShadowX/DeskCue/releases/tag/untagged-fixture",
                        "body": delivery.release_body(metadata), "assets": []}
        return self.release

    def upload_asset(self, release_id, path):
        self.files[path.name] = path.read_bytes()
        self.release["assets"].append({"id": len(self.files), "name": path.name,
                                        "state": "uploaded", "digest": "sha256:" + delivery.sha256(path), "size": path.stat().st_size})

    def download_asset(self, asset_id, path):
        asset = next(asset for asset in self.release["assets"] if asset["id"] == asset_id)
        path.write_bytes(self.files[asset["name"]])

    def releases(self, repository):
        if repository == "CyberShadowX/DeskCue":
            return [self.release] if self.release else []
        return [{"id": 1, "tag_name": "v1.5.9", "draft": False, "prerelease": False,
                 "html_url": "https://github.com/Tianyu199509/DeskBox/releases/tag/v1.5.9", "assets": []}]

    def delete_incomplete_asset(self, asset_id):
        for asset in self.release["assets"]:
            if asset["id"] == asset_id:
                self.files.pop(asset["name"], None)
        self.deleted_assets.append(asset_id)
        self.release["assets"] = [asset for asset in self.release["assets"] if asset["id"] != asset_id]

    def asset_sha256(self, asset):
        return delivery.GitHubApi.asset_sha256(self, asset)

    def publish_release(self, release_id):
        if self.fail_publish:
            raise delivery.DeliveryError("simulated API interruption")
        self.release["draft"] = False
        self.release["html_url"] = "https://github.com/CyberShadowX/DeskCue/releases/tag/" + self.release["tag_name"]
        return self.release


class ReleaseTests(SourceCase):
    def setUp(self):
        super().setUp()
        self.assertTrue(callable(getattr(delivery, "render_release", None)), "verified release assembly is missing")
        self.metadata = delivery.prepare(self.root, self.plan(), self.destination, self.output)
        self.bundle = self.output / "candidate.bundle"
        self.artifacts = self.home / "packages"
        for platform, rid in (("x64", "win-x64"), ("ARM64", "win-arm64")):
            folder = self.artifacts / rid
            folder.mkdir(parents=True)
            name = f"DeskCue_Setup_1.5.9.1_{platform.lower()}.exe"
            installer = folder / name
            installer.write_bytes(b"MZ" + platform.encode("ascii") * 32)
            digest = delivery.sha256(installer)
            (folder / (name + ".sha256")).write_text(f"{digest}  {name}\n", encoding="ascii")
            receipt = {"schemaVersion": 1, "status": "passed", "platform": platform,
                       "runtimeIdentifier": rid, "sourceCommit": self.head, "version": "1.5.9.1",
                       "upstreamRepository": "Tianyu199509/DeskBox", "upstreamCommit": self.upstream_sha,
                       "brandingRevision": 1, "retailSummarySha256": "a" * 64,
                       "tests": {"total": 5, "passed": 5, "failed": 0, "skipped": 0},
                       "installer": {"fileName": name, "path": name, "sha256": digest, "bytes": installer.stat().st_size}}
            (folder / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")

    def receipt_change(self, mutate):
        path = self.artifacts / "win-x64/receipt.json"
        value = json.loads(path.read_text())
        mutate(value)
        path.write_text(json.dumps(value), encoding="utf-8")

    def replace_with_different_fresh_build(self):
        for rid in ("win-x64", "win-arm64"):
            folder = self.artifacts / rid
            receipt_path = folder / "receipt.json"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            name = receipt["installer"]["fileName"]
            package = folder / name
            package.write_bytes(b"MZfresh Inno payload timestamp differs " + rid.encode())
            digest = delivery.sha256(package)
            receipt["installer"].update(sha256=digest, bytes=package.stat().st_size)
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            (folder / (name + ".sha256")).write_text(f"{digest}  {name}\n", encoding="ascii")

    def remote(self):
        remote = self.home / "remote.git"
        git(self.home, "init", "--bare", str(remote))
        git(self.root, "push", str(remote), "HEAD:refs/heads/main")
        return remote

    def test_manifest_matches_both_architectures_and_has_no_local_paths(self):
        files = delivery.render_release(self.metadata, self.bundle, self.artifacts, self.home / "release")
        manifest = json.loads(files["stable.json"].read_text(encoding="utf-8"))
        self.assertEqual(manifest["downloadUrl"], "https://github.com/CyberShadowX/DeskCue/releases/download/v1.5.9.1/DeskCue_Setup_1.5.9.1_x64.exe")
        self.assertTrue(manifest["arm64DownloadUrl"].endswith("_arm64.exe"))
        self.assertEqual(manifest["source"]["commit"], self.head)
        self.assertNotIn(str(self.home), files["stable.json"].read_text(encoding="utf-8"))
        self.assertEqual(set(manifest["architectures"]), {"x64", "arm64"})

    def test_real_github_draft_url_can_upload_then_publish_canonical_release(self):
        api = DeliveryApi()
        result = delivery.promote(self.root, self.metadata, self.bundle, self.artifacts,
                                  self.home / "release", api, remote=str(self.remote()))
        self.assertFalse(api.release["draft"])
        self.assertEqual(result["url"], "https://github.com/CyberShadowX/DeskCue/releases/tag/v1.5.9.1")

    def test_draft_api_url_cannot_claim_foreign_repository(self):
        api = DeliveryApi()
        api.create_release(self.metadata)
        api.release["url"] = "https://api.github.com/repos/foreign/DeskCue/releases/7"
        with self.assertRaises(delivery.DeliveryError):
            delivery.promote(self.root, self.metadata, self.bundle, self.artifacts,
                             self.home / "release", api, remote=str(self.remote()))

    def test_path_traversal_receipt_cannot_read_or_publish_outside_file(self):
        self.receipt_change(lambda receipt: receipt["installer"].update(path="../private.exe"))
        with self.assertRaises(delivery.DeliveryError):
            delivery.render_release(self.metadata, self.bundle, self.artifacts, self.home / "release")
        self.assertFalse((self.home / "release").exists())

    def test_different_commit_receipt_does_not_promote_main(self):
        remote = self.remote()
        self.receipt_change(lambda receipt: receipt.update(sourceCommit="c" * 40))
        with self.assertRaises(delivery.DeliveryError):
            delivery.promote(self.root, self.metadata, self.bundle, self.artifacts,
                             self.home / "release", DeliveryApi(), remote=str(remote))
        self.assertEqual(git(remote, "rev-parse", "refs/heads/main"), self.head)
        self.assertEqual(git(remote, "tag", "--list"), "")

    def test_partial_or_skipped_tests_are_not_successful_build_evidence(self):
        self.receipt_change(lambda receipt: receipt["tests"].update(passed=4, skipped=1))
        with self.assertRaises(delivery.DeliveryError):
            delivery.render_release(self.metadata, self.bundle, self.artifacts, self.home / "release")

    def test_installer_hash_mismatch_does_not_create_release(self):
        remote = self.remote()
        installer = self.artifacts / "win-x64/DeskCue_Setup_1.5.9.1_x64.exe"
        installer.write_bytes(b"MZtampered")
        api = DeliveryApi()
        with self.assertRaises(delivery.DeliveryError):
            delivery.promote(self.root, self.metadata, self.bundle, self.artifacts,
                             self.home / "release", api, remote=str(remote))
        self.assertIsNone(api.release)

    def test_concurrent_remote_main_advance_is_rejected(self):
        remote = self.remote()
        (self.root / "new.txt").write_text("concurrent", encoding="utf-8")
        git(self.root, "add", ".")
        git(self.root, "commit", "-m", "advance main")
        advanced = git(self.root, "rev-parse", "HEAD")
        git(self.root, "push", str(remote), "HEAD:refs/heads/main")
        with self.assertRaises(delivery.DeliveryError):
            delivery.promote(self.root, self.metadata, self.bundle, self.artifacts,
                             self.home / "release", DeliveryApi(), remote=str(remote))
        self.assertEqual(git(remote, "rev-parse", "refs/heads/main"), advanced)

    def test_api_publish_failure_can_retry_without_rewriting_tag_or_assets(self):
        remote = self.remote()
        api = DeliveryApi(fail_publish=True)
        with self.assertRaises(delivery.DeliveryError):
            delivery.promote(self.root, self.metadata, self.bundle, self.artifacts,
                             self.home / "release-first", api, remote=str(remote))
        previous = dict(api.files)
        self.assertTrue(api.release["draft"])
        self.assertEqual(git(remote, "rev-parse", "refs/tags/v1.5.9.1"), self.head)
        api.fail_publish = False
        delivery.promote(self.root, self.metadata, self.bundle, self.artifacts,
                         self.home / "release-retry", api, remote=str(remote))
        self.assertFalse(api.release["draft"])
        self.assertEqual(previous, api.files)

    def test_existing_tag_with_different_source_is_never_replaced(self):
        remote = self.remote()
        git(self.root, "push", str(remote), f"{self.upstream_sha}:refs/tags/v1.5.9.1")
        with self.assertRaises(delivery.DeliveryError):
            delivery.promote(self.root, self.metadata, self.bundle, self.artifacts,
                             self.home / "release", DeliveryApi(), remote=str(remote))
        self.assertEqual(git(remote, "rev-parse", "refs/tags/v1.5.9.1"), self.upstream_sha)

    def test_existing_release_different_asset_bytes_is_not_overwritten(self):
        remote = self.remote()
        api = DeliveryApi()
        api.create_release(self.metadata)
        api.release["assets"] = [{"id": 99, "name": "stable.json", "state": "uploaded", "size": 1,
                                  "digest": "sha256:" + "b" * 64}]
        with self.assertRaises(delivery.DeliveryError):
            delivery.promote(self.root, self.metadata, self.bundle, self.artifacts,
                             self.home / "release", api, remote=str(remote))
        self.assertEqual(api.release["assets"][0]["digest"], "sha256:" + "b" * 64)

    def test_missing_uploaded_asset_readback_prevents_publication(self):
        class DroppedUploadApi(DeliveryApi):
            def upload_asset(self, release_id, path):
                if path.name != "stable.json":
                    super().upload_asset(release_id, path)

        remote = self.remote()
        api = DroppedUploadApi()
        with self.assertRaises(delivery.DeliveryError):
            delivery.promote(self.root, self.metadata, self.bundle, self.artifacts,
                             self.home / "release", api, remote=str(remote))
        self.assertTrue(api.release["draft"])

    def test_fresh_workflow_resumes_frozen_original_bytes_despite_different_rebuild(self):
        remote = self.remote()
        first_api = DeliveryApi(fail_publish=True)
        with self.assertRaises(delivery.DeliveryError):
            delivery.promote(self.root, self.metadata, self.bundle, self.artifacts,
                             self.home / "release-first", first_api, remote=str(remote))
        original = dict(first_api.files)
        self.replace_with_different_fresh_build()
        self.assertNotEqual(original["DeskCue_Setup_1.5.9.1_x64.exe"],
                            (self.artifacts / "win-x64/DeskCue_Setup_1.5.9.1_x64.exe").read_bytes())
        # A new workflow process only has repository/API state; no previous run directory.
        second_api = DeliveryApi()
        second_api.release = copy.deepcopy(first_api.release)
        second_api.files = dict(first_api.files)
        plan = delivery.detect(self.root, second_api)
        self.assertEqual((plan["mode"], plan.get("rebuild")), ("resume", False))
        resumed = self.home / "fresh-run-candidate"
        metadata = delivery.prepare(self.root, plan, self.home / "unused-source", resumed, api=second_api)
        result = delivery.promote(self.root, metadata, resumed / "candidate.bundle", self.artifacts,
                                  self.home / "release-fresh-run", second_api, remote=str(remote),
                                  frozen_archive=resumed / "frozen-delivery.zip")
        self.assertEqual(result["status"], "published")
        self.assertEqual(second_api.files, original)

    def test_partial_installer_upload_resumes_from_first_frozen_asset(self):
        class InterruptedApi(DeliveryApi):
            def upload_asset(self, release_id, path):
                super().upload_asset(release_id, path)
                if path.name.endswith("_x64.exe"):
                    raise delivery.DeliveryError("connection lost after completed installer upload")

        remote = self.remote()
        api = InterruptedApi()
        with self.assertRaises(delivery.DeliveryError):
            delivery.promote(self.root, self.metadata, self.bundle, self.artifacts,
                             self.home / "release-partial", api, remote=str(remote))
        self.assertEqual(next(iter(api.files)), "DeskCue_Delivery_1.5.9.1.zip")
        original_installer = api.files["DeskCue_Setup_1.5.9.1_x64.exe"]
        self.replace_with_different_fresh_build()
        delivery.verify_artifacts(self.metadata, self.artifacts)
        resume_api = DeliveryApi()
        resume_api.release, resume_api.files = copy.deepcopy(api.release), dict(api.files)
        plan = delivery.detect(self.root, resume_api)
        resumed = self.home / "resume"
        metadata = delivery.prepare(self.root, plan, self.home / "unused", resumed, api=resume_api)
        delivery.promote(self.root, metadata, resumed / "candidate.bundle", self.artifacts,
                         self.home / "release-complete", resume_api, remote=str(remote),
                         frozen_archive=resumed / "frozen-delivery.zip")
        self.assertFalse(resume_api.release["draft"])
        self.assertEqual(resume_api.files["DeskCue_Setup_1.5.9.1_x64.exe"], original_installer)

    def assert_starter_resumes_from_frozen_workflow(self, filename):
        class IncompleteUploadApi(DeliveryApi):
            def upload_asset(self, release_id, path):
                if path.name == filename:
                    self.files[path.name] = b""
                    self.release["assets"].append({"id": 999, "name": path.name, "state": "starter",
                                                    "size": 0, "digest": None,
                                                    "url": "https://api.github.com/repos/CyberShadowX/DeskCue/releases/assets/999"})
                    raise delivery.DeliveryError("GitHub 502 left a zero-byte starter asset")
                super().upload_asset(release_id, path)

        remote = self.remote()
        first = IncompleteUploadApi()
        original_installer = (self.artifacts / "win-x64/DeskCue_Setup_1.5.9.1_x64.exe").read_bytes()
        with self.assertRaises(delivery.DeliveryError):
            delivery.promote(self.root, self.metadata, self.bundle, self.artifacts,
                             self.home / "starter-first-run", first, remote=str(remote))
        frozen_bytes = first.files["DeskCue_Delivery_1.5.9.1.zip"]
        completed = {name: data for name, data in first.files.items() if name != filename}
        self.replace_with_different_fresh_build()
        # A new process has only persisted repository/API state, including the real starter descriptor.
        second = DeliveryApi()
        second.release, second.files = copy.deepcopy(first.release), dict(first.files)
        plan = delivery.detect(self.root, second)
        self.assertEqual((plan["mode"], plan["rebuild"]), ("resume", False))
        resumed = self.home / "starter-fresh-workflow"
        metadata = delivery.prepare(self.root, plan, self.home / "unused-starter-source", resumed, api=second)
        result = delivery.promote(self.root, metadata, resumed / "candidate.bundle", self.artifacts,
                                  self.home / "starter-finished", second, remote=str(remote),
                                  frozen_archive=resumed / "frozen-delivery.zip")
        self.assertEqual(result["status"], "published")
        self.assertEqual(second.deleted_assets, [999])
        self.assertEqual(second.files["DeskCue_Delivery_1.5.9.1.zip"], frozen_bytes)
        self.assertEqual(second.files["DeskCue_Setup_1.5.9.1_x64.exe"], original_installer)
        self.assertTrue(all(second.files[name] == data for name, data in completed.items()))

    def test_incomplete_installer_new_workflow_retries_original_frozen_bytes(self):
        self.assert_starter_resumes_from_frozen_workflow("DeskCue_Setup_1.5.9.1_x64.exe")

    def test_incomplete_checksum_new_workflow_retries_original_frozen_bytes(self):
        self.assert_starter_resumes_from_frozen_workflow("DeskCue_Setup_1.5.9.1_x64.exe.sha256")

    def test_invalid_empty_or_nonempty_asset_descriptors_are_never_deleted(self):
        remote = self.remote()
        first = DeliveryApi(fail_publish=True)
        with self.assertRaises(delivery.DeliveryError):
            delivery.promote(self.root, self.metadata, self.bundle, self.artifacts,
                             self.home / "complete-frozen", first, remote=str(remote))
        filename = "DeskCue_Setup_1.5.9.1_x64.exe"
        descriptors = ({"state": "uploaded", "size": 0, "digest": None},
                       {"size": 0, "digest": None},
                       {"state": "starter", "size": 1, "digest": None})
        for index, descriptor in enumerate(descriptors):
            with self.subTest(descriptor=descriptor):
                api = DeliveryApi()
                api.release, api.files = copy.deepcopy(first.release), dict(first.files)
                asset = next(value for value in api.release["assets"] if value["name"] == filename)
                identifier = asset["id"]
                asset.clear()
                asset.update(id=identifier, name=filename, **descriptor)
                before = copy.deepcopy(api.release)
                with self.assertRaises(delivery.DeliveryError):
                    delivery.promote(self.root, self.metadata, self.bundle, self.artifacts,
                                     self.home / f"refuse-invalid-{index}", api, remote=str(remote),
                                     frozen_archive=self.home / "complete-frozen/DeskCue_Delivery_1.5.9.1.zip")
                self.assertEqual(api.deleted_assets, [])
                self.assertEqual(api.release, before)

    def test_failed_first_archive_does_not_freeze_different_future_build_bytes(self):
        class FirstArchiveFailureApi(DeliveryApi):
            def upload_asset(self, release_id, path):
                raise delivery.DeliveryError("archive upload never completed")

        remote = self.remote()
        first = FirstArchiveFailureApi()
        with self.assertRaises(delivery.DeliveryError):
            delivery.promote(self.root, self.metadata, self.bundle, self.artifacts,
                             self.home / "failed-archive", first, remote=str(remote))
        self.assertFalse(first.files)
        self.replace_with_different_fresh_build()
        second = DeliveryApi()
        second.release = copy.deepcopy(first.release)
        plan = delivery.detect(self.root, second)
        self.assertTrue(plan["rebuild"])
        result = delivery.promote(self.root, self.metadata, self.bundle, self.artifacts,
                                  self.home / "new-build", second, remote=str(remote))
        self.assertEqual(result["status"], "published")
        self.assertTrue(second.files["DeskCue_Setup_1.5.9.1_x64.exe"].startswith(b"MZfresh"))

    def test_frozen_archive_digest_mismatch_blocks_resume_before_extraction(self):
        api = DeliveryApi(fail_publish=True)
        with self.assertRaises(delivery.DeliveryError):
            delivery.promote(self.root, self.metadata, self.bundle, self.artifacts,
                             self.home / "initial", api, remote=str(self.remote()))
        plan = delivery.detect(self.root, api)
        self.assertEqual(plan["mode"], "resume")
        archive_name = "DeskCue_Delivery_1.5.9.1.zip"
        api.files[archive_name] = b"tampered archive"
        output = self.home / "bad-resume"
        with self.assertRaises(delivery.DeliveryError):
            delivery.prepare(self.root, plan, self.home / "unused", output, api=api)
        self.assertFalse((output / "candidate.json").exists())

    def test_incomplete_first_upload_is_cleaned_without_replacing_completed_assets(self):
        api = DeliveryApi()
        api.create_release(self.metadata)
        api.release["assets"] = [{"id": 47, "name": "DeskCue_Delivery_1.5.9.1.zip",
                                  "state": "starter", "size": 0, "digest": None}]
        plan = delivery.detect(self.root, api)
        self.assertTrue(plan["rebuild"])
        result = delivery.promote(self.root, self.metadata, self.bundle, self.artifacts,
                                  self.home / "complete-first-upload", api, remote=str(self.remote()))
        self.assertEqual(result["status"], "published")
        self.assertFalse(any(asset["id"] == 47 for asset in api.release["assets"]))

    def test_frozen_zip_traversal_cannot_create_an_outside_file(self):
        archive = self.home / "traversal.zip"
        with zipfile.ZipFile(archive, "w") as stream:
            stream.writestr("frozen.json", "{}")
            stream.writestr("../outside.txt", "must not escape")
        target = self.home / "unpacked"
        with self.assertRaises(delivery.DeliveryError):
            delivery.restore_frozen_delivery(archive, target)
        self.assertFalse(target.exists())
        self.assertFalse((self.home / "outside.txt").exists())

    def test_changed_bytes_during_release_copy_cannot_be_published(self):
        original = delivery.shutil.copyfile

        def broken_copy(source, destination):
            result = original(source, destination)
            if str(destination).endswith("_x64.exe"):
                Path(destination).write_bytes(b"MZchanged while copying")
            return result

        with patch.object(delivery.shutil, "copyfile", side_effect=broken_copy):
            with self.assertRaises(delivery.DeliveryError):
                delivery.render_release(self.metadata, self.bundle, self.artifacts, self.home / "release")


class ApiTests(unittest.TestCase):
    def test_asset_hash_rejects_null_digest_on_incomplete_descriptors_without_network(self):
        api = delivery.GitHubApi("not-sent")
        for fields in ({"state": "starter", "size": 0}, {"state": "uploaded", "size": 0},
                       {"size": 0}, {"state": "starter", "size": 1}):
            with self.subTest(fields=fields), patch.object(api, "request", side_effect=AssertionError("must not request")):
                with self.assertRaises(delivery.DeliveryError):
                    api.asset_sha256({"id": 999, "name": "file.exe", "digest": None, **fields})

    def test_api_credentials_cannot_be_sent_to_foreign_host(self):
        self.assertIsNotNone(delivery)
        with self.assertRaises(delivery.DeliveryError):
            delivery.GitHubApi("never-send-me").request("https://foreign.invalid/releases")

    def test_release_asset_redirect_strips_api_authorization(self):
        request = Request("https://api.github.com/repos/CyberShadowX/DeskCue/releases/assets/1",
                          headers={"Authorization": "Bearer never-forward-me"})
        redirected = delivery.SafeGitHubRedirect().redirect_request(
            request, None, 302, "Found", {}, "https://release-assets.githubusercontent.com/asset")
        self.assertIsNone(redirected.get_header("Authorization"))

    def test_foreign_redirect_fails_before_requesting_target(self):
        with self.assertRaises(delivery.DeliveryError):
            delivery.SafeGitHubRedirect().redirect_request(Request("https://api.github.com/"),
                                                           None, 302, "Found", {}, "https://foreign.invalid/asset")


if __name__ == "__main__":
    unittest.main()
