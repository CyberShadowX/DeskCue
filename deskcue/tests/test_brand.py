"""Run the branding CLI against committed, disposable upstream source trees."""
import codecs
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


RECIPE = Path(__file__).resolve().parents[1] / "brand.py"
CONFIG = RECIPE.with_name("config.json")


class BrandingTests(unittest.TestCase):
    def setUp(self):
        # Keep generated source fixtures on the project drive as required by
        # the workspace rules, rather than the Windows profile's TEMP folder.
        scratch = RECIPE.parents[1] / ".artifacts" / "branding-tests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="deskcue-brand-", dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "source"
        self.root.mkdir()
        self.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        # These source fixtures explicitly model upstream 1.5.9/revision 1.
        # Keep them stable when the real release configuration advances.
        self.config.update(upstreamRef="v1.5.9", upstreamVersion="1.5.9",
                           brandingRevision=1, productVersion="1.5.9.1")
        self.fixture = {
            "DeskBox.sln": 'Project = "DeskBox", "src\\DeskBox\\DeskBox.csproj"\n',
            "src/DeskBox/DeskBox.csproj": '<Project><PropertyGroup><RootNamespace>DeskBox</RootNamespace><Version>1.5.9</Version><AssemblyVersion>1.5.9.0</AssemblyVersion><FileVersion>1.5.9.0</FileVersion><InformationalVersion>1.5.9</InformationalVersion></PropertyGroup><Content Include="deskbox_native.dll" /></Project>\n',
            "src/DeskBox/Package.appxmanifest": '<Package><Identity Name="D1FC332A.DeskBoxWidgets" Publisher="CN=3B75AA4A-2433-4F71-9CC1-B644B26F474A" Version="1.5.9.0" /><PublisherDisplayName>Original Author</PublisherDisplayName><PhoneIdentity PhoneProductId="7bb59608-421d-4fd4-8f12-8929f87d086a" PhonePublisherId="00000000-0000-0000-0000-000000000000" /><ToastNotificationActivation ToastActivatorCLSID="4D54EEC6-13BE-4C8F-A8F7-81FE72F4B2C9" /><Class Id="4D54EEC6-13BE-4C8F-A8F7-81FE72F4B2C9" /></Package>\n',
            "src/DeskBox/app.manifest": '<assembly><assemblyIdentity version="1.2.0.0" name="DeskBox" /><assemblyIdentity version="6.0.0.0" name="Microsoft.Windows.Common-Controls" /></assembly>\n',
            "src/DeskBox/MainWindow.xaml": '<Window x:Class="DeskBox.MainWindow" xmlns:local="using:DeskBox" />\n',
            "src/DeskBox/Services/DeskBoxDataPathService.cs": 'namespace DeskBox.Services; const string ProductionInstanceScope = "7F3A9B2E"; // deskBox\n',
            "src/DeskBox/Services/AppUpdateService.cs": 'namespace DeskBox.Services; const string DefaultManifestUrl = "https://deskbox.fun/update/stable.json"; const string DefaultGitHubLatestReleaseApiUrl = "https://api.github.com/repos/Tianyu199509/DeskBox/releases/latest"; const string DefaultManualDownloadUrl = "https://deskbox.fun/download";\n',
            "src/DeskBox/Services/ReleaseNotesService.cs": 'public static readonly IReadOnlyList<string> KnownReleaseVersions =\n[\n    "1.5.9", "1.5.8",\n];\n',
            "src/DeskBox/Services/FeedbackService.cs": 'const string Api = "https://deskbox.fun/stats/api/"; // owner service left for Task2\n',
            "src/DeskBox/Interop.cs": '[DllImport("deskbox_native.dll", EntryPoint="deskbox_get_version")] class DeskBox { const string IID = "00000000-0000-0000-C000-000000000046"; }\n',
            "src/DeskBox.Updater/DeskBox.Updater.csproj": '<Project><PropertyGroup><AssemblyName>DeskBox.Updater</AssemblyName></PropertyGroup></Project>\n',
            "native/Cargo.toml": '[workspace]\nmembers = ["deskbox-native"]\n',
            "native/deskbox-native/Cargo.toml": '[package]\nname = "deskbox-native"\nversion = "0.1.0"\n[lib]\nname = "deskbox_native"\n',
            "native/deskbox-native/src/lib.rs": '#[unsafe(no_mangle)]\npub extern "C" fn deskbox_get_version() {}\n',
            "native/include/deskbox_native.h": '#define DESKBOX_NATIVE_DLL_NAME L"deskbox_native.dll"\nint deskbox_get_version(void);\n',
            "installer/DeskBox.iss": '#define MyAppName "DeskBox"\n#define MyAppVersion "1.5.9"\n#define MyAppVersionInfo "1.5.9.0"\n#define MyAppPublisher "Original Author"\nAppId={{5E052824-3456-427E-9759-3BCAE078A1D3}\n',
            "installer/DeskBox.arm64.iss": '#define MyAppVersion "1.5.9"\n#define MyAppVersionInfo "1.5.9.0"\n#define MyAppPublisher "Original Author"\nAppId={{5E052824-3456-427E-9759-3BCAE078A1D3}\n',
            "scripts/Test-DeskBoxDirectReleaseConsistency.ps1": '$projectVersion = "1.5.9"\n$checks = @(@{ Expected = "$projectVersion.0" })\n',
            "docs/releases/v1.5.9.md": '# DeskBox 1.5.9\nUpstream fixes.\n',
            "README.md": '# DeskBox\nhttps://github.com/Tianyu199509/DeskBox/releases\nhttps://deskbox.fun\n[DeskBox](https://deskbox.fun)\nCopyright (c) 2026 Tianyu199509 DeskBox\nHistorical example: 1.5.9\n',
            "LICENSE": 'DeskBox Copyright (c) Tianyu199509\nSPDX-License-Identifier: GPL-3.0-only\n',
            "src/DeskBox/ThirdParty/NOTICE.txt": 'DeskBox third-party copyright, do not change.\n',
            "src/DeskBox/Assets/LICENSE-images.txt": 'Licensed for DeskBox, original copyright.\n',
            "AGENTS.md": 'DeskBox governance must stay literal.\n',
            "deskcue/overlay.txt": 'DeskBox management must stay literal.\n',
            "docs/superpowers/plan.md": 'DeskBox plan must stay literal.\n',
            "artifacts/DeskBox.txt": 'DeskBox build artifact\n',
            "src/DeskBox/bin/DeskBox.txt": 'DeskBox bin artifact\n',
        }
        for name, content in self.fixture.items():
            self.write(name, content.encode("utf-8"))
        self.write("src/DeskBox/Assets/deskbox.ico", b"\x00\x00DeskBox\xff\xfe\x01")
        self.write("src/DeskBox/Bom.cs", codecs.BOM_UTF8 + b"// DeskBox\r\n")
        self.write("src/DeskBox/Wide.cs", codecs.BOM_UTF16_LE + "// DeskBox\r\n".encode("utf-16-le"))
        self.git("init", "-q")
        self.git("config", "core.autocrlf", "false")
        self.git("config", "core.eol", "lf")
        self.git("add", ".")
        self.commit()
        self.config_path = Path(self.temp.name) / "config.json"

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)

    def git(self, *args):
        result = subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def commit(self):
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "upstream fixture")
        self.config["upstreamCommit"] = self.git("rev-parse", "HEAD")

    def run_recipe(self, *, root=None, expected=0):
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")
        result = subprocess.run([sys.executable, str(RECIPE), "--root", str(root or self.root), "--config", str(self.config_path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        if expected == 2:
            self.assertIn("branding error:", result.stderr)
        return result

    def read(self, name):
        return (self.root / name).read_text(encoding="utf-8")

    def snapshot(self, root=None):
        root = root or self.root
        return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file() and ".git" not in p.parts}

    def test_coordinates_paths_namespaces_native_abi_and_build_references(self):
        self.run_recipe()
        self.assertFalse((self.root / "DeskBox.sln").exists())
        self.assertIn('src\\DeskCue\\DeskCue.csproj', self.read("DeskCue.sln"))
        self.assertIn('x:Class="DeskCue.MainWindow"', self.read("src/DeskCue/MainWindow.xaml"))
        self.assertIn('EntryPoint="deskcue_get_version"', self.read("src/DeskCue/Interop.cs"))
        self.assertIn('fn deskcue_get_version', self.read("native/deskcue-native/src/lib.rs"))
        self.assertIn('DESKCUE_NATIVE_DLL_NAME L"deskcue_native.dll"', self.read("native/include/deskcue_native.h"))
        self.assertIn('name = "deskcue-native"', self.read("native/deskcue-native/Cargo.toml"))
        self.assertIn('// deskCue', self.read("src/DeskCue/Services/DeskCueDataPathService.cs"))

    def test_fixed_product_identities_leave_platform_guids_intact(self):
        self.run_recipe()
        manifest = self.read("src/DeskCue/Package.appxmanifest")
        for value in ("CyberShadowX.DeskCue", "32AFF2BA-34E3-56BE-83E3-671BEBBFA32F", "D61F048B-B5EE-5CC8-87BC-D28E118A8CBB", "E5662752-7950-51E8-9830-6A12DE878954", "00000000-0000-0000-0000-000000000000"):
            self.assertIn(value, manifest)
        self.assertIn("F90973DE-39B2-508A-8DEC-088C53758F37", self.read("installer/DeskCue.iss"))
        self.assertIn('"0F10D29D"', self.read("src/DeskCue/Services/DeskCueDataPathService.cs"))
        self.assertIn("00000000-0000-0000-C000-000000000046", self.read("src/DeskCue/Interop.cs"))

    def test_own_product_links_never_invent_a_host_or_relabel_owner_services(self):
        self.run_recipe()
        update = self.read("src/DeskCue/Services/AppUpdateService.cs")
        self.assertIn("https://github.com/CyberShadowX/DeskCue/releases/latest/download/stable.json", update)
        self.assertIn("https://api.github.com/repos/CyberShadowX/DeskCue/releases/latest", update)
        self.assertIn("https://github.com/CyberShadowX/DeskCue/releases/latest", update)
        self.assertIn("https://deskbox.fun/stats/api/", self.read("src/DeskCue/Services/FeedbackService.cs"))
        self.assertIn("[DeskCue](https://github.com/CyberShadowX/DeskCue)", self.read("README.md"))
        self.assertNotIn("deskcue.fun", "".join(self.read(p) for p in ("README.md", "src/DeskCue/Services/AppUpdateService.cs")))

    def test_versions_metadata_and_current_notes_use_four_parts_without_rewriting_history(self):
        self.run_recipe()
        project = self.read("src/DeskCue/DeskCue.csproj")
        for tag in ("Version", "AssemblyVersion", "FileVersion", "InformationalVersion"):
            self.assertIn(f"<{tag}>1.5.9.1</{tag}>", project)
            self.assertIn(f"<{tag}>1.5.9.1</{tag}>", self.read("src/DeskCue.Updater/DeskCue.Updater.csproj"))
        self.assertIn('Version="1.5.9.1"', self.read("src/DeskCue/Package.appxmanifest"))
        self.assertIn('version="1.5.9.1" name="DeskCue"', self.read("src/DeskCue/app.manifest"))
        self.assertIn('version="6.0.0.0"', self.read("src/DeskCue/app.manifest"))
        self.assertIn('#define MyAppVersionInfo "1.5.9.1"', self.read("installer/DeskCue.arm64.iss"))
        self.assertNotIn('"$projectVersion.0"', self.read("scripts/Test-DeskCueDirectReleaseConsistency.ps1"))
        self.assertIn('"1.5.9.1", "1.5.9", "1.5.8"', self.read("src/DeskCue/Services/ReleaseNotesService.cs").replace("\n", ""))
        self.assertTrue((self.root / "docs/releases/v1.5.9.1.md").is_file())
        self.assertIn("Historical example: 1.5.9", self.read("README.md"))

    def test_legal_binary_encoding_and_management_preservation(self):
        before = self.snapshot()
        self.write("untracked-DeskBox.txt", b"DeskBox personal data")
        self.run_recipe()
        for name in ("LICENSE", "AGENTS.md", "deskcue/overlay.txt", "docs/superpowers/plan.md", "artifacts/DeskBox.txt", "src/DeskBox/bin/DeskBox.txt"):
            self.assertEqual((self.root / name).read_bytes(), before[name])
        for name in ("ThirdParty/NOTICE.txt", "Assets/LICENSE-images.txt", "Assets/deskbox.ico"):
            self.assertEqual((self.root / ("src/DeskCue/" + name.replace("deskbox.ico", "deskcue.ico"))).read_bytes(), before["src/DeskBox/" + name])
        self.assertEqual((self.root / "src/DeskCue/Bom.cs").read_bytes(), codecs.BOM_UTF8 + b"// DeskCue\r\n")
        self.assertEqual((self.root / "src/DeskCue/Wide.cs").read_bytes(), codecs.BOM_UTF16_LE + "// DeskCue\r\n".encode("utf-16-le"))
        self.assertIn("Copyright (c) 2026 Tianyu199509 DeskBox", self.read("README.md"))
        self.assertEqual((self.root / "untracked-DeskBox.txt").read_bytes(), b"DeskBox personal data")

    def test_provenance_is_deterministic_and_records_input_recipe_and_config(self):
        self.run_recipe()
        provenance = json.loads(self.read("deskcue/provenance.json"))
        self.assertEqual(provenance["upstreamCommit"], self.config["upstreamCommit"])
        self.assertEqual(provenance["productVersion"], "1.5.9.1")
        self.assertEqual(provenance["recipeSha256"], hashlib.sha256(RECIPE.read_bytes()).hexdigest())
        self.assertEqual(provenance["configSha256"], hashlib.sha256(self.config_path.read_bytes()).hexdigest())
        self.assertNotIn("timestamp", provenance)
        self.assertEqual(provenance["forkPatches"], ["001-fork-boundaries.patch"])

    def test_linked_worktree_and_checkout_produce_identical_bytes(self):
        linked = Path(self.temp.name) / "linked"
        self.git("worktree", "add", "--detach", str(linked), "HEAD")
        self.assertTrue((linked / ".git").is_file())
        self.run_recipe(root=linked)
        self.run_recipe()
        self.assertEqual(self.snapshot(linked), self.snapshot())

    def test_missing_anchor_fails_before_any_mutation(self):
        (self.root / "native/include/deskbox_native.h").unlink()
        before = self.snapshot()
        self.run_recipe(expected=2)
        self.assertEqual(self.snapshot(), before)

    def test_path_collision_fails_before_any_mutation(self):
        self.write("src/DeskCue/DeskCue.csproj", b"user-owned destination")
        before = self.snapshot()
        self.run_recipe(expected=2)
        self.assertEqual(self.snapshot(), before)

    def test_nested_non_repository_and_already_branded_roots_are_rejected(self):
        for root in (self.root.parent, self.root / "src", self.root / "missing"):
            with self.subTest(root=root):
                self.run_recipe(root=root, expected=2)
        self.run_recipe()
        before = self.snapshot()
        self.run_recipe(expected=2)
        self.assertEqual(self.snapshot(), before)

    def test_invalid_config_and_wrong_commit_fail_without_changes(self):
        before = self.snapshot()
        for key, value in (("schemaVersion", 2), ("productVersion", "1.5.9.1.0"), ("repository", "../evil"), ("brandingRevision", 0), ("upstreamCommit", "0" * 40), ("upstreamReleaseCommit", "not-a-commit"), ("packageIdentity", "D1FC332A.DeskBoxWidgets")):
            original = self.config[key]
            with self.subTest(key=key):
                self.config[key] = value
                self.run_recipe(expected=2)
                self.assertEqual(self.snapshot(), before)
            self.config[key] = original

    def test_changed_owner_identity_anchor_is_rejected_before_writes(self):
        source = self.fixture["src/DeskBox/Package.appxmanifest"].replace("3B75AA4A-2433-4F71-9CC1-B644B26F474A", "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF")
        self.write("src/DeskBox/Package.appxmanifest", source.encode())
        self.git("add", ".")
        self.commit()
        before = self.snapshot()
        self.run_recipe(expected=2)
        self.assertEqual(self.snapshot(), before)

    def test_modified_gitignore_is_preserved_as_management_overlay(self):
        self.write(".gitignore", b"DeskBox-specific original\n")
        self.git("add", ".gitignore")
        self.commit()
        self.write(".gitignore", b"DeskCue Controller ignore additions\n")
        self.run_recipe()
        self.assertEqual((self.root / ".gitignore").read_bytes(), b"DeskCue Controller ignore additions\n")

    def test_destination_parent_symlink_cannot_write_outside_source(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        try:
            (self.root / "src/DeskCue").symlink_to(outside, target_is_directory=True)
        except OSError as error:
            self.skipTest(f"symlink privilege unavailable: {error}")
        self.run_recipe(expected=2)
        self.assertEqual(list(outside.iterdir()), [])

    def make_junction(self, link, target):
        env = dict(os.environ, DESKCUE_FIXTURE_LINK=str(link), DESKCUE_FIXTURE_TARGET=str(target))
        result = subprocess.run(
            ["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command",
             "New-Item -ItemType Junction -Path $env:DESKCUE_FIXTURE_LINK -Target $env:DESKCUE_FIXTURE_TARGET -ErrorAction Stop | Out-Null"],
            env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(link.is_junction(), "fixture must exercise a genuine Windows junction")
        self.addCleanup(lambda: os.rmdir(link) if os.path.lexists(link) else None)

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_source_junction_cannot_read_or_unlink_external_files(self):
        source = self.root / "src/DeskBox/Assets"
        outside = Path(self.temp.name) / "external-assets"
        source.rename(outside)
        self.make_junction(source, outside)
        outside_before = self.snapshot(outside)
        root_before = self.snapshot()
        self.run_recipe(expected=2)
        self.assertEqual(self.snapshot(outside), outside_before)
        self.assertEqual(self.snapshot(), root_before)

    @unittest.skipUnless(os.name == "nt", "Windows junction regression")
    def test_root_junction_is_rejected_without_changing_its_target(self):
        link = Path(self.temp.name) / "root-junction"
        self.make_junction(link, self.root)
        before = self.snapshot()
        self.run_recipe(root=link, expected=2)
        self.assertEqual(self.snapshot(), before)

    def test_ignored_tracked_dlls_survive_a_clean_committed_export(self):
        binary = b"MZ\x00DeskBox original binary\xff\x01"
        self.write(".gitignore", b"*.dll\n")
        self.write("src/DeskBox/ThirdParty/Everything/Everything64.dll", binary)
        self.git("add", ".gitignore")
        self.git("add", "--force", "src/DeskBox/ThirdParty/Everything/Everything64.dll")
        self.commit()
        self.write("untracked-private.dll", b"must never enter the generated tree")
        self.run_recipe()
        self.git("add", "--all")
        tree = self.git("write-tree")
        path = "src/DeskCue/ThirdParty/Everything/Everything64.dll"
        result = subprocess.run(["git", "-C", str(self.root), "show", f"{tree}:{path}"], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, binary)
        self.assertNotIn("untracked-private.dll", self.git("ls-tree", "-r", "--name-only", tree))

    def test_sentence_case_defaults_are_branded_with_the_rest_of_the_product(self):
        self.write("src/DeskBox/defaultWidgetConfig.json", b'{"Title":"Deskbox"}\n')
        self.write("src/DeskBox/Services/SettingsService.cs", b'const string DefaultName = "Deskbox";\n')
        self.git("add", ".")
        self.commit()
        self.run_recipe()
        self.assertEqual(self.read("src/DeskCue/defaultWidgetConfig.json"), '{"Title":"DeskCue"}\n')
        self.assertEqual(self.read("src/DeskCue/Services/SettingsService.cs"), 'const string DefaultName = "DeskCue";\n')

    def test_operational_publisher_fields_use_fork_owner_and_retain_original_credit(self):
        self.run_recipe()
        self.assertIn("<PublisherDisplayName>CyberShadowX</PublisherDisplayName>", self.read("src/DeskCue/Package.appxmanifest"))
        for name in ("installer/DeskCue.iss", "installer/DeskCue.arm64.iss"):
            self.assertIn('#define MyAppPublisher "CyberShadowX"', self.read(name))
        self.assertEqual(self.read("LICENSE"), self.fixture["LICENSE"])
        self.assertIn("Copyright (c) 2026 Tianyu199509 DeskBox", self.read("README.md"))

    def test_ambiguous_publisher_anchor_is_rejected_before_mutation(self):
        name = "installer/DeskBox.iss"
        self.write(name, (self.fixture[name] + '#define MyAppPublisher "Ambiguous"\n').encode())
        self.git("add", ".")
        self.commit()
        before = self.snapshot()
        self.run_recipe(expected=2)
        self.assertEqual(self.snapshot(), before)

    def test_revision_two_drives_metadata_and_provenance_without_changing_identity(self):
        self.config.update(brandingRevision=2, productVersion="1.5.9.2")
        self.run_recipe()
        for path in ("src/DeskCue/DeskCue.csproj", "src/DeskCue.Updater/DeskCue.Updater.csproj"):
            for tag in ("Version", "AssemblyVersion", "FileVersion", "InformationalVersion"):
                self.assertIn(f"<{tag}>1.5.9.2</{tag}>", self.read(path))
        for path in ("installer/DeskCue.iss", "installer/DeskCue.arm64.iss"):
            self.assertIn('#define MyAppVersion "1.5.9.2"', self.read(path))
            self.assertIn('#define MyAppVersionInfo "1.5.9.2"', self.read(path))
            self.assertIn("F90973DE-39B2-508A-8DEC-088C53758F37", self.read(path))
        manifest = self.read("src/DeskCue/Package.appxmanifest")
        self.assertIn('Version="1.5.9.2"', manifest)
        for identity in ("CyberShadowX.DeskCue", "32AFF2BA-34E3-56BE-83E3-671BEBBFA32F",
                         "D61F048B-B5EE-5CC8-87BC-D28E118A8CBB", "E5662752-7950-51E8-9830-6A12DE878954"):
            self.assertIn(identity, manifest)
        self.assertIn('version="1.5.9.2" name="DeskCue"', self.read("src/DeskCue/app.manifest"))
        self.assertIn('"1.5.9.2", "1.5.9", "1.5.8"', self.read("src/DeskCue/Services/ReleaseNotesService.cs").replace("\n", ""))
        self.assertIn('"0F10D29D"', self.read("src/DeskCue/Services/DeskCueDataPathService.cs"))
        self.assertTrue((self.root / "docs/releases/v1.5.9.2.md").is_file())
        self.assertFalse((self.root / "docs/releases/v1.5.9.1.md").exists())
        provenance = json.loads(self.read("deskcue/provenance.json"))
        self.assertEqual(provenance["brandingRevision"], 2)
        self.assertEqual(provenance["productVersion"], "1.5.9.2")


if __name__ == "__main__":
    unittest.main()
