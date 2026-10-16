"""Child-only guard and loopback health adapter for Phase A evidence runs."""
import argparse
import json
import os
from pathlib import Path
import runpy
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("runtime", type=Path)
    parser.add_argument("module")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    runtime = args.runtime.resolve()

    def safe_path(value):
        if isinstance(value, int):
            return
        if not Path(os.fsdecode(value)).resolve().is_relative_to(runtime):
            raise PermissionError("A01 write blocked outside isolated runtime")

    def guard(event, values):
        if event == "open":
            path, mode, flags = values
            if (mode and any(c in mode for c in "wax+")) or flags & (
                    os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC):
                safe_path(path)
        elif event in {"os.remove", "os.rmdir", "os.mkdir", "os.chmod"}:
            safe_path(values[0])
        elif event in {"os.rename", "os.link", "os.symlink"}:
            safe_path(values[0])
            safe_path(values[1])
        elif event in {"socket.bind", "socket.connect"}:
            address = values[1]
            if not isinstance(address, tuple) or address[0] != "127.0.0.1":
                raise PermissionError("A01 socket blocked outside IPv4 loopback")
            if event == "socket.bind":
                print("A01_BIND " + json.dumps(address), file=sys.stderr, flush=True)
        elif event in {"subprocess.Popen", "os.system", "os.exec", "os.spawn"}:
            raise PermissionError("A01 nested subprocess blocked")

    sys.addaudithook(guard)
    if args.module == "prepare-key":
        from common import crypto
        key = crypto.generate_mlkem_keypair()
        crypto.save_mlkem_private_key(key, Path(args.args[0]))
        print(crypto.public_key_fingerprint(crypto.public_key_bytes(key.public_key())))
        return
    if args.module in {"cloud.cloud", "gateway.gateway"}:
        from common import health
        original = health.ThreadingHTTPServer

        class LoopbackHealthServer(original):
            def __init__(self, address, handler, *positional, **kwargs):
                super().__init__(("127.0.0.1", address[1]), handler,
                                 *positional, **kwargs)

        health.ThreadingHTTPServer = LoopbackHealthServer
    sys.argv = [args.module, *args.args]
    runpy.run_module(args.module, run_name="__main__")


if __name__ == "__main__":
    main()
