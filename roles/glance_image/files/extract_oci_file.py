#!/usr/bin/env python3
# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0
"""Extract one absolute path from a digest-selected OCI image archive."""

from __future__ import annotations

import io
import json
from pathlib import Path, PurePosixPath
import shutil
import sys
import tarfile


def _member(archive: tarfile.TarFile, name: str) -> bytes:
    member = archive.getmember(name)
    stream = archive.extractfile(member)
    if stream is None:
        raise ValueError(f"OCI member {name} has no content")
    return stream.read()


def _blob_name(digest: str) -> str:
    algorithm, separator, value = digest.partition(":")
    if separator != ":" or algorithm != "sha256" or len(value) != 64:
        raise ValueError(f"unsupported OCI digest {digest}")
    int(value, 16)
    return f"blobs/{algorithm}/{value}"


def _normalized_target(raw_target: str) -> PurePosixPath:
    target = PurePosixPath(raw_target)
    if not target.is_absolute() or ".." in target.parts:
        raise ValueError("OCI artifact path must be absolute and normalized")
    normalized = PurePosixPath(*target.parts[1:])
    if not normalized.parts:
        raise ValueError("OCI artifact path cannot be the root directory")
    return normalized


def _layer_hides_target(names: set[str], target: PurePosixPath) -> bool:
    whiteout = target.parent / f".wh.{target.name}"
    if str(whiteout) in names:
        return True
    for parent in (target.parent, *target.parents):
        if str(parent / ".wh..wh..opq") in names:
            return True
    return False


def extract(archive_path: Path, raw_target: str, output: Path) -> None:
    target = _normalized_target(raw_target)
    with tarfile.open(archive_path, "r:*") as archive:
        index = json.loads(_member(archive, "index.json"))
        manifests = index.get("manifests", [])
        if len(manifests) != 1:
            raise ValueError("OCI archive must contain exactly one selected manifest")
        manifest = json.loads(
            _member(archive, _blob_name(manifests[0]["digest"]))
        )
        layers = manifest.get("layers", [])
        for descriptor in reversed(layers):
            layer_data = _member(archive, _blob_name(descriptor["digest"]))
            with tarfile.open(fileobj=io.BytesIO(layer_data), mode="r:*") as layer:
                members = {
                    (
                        member.name[2:]
                        if member.name.startswith("./")
                        else member.name
                    ): member
                    for member in layer.getmembers()
                }
                target_name = str(target)
                if target_name in members:
                    member = members[target_name]
                    if not member.isfile():
                        raise ValueError(f"OCI artifact {raw_target} is not a file")
                    stream = layer.extractfile(member)
                    if stream is None:
                        raise ValueError(f"OCI artifact {raw_target} has no content")
                    with output.open("wb") as destination:
                        shutil.copyfileobj(stream, destination)
                    return
                if _layer_hides_target(set(members), target):
                    break
    raise FileNotFoundError(f"OCI artifact does not contain {raw_target}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: extract_oci_file.py ARCHIVE PATH OUTPUT")
    extract(Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]))
