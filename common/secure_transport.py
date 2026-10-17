"""Bounded JSON framing and the pre-initialization mandatory-hybrid TLS boundary.

Applications start through ``common.secure_bootstrap``. Importing this module
does not initialize OpenSSL; the launcher validates the controlled policy first.
"""
import os
import json
import math
from pathlib import Path
import select
import sys
import time


POLICY_BYTES = (
    b"config_diagnostics = 1\n"
    b"openssl_conf = openssl_init\n"
    b"[openssl_init]\n"
    b"ssl_conf = ssl_section\n"
    b"[ssl_section]\n"
    b"system_default = tls_defaults\n"
    b"[tls_defaults]\n"
    b"MinProtocol = TLSv1.3\n"
    b"MaxProtocol = TLSv1.3\n"
    b"Groups = X25519MLKEM768\n"
)


class TransportError(ValueError):
    """The transport policy, identity or application frame is invalid."""


_ssl_module = None
_policy_path = None


def _validate_policy():
    configured = os.environ.get("OPENSSL_CONF")
    if not configured or not Path(configured).is_absolute():
        raise TransportError("OPENSSL_CONF must name an absolute controlled policy")
    path = Path(configured)
    try:
        if path.read_bytes() != POLICY_BYTES:
            raise TransportError("OPENSSL_CONF must contain the exact hybrid policy bytes")
    except OSError as exc:
        raise TransportError("OPENSSL_CONF policy cannot be read") from exc
    for name in ("OPENSSL_CONF_INCLUDE", "OPENSSL_MODULES", "OPENSSL_ENGINES"):
        if name in os.environ:
            raise TransportError(f"unexpected OpenSSL environment override: {name}")
    return path.resolve()


def initialize_tls_policy():
    """Validate before the first OpenSSL import; refuse unsupported runtimes.

    Repeated calls may reuse this module's initialization, but cannot switch
    policy. Environment and bytes are checked on every context construction.
    """
    global _ssl_module, _policy_path
    path = _validate_policy()
    if _ssl_module is not None:
        if path != _policy_path:
            raise TransportError("TLS policy path changed after initialization")
        return _ssl_module
    if any(name in sys.modules for name in ("ssl", "_ssl", "_hashlib")) or any(
        name.startswith("cryptography.hazmat.bindings") for name in sys.modules
    ):
        raise TransportError("OpenSSL was imported before controlled TLS initialization")
    import ssl
    # The approved target is OpenSSL 3.5 with the official hybrid group. A
    # different series requires revalidation rather than an assumed fallback.
    if ssl.OPENSSL_VERSION_INFO[:2] != (3, 5):
        raise TransportError("validated OpenSSL 3.5 runtime required")
    _policy_path, _ssl_module = path, ssl
    return ssl


def require_initialized():
    """Refuse alternate application entrypoints, even with matching env flags."""
    if _ssl_module is None or _policy_path is None:
        raise TransportError("secure bootstrap is required before application imports")
    return initialize_tls_policy()


def _credential_path(tls, name):
    value = tls.get(name)
    if not isinstance(value, str) or not Path(value).is_absolute():
        raise TransportError(f"TLS {name} must be an absolute path")
    if not Path(value).is_file():
        raise TransportError(f"TLS {name} must name an existing file")
    return value


def _context(tls, *, server):
    ssl = initialize_tls_policy()
    if not isinstance(tls, dict):
        raise TransportError("TLS configuration must be an object")
    if not server:
        hostname = tls.get("server_hostname")
        if not isinstance(hostname, str) or not hostname or "\x00" in hostname:
            raise TransportError("TLS server_hostname is required")
    paths = {name: _credential_path(tls, name) for name in ("ca_file", "cert_file", "key_file")}
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER if server else ssl.PROTOCOL_TLS_CLIENT)
        context.minimum_version = context.maximum_version = ssl.TLSVersion.TLSv1_3
        context.verify_mode = ssl.CERT_REQUIRED
        context.options |= ssl.OP_NO_TICKET
        if server:
            context.num_tickets = 0
        else:
            context.check_hostname = True
            context.hostname_checks_common_name = False
        context.load_verify_locations(cafile=paths["ca_file"])
        context.load_cert_chain(certfile=paths["cert_file"], keyfile=paths["key_file"])
        return context
    except (ssl.SSLError, OSError, ValueError) as exc:
        raise TransportError("TLS credentials or context initialization failed") from exc


def server_context(tls):
    """Build TLS-1.3-only mTLS server under the preloaded hybrid group policy."""
    return _context(tls, server=True)


def client_context(tls):
    """Build TLS-1.3-only mTLS client; caller supplies configured SNI hostname."""
    return _context(tls, server=False)


