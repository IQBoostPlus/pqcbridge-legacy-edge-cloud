"""Explicit engineering cloud entry point; use the secure bootstrap launcher."""
import sys


def main():
    from common.secure_transport import require_initialized
    try:
        require_initialized()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 3
    from common.secure_runtime import service_main
    return service_main('cloud')


if __name__ == '__main__':
    raise SystemExit(main())
