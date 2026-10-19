"""Opt-in managed lab entry; initialize mandatory TLS before app imports."""
import sys

from common.secure_transport import TransportError, initialize_tls_policy


def main():
    try:
        initialize_tls_policy()
    except (TransportError, OSError) as exc:
        print(f'TLS startup rejected: {exc}', file=sys.stderr)
        return 3
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('role', choices=('gateway', 'cloud'))
    parser.add_argument('--config', required=True)
    arguments = parser.parse_args()
    if not Path(arguments.config).is_absolute():
        parser.error('--config must be an absolute path')
    from common.managed_config import ManagedConfiguration
    from common.secure_runtime import service_main
    sys.argv = [arguments.role + '.managed', '--config', arguments.config]
    return service_main(arguments.role, configuration_class=ManagedConfiguration)


if __name__ == '__main__':
    raise SystemExit(main())
