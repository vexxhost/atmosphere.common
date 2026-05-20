#!/usr/bin/env python3
# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
import os


class ETagHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        etag = Path(self.server.etag_file).read_text(encoding="utf-8").strip()
        if etag:
            self.send_header("ETag", etag)
        super().end_headers()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--etag-file", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18080)
    args = parser.parse_args()

    os.chdir(args.directory)
    server = ThreadingHTTPServer((args.host, args.port), ETagHandler)
    server.etag_file = args.etag_file
    server.serve_forever()


if __name__ == "__main__":
    main()
