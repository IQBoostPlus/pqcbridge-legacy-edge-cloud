"""Fresh-process launcher: validate mandatory TLS policy before app imports."""
import sys

from common.secure_transport import TransportError, initialize_tls_policy


def main():
    try:
        initialize_tls_policy()
    except (TransportError, OSError) as exc:
        print(f"TLS startup rejected: {exc}", file=sys.stderr)
        return 3
    import argparse
    import runpy
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role", choices=("gateway", "cloud"))
    parser.add_argument("--config", required=True)
    arguments = parser.parse_args()
    if not Path(arguments.config).is_absolute():
        parser.error("--config must be an absolute path")
    sys.argv = [arguments.role + ".secure", "--config", arguments.config]
    runpy.run_module(arguments.role + ".secure", run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
