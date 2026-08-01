from __future__ import annotations

import hashlib
import io
import json
import shutil
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import yaml


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import libclang_toolchain_adapter as provider
from libclang_toolchain_contract import ToolchainProviderError


class LibclangToolchainProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.cache_override = self.root / "cache"
        environment = mock.patch.dict(
            "os.environ", {"GOVERNED_TOOLCHAIN_CACHE": str(self.cache_override)}
        )
        environment.start()
        self.addCleanup(environment.stop)

    def _archive(
        self,
        *,
        member: str = "esp-clang/bin/libclang.dll",
        content: bytes = b"official-library",
        link: bool = False,
        extra_member: str | None = None,
        extra_link: bool = False,
    ) -> Path:
        archive = self.root / f"fixture-{len(list(self.root.glob('fixture-*')))}.tar.xz"
        with tarfile.open(archive, "w:xz") as bundle:
            info = tarfile.TarInfo(member)
            if link:
                info.type = tarfile.SYMTYPE
                info.linkname = "../../outside"
                bundle.addfile(info)
            else:
                info.size = len(content)
                bundle.addfile(info, io.BytesIO(content))
            if extra_member is not None:
                extra = tarfile.TarInfo(extra_member)
                if extra_link:
                    extra.type = tarfile.SYMTYPE
                    extra.linkname = "../../outside"
                    bundle.addfile(extra)
                else:
                    extra.size = len(content)
                    bundle.addfile(extra, io.BytesIO(content))
        return archive

    def _lock(self, archive: Path, library_hash: str | None = None) -> Path:
        artifact = {
            "url": archive.as_uri(),
            "archive_sha256": provider._sha256(archive),
            "library_path": "esp-clang/bin/libclang.dll",
            "library_sha256": library_hash
            or hashlib.sha256(b"official-library").hexdigest(),
        }
        document = {
            "schema": provider.LOCK_SCHEMA,
            "libclang_provider": {
                "id": "espressif-esp-clang-libs",
                "version": "20.1.1_test",
                "binding": {"package": "clang", "version": "20.1.5"},
                "target_triple": "xtensa-esp32s3-elf",
                "artifacts": {
                    "windows-x86_64": artifact,
                    "linux-x86_64": artifact,
                },
            },
        }
        path = self.root / "toolchain-lock.yaml"
        path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
        return path

    def _install(self, lock: Path, archive: Path) -> None:
        fake_cindex = SimpleNamespace(Config=SimpleNamespace(set_library_file=lambda _: None))
        with (
            mock.patch(
                "libclang_toolchain_adapter.urllib.request.urlretrieve",
                side_effect=lambda _url, output: shutil.copy2(archive, output),
            ),
            mock.patch(
                "libclang_toolchain_adapter._binding_version",
                return_value="20.1.5",
            ),
            mock.patch(
                "libclang_toolchain_adapter._probe",
                return_value="Espressif clang version 20.1.1",
            ),
            mock.patch.dict(sys.modules, {"clang": SimpleNamespace(cindex=fake_cindex)}),
        ):
            provider.EspressifLibclangToolchainAdapter().install(lock)

    def test_missing_lock_is_cast002(self) -> None:
        with self.assertRaises(ToolchainProviderError) as caught:
            provider.EspressifLibclangToolchainAdapter().verify(
                self.root / "missing.yaml", bind_library=False
            )
        self.assertEqual("CAST002", caught.exception.rule_id)

    def test_wrong_platform_is_cast002(self) -> None:
        lock = self._lock(self._archive())
        with mock.patch.object(provider.sys, "platform", "darwin"):
            with self.assertRaises(ToolchainProviderError) as caught:
                provider.EspressifLibclangToolchainAdapter().verify(
                    lock, bind_library=False
                )
        self.assertEqual("CAST002", caught.exception.rule_id)

    def test_download_failure_is_cast001(self) -> None:
        archive = self._archive()
        lock = self._lock(archive)
        with mock.patch(
            "libclang_toolchain_adapter.urllib.request.urlretrieve",
            side_effect=OSError("offline"),
        ):
            with self.assertRaises(ToolchainProviderError) as caught:
                provider.EspressifLibclangToolchainAdapter().install(lock)
        self.assertEqual("CAST001", caught.exception.rule_id)

    def test_archive_hash_mismatch_is_cast001(self) -> None:
        archive = self._archive()
        lock = self._lock(archive)
        document = yaml.safe_load(lock.read_text(encoding="utf-8"))
        for artifact in document["libclang_provider"]["artifacts"].values():
            artifact["archive_sha256"] = "0" * 64
        lock.write_text(yaml.safe_dump(document), encoding="utf-8")
        with mock.patch(
            "libclang_toolchain_adapter.urllib.request.urlretrieve",
            side_effect=lambda _url, output: shutil.copy2(archive, output),
        ):
            with self.assertRaises(ToolchainProviderError) as caught:
                provider.EspressifLibclangToolchainAdapter().install(lock)
        self.assertEqual("CAST001", caught.exception.rule_id)

    def test_library_hash_mismatch_is_cast001(self) -> None:
        archive = self._archive()
        lock = self._lock(archive, "0" * 64)
        with (
            mock.patch(
                "libclang_toolchain_adapter.urllib.request.urlretrieve",
                side_effect=lambda _url, output: shutil.copy2(archive, output),
            ),
            self.assertRaises(ToolchainProviderError) as caught,
        ):
            provider.EspressifLibclangToolchainAdapter().install(lock)
        self.assertEqual("CAST001", caught.exception.rule_id)

    def test_path_traversal_is_rejected(self) -> None:
        archive = self._archive(member="../outside.dll")
        with self.assertRaises(ToolchainProviderError) as caught:
            provider._safe_extract(archive, self.root / "out")
        self.assertEqual("CAST002", caught.exception.rule_id)

    def test_windows_path_traversal_is_rejected_by_install(self) -> None:
        archive = self._archive(extra_member=r"..\outside.dll")
        lock = self._lock(archive)
        with self.assertRaises(ToolchainProviderError) as caught:
            self._install(lock, archive)
        self.assertEqual("CAST002", caught.exception.rule_id)
        self.assertEqual(r"..\outside.dll", caught.exception.location)

    def test_link_entry_is_rejected_by_install(self) -> None:
        archive = self._archive(
            extra_member="esp-clang/lib/libclang.so",
            extra_link=True,
        )
        lock = self._lock(archive)
        with self.assertRaises(ToolchainProviderError) as caught:
            self._install(lock, archive)
        self.assertEqual("CAST002", caught.exception.rule_id)
        self.assertEqual("esp-clang/lib/libclang.so", caught.exception.location)

    def test_incomplete_cache_is_cast002(self) -> None:
        archive = self._archive()
        lock = self._lock(archive)
        cache = (
            self.cache_override
            / "espressif"
            / "esp-clang-libs"
            / "20.1.1_test"
        )
        cache.mkdir(parents=True)
        with self.assertRaises(ToolchainProviderError) as caught:
            provider.EspressifLibclangToolchainAdapter().verify(
                lock, bind_library=False
            )
        self.assertEqual("CAST002", caught.exception.rule_id)

    def test_wrong_binding_version_is_cast001(self) -> None:
        archive = self._archive()
        lock = self._lock(archive)
        self._install(lock, archive)
        with mock.patch(
            "libclang_toolchain_adapter.importlib.metadata.version",
            return_value="19.0.0",
        ):
            with self.assertRaises(ToolchainProviderError) as caught:
                provider.EspressifLibclangToolchainAdapter().verify(
                    lock, bind_library=False
                )
        self.assertEqual("CAST001", caught.exception.rule_id)

    def test_backend_probe_failure_is_cast001(self) -> None:
        archive = self._archive()
        lock = self._lock(archive)
        fake_cindex = SimpleNamespace(Config=SimpleNamespace(set_library_file=lambda _: None))
        failure = ToolchainProviderError("CAST001", "xtensa", "no backend")
        with (
            mock.patch(
                "libclang_toolchain_adapter.urllib.request.urlretrieve",
                side_effect=lambda _url, output: shutil.copy2(archive, output),
            ),
            mock.patch(
                "libclang_toolchain_adapter._binding_version",
                return_value="20.1.5",
            ),
            mock.patch("libclang_toolchain_adapter._probe", side_effect=failure),
            mock.patch.dict(sys.modules, {"clang": SimpleNamespace(cindex=fake_cindex)}),
            self.assertRaises(ToolchainProviderError) as caught,
        ):
            provider.EspressifLibclangToolchainAdapter().install(lock)
        self.assertEqual("CAST001", caught.exception.rule_id)

    def test_modified_receipt_is_cast002(self) -> None:
        archive = self._archive()
        lock = self._lock(archive)
        self._install(lock, archive)
        receipt = next(self.cache_override.rglob(provider.RECEIPT_NAME))
        document = json.loads(receipt.read_text(encoding="utf-8"))
        document["library_sha256"] = "0" * 64
        receipt.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaises(ToolchainProviderError) as caught:
            provider.EspressifLibclangToolchainAdapter().verify(
                lock, bind_library=False
            )
        self.assertEqual("CAST002", caught.exception.rule_id)

    def test_existing_valid_cache_is_reused_without_download(self) -> None:
        archive = self._archive()
        lock = self._lock(archive)
        self._install(lock, archive)
        with (
            mock.patch(
                "libclang_toolchain_adapter.urllib.request.urlretrieve"
            ) as download,
            mock.patch(
                "libclang_toolchain_adapter._binding_version",
                return_value="20.1.5",
            ),
        ):
            evidence = provider.EspressifLibclangToolchainAdapter().install(lock)
        download.assert_not_called()
        self.assertEqual("20.1.1_test", evidence.provider_version)