def peer_fingerprint(connection):
    """SHA-256 of the verified peer's DER certificate on this TLS socket."""
    ssl = require_initialized()
    if connection.context.verify_mode != ssl.CERT_REQUIRED or connection.version() != "TLSv1.3":
        raise TransportError("verified TLS 1.3 peer required")
    certificate = connection.getpeercert(binary_form=True)
    if not certificate or not connection.getpeercert():
        raise TransportError("verified peer certificate required")
    import hashlib
    return hashlib.sha256(certificate).hexdigest()


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise TransportError("duplicate JSON object key")
        result[key] = value
    return result


def _float(value):
    result = float(value)
    if not math.isfinite(result):
        raise TransportError("non-finite JSON number")
    return result


def _constant(value):
    raise TransportError("non-finite JSON constant")


def _limit(max_bytes):
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 3:
        raise TransportError("frame byte limit must be an integer of at least three")


class SocketFrameReader:
    """A connection owner's bounded, deadline-aware binary line reader.

    Set a new deadline immediately before each application frame. TLS internal
    decrypted bytes and this reader's coalesced bytes count as readable even
    when the kernel has no new input. This reader never closes its socket.
    """

    def __init__(self, connection, max_prefetch=65537):
        if (isinstance(max_prefetch, bool) or not isinstance(max_prefetch, int)
                or not 3 <= max_prefetch <= 65537):
            raise TransportError("reader capacity must be between three and 65537 bytes")
        self._connection = connection
        self._capacity = max_prefetch
        self._buffer = bytearray()
        self._deadline = None
        self._closed = False

    @staticmethod
    def _seconds(value):
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or not 0 <= value <= 5):
            raise TransportError("socket wait/deadline must be a finite value from zero to five seconds")
        return value

    def _open(self):
        if self._closed:
            raise TransportError("frame reader is closed")

    def set_deadline(self, seconds):
        self._open()
        self._deadline = time.monotonic() + self._seconds(seconds)

    def wait_readable(self, timeout):
        self._open()
        timeout = self._seconds(timeout)
        if self._buffer:
            return True
        pending = getattr(self._connection, "pending", None)
        if pending is not None and pending():
            return True
        return bool(select.select([self._connection], [], [], timeout)[0])

    def readline(self, limit):
        self._open()
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= self._capacity:
            raise TransportError("line limit exceeds bounded reader capacity")
        if self._deadline is None:
            raise TransportError("set a frame deadline before reading")
        connection = self._connection
        previous_timeout = connection.gettimeout()
        try:
            while True:
                remaining = self._deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("whole frame deadline expired")
                newline = self._buffer.find(b"\n", 0, limit)
                if newline >= 0:
                    length = newline + 1
                    result = bytes(self._buffer[:length])
                    del self._buffer[:length]
                    return result
                if len(self._buffer) >= limit:
                    result = bytes(self._buffer[:limit])
                    del self._buffer[:limit]
                    return result
                connection.settimeout(remaining)
                piece = connection.recv(min(4096, limit - len(self._buffer)))
                if time.monotonic() >= self._deadline:
                    raise TimeoutError("whole frame deadline expired")
                if not piece:
                    result = bytes(self._buffer)
                    self._buffer.clear()
                    return result
                self._buffer.extend(piece)
        finally:
            connection.settimeout(previous_timeout)

    def close(self):
        self._buffer.clear()
        self._closed = True

    def __enter__(self):
        self._open()
        return self

    def __exit__(self, *_):
        self.close()


def read_frame(stream, max_bytes=16384):
    """Read one strict UTF-8 JSON object including its required newline.

    Network callers use SocketFrameReader and set its whole-frame deadline.
    In-memory binary streams are also accepted for bounded event parsing.
    The size limit includes the final newline. The stream keeps later frames.
    EOF, partial frames and oversized messages terminate the caller's session.
    """
    _limit(max_bytes)
    raw = stream.readline(max_bytes + 1)
    if not isinstance(raw, bytes) or not raw or len(raw) > max_bytes or not raw.endswith(b"\n"):
        raise TransportError("missing, truncated or oversized frame")
    try:
        result = json.loads(raw.decode("utf-8"), object_pairs_hook=_object,
                            parse_float=_float, parse_constant=_constant)
        if not isinstance(result, dict):
            raise TransportError("frame must be a JSON object")
        # json.loads permits escaped lone surrogates; they are not UTF-8 text.
        json.dumps(result, ensure_ascii=False, allow_nan=False).encode("utf-8")
        return result
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise TransportError("invalid strict UTF-8 JSON frame") from exc


def send_frame(sock, message, max_bytes=16384):
    """Validate/encode completely before sending any application bytes."""
    _limit(max_bytes)
    if not isinstance(message, dict):
        raise TransportError("frame must be a JSON object")
    try:
        raw = json.dumps(message, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"
    except (UnicodeError, ValueError, TypeError, RecursionError) as exc:
        raise TransportError("invalid strict UTF-8 JSON frame") from exc
    if len(raw) > max_bytes:
        raise TransportError("oversized frame")
    sock.sendall(raw)
