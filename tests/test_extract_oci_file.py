# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest


EXTRACTOR_PATH = (
    Path(__file__).parents[1]
    / "roles"
    / "glance_image"
    / "files"
    / "extract_oci_file.py"
)
SPEC = importlib.util.spec_from_file_location("extract_oci_file", EXTRACTOR_PATH)
assert SPEC is not None
assert SPEC.loader is not None
EXTRACTOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXTRACTOR)


def _tar(entries: list[tuple[str, bytes, bytes]], mode: str = "w") -> bytes:
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode=mode) as archive:
        for name, content, entry_type in entries:
            member = tarfile.TarInfo(name)
            member.type = entry_type
            member.size = len(content)
            archive.addfile(member, io.BytesIO(content))
    return stream.getvalue()


def _digest(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def _oci_archive(path: Path, layers: list[bytes]) -> None:
    blobs: dict[str, bytes] = {}
    descriptors = []
    for layer in layers:
        digest = _digest(layer)
        blobs[digest] = layer
        descriptors.append(
            {
                "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
                "digest": digest,
                "size": len(layer),
            }
        )

    manifest = json.dumps(
        {"schemaVersion": 2, "config": {}, "layers": descriptors}
    ).encode()
    manifest_digest = _digest(manifest)
    blobs[manifest_digest] = manifest
    index = json.dumps(
        {
            "schemaVersion": 2,
            "manifests": [
                {
                    "mediaType": "application/vnd.oci.image.manifest.v1+json",
                    "digest": manifest_digest,
                    "size": len(manifest),
                }
            ],
        }
    ).encode()

    entries = [("index.json", index, tarfile.REGTYPE)]
    entries.extend(
        (
            f"blobs/sha256/{digest.removeprefix('sha256:')}",
            content,
            tarfile.REGTYPE,
        )
        for digest, content in blobs.items()
    )
    path.write_bytes(_tar(entries))


class ExtractOciFileTest(unittest.TestCase):
    target = "/a/b/image.qcow2"

    def _extract(self, layers: list[bytes]) -> bytes:
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "source.oci"
            output = Path(directory) / "image.qcow2"
            _oci_archive(archive, layers)
            EXTRACTOR.extract(archive, self.target, output)
            return output.read_bytes()

    def _assert_hidden(self, upper_entry: tuple[str, bytes, bytes]) -> None:
        lower = _tar(
            [("a/b/image.qcow2", b"lower", tarfile.REGTYPE)],
            mode="w:gz",
        )
        upper = _tar([upper_entry], mode="w:gz")
        with self.assertRaises(FileNotFoundError):
            self._extract([lower, upper])

    def test_newest_layer_wins(self) -> None:
        lower = _tar(
            [("a/b/image.qcow2", b"lower", tarfile.REGTYPE)],
            mode="w:gz",
        )
        upper = _tar(
            [("a/b/image.qcow2", b"upper", tarfile.REGTYPE)],
            mode="w:gz",
        )
        self.assertEqual(b"upper", self._extract([lower, upper]))

    def test_uncompressed_layer(self) -> None:
        layer = _tar(
            [("a/b/image.qcow2", b"image", tarfile.REGTYPE)]
        )
        self.assertEqual(b"image", self._extract([layer]))

    def test_exact_whiteout_hides_target(self) -> None:
        self._assert_hidden(
            ("a/b/.wh.image.qcow2", b"", tarfile.REGTYPE)
        )

    def test_ancestor_whiteout_hides_target(self) -> None:
        self._assert_hidden(("a/.wh.b", b"", tarfile.REGTYPE))
        self._assert_hidden((".wh.a", b"", tarfile.REGTYPE))

    def test_opaque_whiteout_hides_target(self) -> None:
        self._assert_hidden(("a/.wh..wh..opq", b"", tarfile.REGTYPE))

    def test_ancestor_type_change_hides_target(self) -> None:
        self._assert_hidden(("a/b", b"replacement", tarfile.REGTYPE))

    def test_same_layer_target_survives_whiteout(self) -> None:
        lower = _tar(
            [("a/b/image.qcow2", b"lower", tarfile.REGTYPE)],
            mode="w:gz",
        )
        upper = _tar(
            [
                ("a/.wh.b", b"", tarfile.REGTYPE),
                ("a/b/image.qcow2", b"upper", tarfile.REGTYPE),
            ],
            mode="w:gz",
        )
        self.assertEqual(b"upper", self._extract([lower, upper]))


if __name__ == "__main__":
    unittest.main()
