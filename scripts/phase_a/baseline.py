"""Reproduce A-01 using copied sources, loopback sockets and external state.

The existing interpreter/dependencies are reused read-only. No installation,
Docker mutation, real device traffic, or original state is used.
"""
import argparse
import contextlib
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import secrets
import shutil
import socket
import subprocess
import sys
import time
import urllib.request


REPO = Path(__file__).resolve().parents[2]
CHILD = Path(__file__).with_name("baseline_child.py")


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def source_snapshot(destination):
    """Copy only program/test/deployment sources, excluding user state/.env."""
    destination.mkdir(parents=True)
    for directory in ("common", "device", "gateway", "cloud", "tests"):
        shutil.copytree(REPO / directory, destination / directory,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for pattern in ("pytest.ini", "requirements.txt", ".gitignore",
                    "Dockerfile.*", "docker-compose.yml", ".dockerignore"):
        for source in REPO.glob(pattern):
            shutil.copy2(source, destination / source.name)
    return destination


def isolated_environment(runtime, source):
    # In particular do not inherit app config, PYTHONPATH, proxy settings,
    # PYTEST_ADDOPTS or third-party pytest plugin configuration.
    env = {name: value for name, value in os.environ.items() if name.upper() in {
        "SYSTEMROOT", "WINDIR", "COMSPEC", "PATH", "PATHEXT",
        "PROCESSOR_ARCHITECTURE", "NUMBER_OF_PROCESSORS", "OS"}}
    temporary = runtime / "tmp"
    temporary.mkdir(exist_ok=True)
    env.update({"TEMP": str(temporary), "TMP": str(temporary),
                "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(source),
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTHONUTF8": "1",
                "DEVICE_STATE_DIR": str(runtime / "unused-device-state"),
                "CLOUD_KEY_FILE": str(runtime / "unused-cloud-key")})
    return env


def available_ports(count):
    sockets = []
    try:
        for _ in range(count):
            sock = socket.socket()
            sock.bind(("127.0.0.1", 0))
            sockets.append(sock)
        return [sock.getsockname()[1] for sock in sockets]
    finally:
        for sock in sockets:
            sock.close()


class IsolatedStack:
    """Owned subprocess lifecycle. Keys remain in the external runtime only."""
    def __init__(self, runtime, source, python):
        self.runtime = runtime
        self.source = source
        self.python = str(python)
        self.processes = {}
        self.log_files = []
        self.env = isolated_environment(runtime, source)
        (self.cloud_port, self.gateway_port, self.cloud_health_port,
         self.gateway_health_port) = available_ports(4)
        self.device_id = "dev-baseline"
        self.gateway_id = "gw-baseline"
        self.device_key = secrets.token_bytes(32)
        gateway_key = secrets.token_bytes(32)
        write_json(runtime / "device-keys.json",
                   {self.device_id: self.device_key.hex()})
        write_json(runtime / "gateway-keys.json",
                   {self.gateway_id: gateway_key.hex()})
        self.env.update({"DEVICE_KEYS_FILE": str(runtime / "device-keys.json"),
                         "GATEWAY_KEYS_FILE": str(runtime / "gateway-keys.json"),
                         "DEVICE_KEY_HEX": self.device_key.hex(),
                         "GATEWAY_KEY_HEX": gateway_key.hex()})

    def child_command(self, module, *args):
        return [self.python, "-B", str(CHILD), str(self.runtime), module,
                *map(str, args)]

    def launch(self, name, module, *args):
        log = (self.runtime / (name + ".log")).open("wb")
        self.log_files.append(log)
        process = subprocess.Popen(self.child_command(module, *args),
                                   cwd=self.source, env=self.env, stdout=log,
                                   stderr=subprocess.STDOUT)
        self.processes[name] = process
        return process

    def start(self):
        result = subprocess.run(self.child_command(
            "prepare-key", self.runtime / "cloud.key"), cwd=self.source,
            env=self.env, capture_output=True, text=True, timeout=15)
        (self.runtime / "prepare-key.log").write_text(
            result.stdout + result.stderr, encoding="utf-8")
        result.check_returncode()
        pin = result.stdout.strip()
        if len(pin) != 64 or any(c not in "0123456789abcdef" for c in pin):
            raise RuntimeError("local key provisioning did not return a fingerprint")
        self.env["CLOUD_PUBLIC_KEY_SHA256"] = pin
        self.launch("cloud", "cloud.cloud", "--listen-host", "127.0.0.1",
                    "--listen-port", self.cloud_port, "--health-port",
                    self.cloud_health_port, "--key-file", self.runtime / "cloud.key")
        self.wait_for(self.cloud_health, "cloud readiness")
        self.launch("gateway", "gateway.gateway", "--gateway-id", self.gateway_id,
                    "--listen-host", "127.0.0.1", "--listen-port", self.gateway_port,
                    "--cloud-host", "127.0.0.1", "--cloud-port", self.cloud_port,
                    "--health-port", self.gateway_health_port)
        self.wait_for(lambda: self.gateway_health().get("cloud_connected"),
                      "authenticated gateway readiness")
        # Health starts just before the device listener; wait without sending
        # application messages. This probe is disclosed in the evidence.
        def listener_ready():
            with socket.create_connection(("127.0.0.1", self.gateway_port), timeout=1):
                return True
        self.wait_for(listener_ready, "device listener readiness")

    def wait_for(self, predicate, label, timeout=15):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if any(proc.poll() is not None for proc in self.processes.values()):
                raise RuntimeError("service exited during " + label)
            try:
                value = predicate()
                if value:
                    return value
            except (OSError, ValueError):
                pass
            time.sleep(0.05)
        raise TimeoutError(label)

    def get_json(self, port, route):
        # Bypass inherited system proxies, even if the host configures one.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f"http://127.0.0.1:{port}{route}", timeout=1) as response:
            return json.load(response)

    def readings(self):
        return self.get_json(self.cloud_health_port, "/readings")

    def cloud_health(self):
        return self.get_json(self.cloud_health_port, "/health")

    def gateway_health(self):
        return self.get_json(self.gateway_health_port, "/health")

    def start_device(self, interval=0.2):
        return self.launch("device", "device.device", "--device-id", self.device_id,
                           "--gateway-host", "127.0.0.1", "--gateway-port",
                           self.gateway_port, "--interval", interval, "--state-dir",
                           self.runtime / "device-state")

    def close(self):
        for process in reversed(list(self.processes.values())):
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        for log in self.log_files:
            log.close()


@contextlib.contextmanager
def isolated_stack(runtime, source=None, python=None):
    """Launch existing Cloud/Gateway with loopback-only health adaptation.

    runtime must be a new external directory. Returned stack exposes
    gateway_port, device_id, device_key, readings and health methods. All
    child processes terminate on exit; raw logs and synthetic state remain.
    This is a test launch, not validation of unmodified health deployment.
    """
    runtime = Path(runtime).resolve()
    if runtime.is_relative_to(REPO):
        raise ValueError("runtime must be outside the repository")
    runtime.mkdir(parents=True, exist_ok=False)
    source = Path(source).resolve() if source else source_snapshot(runtime / "source")
    stack = IsolatedStack(runtime, source, python or sys.executable)
    try:
        stack.start()
        yield stack
    finally:
        stack.close()


def protected_hashes():
    paths = [REPO / name for name in (".env", "README.md", "CLAUDE.md")]
    for directory in ("cloud_state", "device_state", "docs"):
        root = REPO / directory
        if root.exists():
            paths.extend(p for p in root.rglob("*") if p.is_file()
                         and not p.is_relative_to(REPO / "docs" / "phase-a"))
    return {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(set(paths)) if p.is_file()}


def read_command(command, cwd=None, env=None, timeout=20):
    try:
        result = subprocess.run(command, cwd=cwd, env=env, timeout=timeout,
                                capture_output=True, text=True, encoding="utf-8",
                                errors="replace")
        return {"returncode": result.returncode, "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip()}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"returncode": None, "error": type(exc).__name__}


def baseline(runtime, evidence, python):
    before = protected_hashes()
    runtime.mkdir(parents=True, exist_ok=False)
    source = source_snapshot(runtime / "source")
    env = isolated_environment(runtime, source)
    report = {"captured_utc": datetime.now(timezone.utc).isoformat(),
              "repository": str(REPO), "runtime_root": str(runtime),
              "head": read_command(["git", "rev-parse", "HEAD"], REPO)["stdout"],
              "branch": read_command(["git", "branch", "--show-current"], REPO)["stdout"],
              "status": read_command(["git", "status", "--short"], REPO)["stdout"],
              "platform": platform.platform(), "interpreter": str(python),
              "inherited_environment_names": sorted(os.environ),
              "tests": {"status": "not_run"}, "smoke": {"status": "not_run"}}
    versions = read_command([str(python), "-B", "-c",
        "import json,ssl,sys,cryptography,pytest; from cryptography.hazmat.backends.openssl.backend import backend; print(json.dumps({'python':sys.version,'cryptography':cryptography.__version__,'pytest':pytest.__version__,'python_ssl':ssl.OPENSSL_VERSION,'cryptography_openssl':backend.openssl_version_text()}))"], source, env)
    report["versions"] = json.loads(versions["stdout"]) if versions.get("returncode") == 0 else versions
    try:
        command = [str(python), "-B", str(CHILD), str(runtime), "pytest", "-q",
                   "-p", "no:cacheprovider", "--basetemp", str(runtime / "pytest-tmp"),
                   "--log-file", str(runtime / "pytest-internal.log"),
                   "--junitxml", str(runtime / "pytest.xml")]
        started = time.monotonic()
        result = read_command(command, source, env, timeout=90)
        (runtime / "pytest.log").write_text(json.dumps(result, indent=2), encoding="utf-8")
        report["tests"] = {"status": "passed" if result["returncode"] == 0 else "failed",
                           "returncode": result["returncode"], "command": command,
                           "duration_seconds": round(time.monotonic() - started, 3)}
        import xml.etree.ElementTree as ET
        suites = ET.parse(runtime / "pytest.xml").getroot()
        suite = suites.find("testsuite")
        tests = {key: int(suite.attrib[key]) for key in ("tests", "failures", "errors", "skipped")}
        report["tests"].update({**tests, "summary": result["stdout"].splitlines()[-1]})
        with isolated_stack(runtime / "stack", source=source, python=python) as stack:
            stack.start_device()
            stack.wait_for(lambda: len(stack.readings()) >= 3, "three stored readings")
            # Stop generator before taking final business and health snapshots.
            stack.processes["device"].terminate()
            stack.processes["device"].wait(timeout=5)
            readings = stack.readings()
            cloud = stack.cloud_health()
            gateway = stack.gateway_health()
            sequences = [reading["sequence"] for reading in readings]
            passed = (len(readings) >= 3 and sequences == list(range(1, len(readings) + 1))
                      and cloud["stored_readings"] == len(readings)
                      and gateway["cloud_connected"]
                      and all(r["device_id"] == stack.device_id for r in readings))
            report["smoke"] = {"status": "passed" if passed else "failed",
                               "cloud_reading_count": len(readings), "readings": readings,
                               "cloud_health": cloud, "gateway_health": gateway,
                               "bind_host": "127.0.0.1", "ports": {
                                   "cloud": stack.cloud_port, "gateway": stack.gateway_port,
                                   "cloud_health": stack.cloud_health_port,
                                   "gateway_health": stack.gateway_health_port},
                               "health_launch_adapter": "child-only loopback bind override",
                               "trust_anchor_source": "fresh locally generated cloud.key; not logs",
                               "data_store": "existing in-memory ReadingStore; no durability claim"}
        report["smoke"]["all_children_stopped"] = all(
            p.poll() is not None for p in stack.processes.values())
    except Exception as exc:
        report["execution_error"] = type(exc).__name__ + ": " + str(exc)
    finally:
        after = protected_hashes()
        report["preservation"] = {"before": before, "after": after,
                                  "changed": sorted(p for p in before.keys() | after.keys()
                                                    if before.get(p) != after.get(p))}
    report["docker"] = {
        "version": read_command(["docker", "version", "--format", "{{json .}}"]),
        "compose_version": read_command(["docker", "compose", "version", "--short"]),
        "runtime_validation": "not_run: no builds, containers, volumes or original .env touched"}
    empty_env = runtime / "empty.env"
    empty_env.write_text("", encoding="utf-8")
    # Docker locates its existing CLI plugins under the user's profile. This
    # read-only config check needs that path; application child env stays scrubbed.
    docker_env = dict(env)
    for name in ("USERPROFILE", "APPDATA", "LOCALAPPDATA", "PROGRAMDATA",
                 "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMW6432", "SYSTEMDRIVE"):
        if name in os.environ:
            docker_env[name] = os.environ[name]
    report["docker"]["isolated_compose_config"] = read_command([
        "docker", "compose", "--env-file", str(empty_env), "--project-directory",
        str(source), "-f", str(source / "docker-compose.yml"), "config", "--quiet"], source, docker_env)
    bindings = []
    for log in (runtime / "stack").glob("*.log"):
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("A01_BIND "):
                bindings.append(json.loads(line.removeprefix("A01_BIND ")))
    report["smoke"]["observed_bind_addresses"] = bindings
    report["smoke"]["all_observed_binds_loopback"] = bool(bindings) and all(
        address[0] == "127.0.0.1" for address in bindings)
    write_json(evidence / "result.json", report)
    # Logs remain outside the checkout. The committed evidence contains only
    # versions, counts, generated sensor data and public fingerprint metadata.
    print(json.dumps({"evidence": str(evidence / "result.json"),
                      "tests": report["tests"]["status"],
                      "smoke": report["smoke"]["status"],
                      "preserved": not report["preservation"]["changed"]}))
    return 0 if (report["tests"]["status"] == "passed"
                 and report["smoke"]["status"] == "passed"
                 and report["smoke"].get("all_observed_binds_loopback")
                 and not report["preservation"]["changed"]) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path,
                        default=REPO / "docs/phase-a/evidence/baseline")
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    if args.runtime_root.resolve().is_relative_to(repo):
        parser.error("runtime must be outside the repository")
    if args.runtime_root.exists():
        parser.error("runtime must be a new directory; existing state is never reused")
    return baseline(args.runtime_root.resolve(), args.evidence_dir.resolve(),
                    args.python.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
