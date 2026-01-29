#!/usr/bin/env python3
import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


EXAMPLE_YAML = """\
# bootstrap.yml (пример с няколко venv-а)
apt:
  - name: git
  - name: curl
  - name: python3-venv
  - name: python3-pip

snap:
  - name: btop
  - name: code
    classic: true

pipx:
  - name: httpie

venvs:
  - name: "app"
    base_dir: "venv"      # -> ./venv/app
    python: "python3"
    pip:
      - name: django
        version: "5.0.10"
      - name: gunicorn

  - name: "tools"
    base_dir: "venv"      # -> ./venv/tools
    python: "python3"
    pip:
      - name: pre-commit
        version: "3.7.1"
      - name: black

commands:
  - name: "oh-my-zsh (пример)"
    check: "test -d ~/.oh-my-zsh"
    install: "sh -c \\"$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)\\""

copy:
  - src: "/path/from/file1.txt"
    dst: "/path/to/file1.txt"
  - src: "local/file2.conf"
    dst: "/etc/myapp/file2.conf"
    overwrite: true
"""

EXAMPLE_JSON = """\
{
  "apt": [
    { "name": "git" },
    { "name": "curl" },
    { "name": "python3-venv" },
    { "name": "python3-pip" }
  ],
  "snap": [
    { "name": "btop" },
    { "name": "code", "classic": true }
  ],
  "pipx": [
    { "name": "httpie" }
  ],
  "venvs": [
    {
      "name": "app",
      "base_dir": "venv",
      "python": "python3",
      "pip": [
        { "name": "django", "version": "5.0.10" },
        { "name": "gunicorn" }
      ]
    },
    {
      "name": "tools",
      "base_dir": "venv",
      "python": "python3",
      "pip": [
        { "name": "pre-commit", "version": "3.7.1" },
        { "name": "black" }
      ]
    }
  ],
  "commands": [
    {
      "name": "oh-my-zsh (пример)",
      "check": "test -d ~/.oh-my-zsh",
      "install": "sh -c \\"$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)\\""
    }
  ],
  "copy": [
    {
      "src": "/path/from/file1.txt",
      "dst": "/path/to/file1.txt"
    },
    {
      "src": "local/file2.conf",
      "dst": "/etc/myapp/file2.conf",
      "overwrite": true
    }
  ]
}
"""


@dataclass
class Result:
    name: str
    action: str   # ok | installed | copied | skipped | failed | planned
    detail: str = ""


def run(cmd: List[str], *, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        check=check,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def apt_is_installed(pkg: str) -> bool:
    try:
        run(["dpkg", "-s", pkg], check=True, capture=True)
        return True
    except subprocess.CalledProcessError:
        return False


def snap_is_installed(name: str) -> bool:
    try:
        out = run(["snap", "list", name], check=True, capture=True).stdout or ""
        return name in out
    except subprocess.CalledProcessError:
        return False


def ensure_apt_update_once(state: Dict[str, Any], *, dry_run: bool) -> None:
    if state.get("apt_updated"):
        return
    if dry_run:
        print("==> [DRY] sudo apt-get update")
        state["apt_updated"] = True
        return
    print("==> apt update")
    run(["sudo", "apt-get", "update"])
    state["apt_updated"] = True


def install_apt(items: List[Dict[str, Any]], *, dry_run: bool) -> List[Result]:
    results: List[Result] = []
    state = {"apt_updated": False}

    for it in items or []:
        pkg = (it or {}).get("name")
        if not pkg:
            continue

        if apt_is_installed(pkg):
            print(f"[OK]  apt  {pkg} (already installed)")
            results.append(Result(pkg, "ok", "already installed"))
            continue

        ensure_apt_update_once(state, dry_run=dry_run)
        if dry_run:
            print(f"[..]  apt  {pkg} (would install)")
            results.append(Result(pkg, "planned", "would install"))
            continue

        print(f"[..]  apt  {pkg} (installing)")
        try:
            run(["sudo", "apt-get", "install", "-y", pkg])
            print(f"[OK]  apt  {pkg} (installed)")
            results.append(Result(pkg, "installed", "installed"))
        except subprocess.CalledProcessError as e:
            print(f"[ERR] apt  {pkg} (failed)")
            results.append(Result(pkg, "failed", str(e)))

    return results


def install_snap(items: List[Dict[str, Any]], *, dry_run: bool) -> List[Result]:
    results: List[Result] = []
    if not items:
        return results

    if shutil.which("snap") is None:
        for it in items:
            name = (it or {}).get("name", "?")
            print(f"[ERR] snap {name} (snap not found)")
            results.append(Result(name, "failed", "snap not found"))
        return results

    for it in items:
        name = (it or {}).get("name")
        if not name:
            continue
        classic = bool((it or {}).get("classic", False))

        if snap_is_installed(name):
            print(f"[OK]  snap {name} (already installed)")
            results.append(Result(name, "ok", "already installed"))
            continue

        cmd = ["sudo", "snap", "install", name] + (["--classic"] if classic else [])
        if dry_run:
            print(f"[..]  snap {name} (would install: {' '.join(cmd)})")
            results.append(Result(name, "planned", "would install"))
            continue

        print(f"[..]  snap {name} (installing)")
        try:
            run(cmd)
            print(f"[OK]  snap {name} (installed)")
            results.append(Result(name, "installed", "installed"))
        except subprocess.CalledProcessError as e:
            print(f"[ERR] snap {name} (failed)")
            results.append(Result(name, "failed", str(e)))

    return results


def ensure_pipx(*, dry_run: bool) -> bool:
    if shutil.which("pipx"):
        return True
    if dry_run:
        print("[..]  pipx (would install via apt: sudo apt-get install -y pipx)")
        return False
    print("[..]  pipx (installing via apt)")
    try:
        run(["sudo", "apt-get", "update"])
        run(["sudo", "apt-get", "install", "-y", "pipx"])
        run(["pipx", "ensurepath"], check=False)
        return shutil.which("pipx") is not None
    except subprocess.CalledProcessError:
        return False


def pipx_is_installed(name: str) -> bool:
    if shutil.which("pipx") is None:
        return False
    out = run(["pipx", "list"], check=True, capture=True).stdout or ""
    return f"package {name} " in out or f"package {name}\n" in out


def install_pipx(items: List[Dict[str, Any]], *, dry_run: bool) -> List[Result]:
    results: List[Result] = []
    if not items:
        return results

    have_pipx = ensure_pipx(dry_run=dry_run)
    if not have_pipx and not dry_run:
        for it in items:
            name = (it or {}).get("name", "?")
            print(f"[ERR] pipx {name} (pipx missing)")
            results.append(Result(name, "failed", "pipx missing"))
        return results

    for it in items:
        name = (it or {}).get("name")
        if not name:
            continue

        if have_pipx and pipx_is_installed(name):
            print(f"[OK]  pipx {name} (already installed)")
            results.append(Result(name, "ok", "already installed"))
            continue

        if dry_run:
            print(f"[..]  pipx {name} (would install)")
            results.append(Result(name, "planned", "would install"))
            continue

        print(f"[..]  pipx {name} (installing)")
        try:
            run(["pipx", "install", name])
            print(f"[OK]  pipx {name} (installed)")
            results.append(Result(name, "installed", "installed"))
        except subprocess.CalledProcessError as e:
            print(f"[ERR] pipx {name} (failed)")
            results.append(Result(name, "failed", str(e)))

    return results


def ensure_venv(venv_cfg: Dict[str, Any], *, dry_run: bool) -> Optional[Dict[str, str]]:
    name = str(venv_cfg.get("name") or "").strip()
    if not name:
        print("[SKIP] venv (missing name)")
        return None

    base_dir = str(venv_cfg.get("base_dir") or "venv").strip()
    py = str(venv_cfg.get("python") or "python3").strip()

    venv_path = Path.cwd() / base_dir / name
    venv_python = venv_path / "bin" / "python"

    if venv_python.exists():
        print(f"[OK]  venv {venv_path} (already exists)")
        return {"path": str(venv_path), "python": str(venv_python)}

    if dry_run:
        print(f"[..]  venv {venv_path} (would create using: {py} -m venv {venv_path})")
        return {"path": str(venv_path), "python": str(venv_python)}

    print(f"[..]  venv {venv_path} (creating)")
    run([py, "-m", "venv", str(venv_path)])
    print(f"[OK]  venv {venv_path} (created)")
    return {"path": str(venv_path), "python": str(venv_python)}


def pip_in_venv_is_installed(venv_python: str, name: str, version: Optional[str]) -> bool:
    try:
        out = run([venv_python, "-m", "pip", "show", name], check=True, capture=True).stdout or ""
    except subprocess.CalledProcessError:
        return False

    if not version:
        return True

    for line in out.splitlines():
        if line.lower().startswith("version:"):
            installed_ver = line.split(":", 1)[1].strip()
            return installed_ver == version
    return False


def install_pip_into_venv(pip_items: List[Dict[str, Any]], venv_python: str, venv_label: str, *, dry_run: bool) -> List[Result]:
    results: List[Result] = []
    if not pip_items:
        return results

    if not dry_run:
        # ensure pip exists inside venv
        try:
            run([venv_python, "-m", "pip", "--version"], capture=True)
        except subprocess.CalledProcessError:
            run([venv_python, "-m", "ensurepip", "--upgrade"])

    for it in pip_items:
        name = (it or {}).get("name")
        if not name:
            continue
        version = (it or {}).get("version")
        spec = f"{name}=={version}" if version else name

        if pip_in_venv_is_installed(venv_python, name, version):
            msg = "already installed" if not version else f"already installed ({version})"
            print(f"[OK]  pip  {spec} (venv: {venv_label}, {msg})")
            results.append(Result(f"{venv_label}:{spec}", "ok", msg))
            continue

        if dry_run:
            print(f"[..]  pip  {spec} (would install into venv: {venv_label})")
            results.append(Result(f"{venv_label}:{spec}", "planned", "would install"))
            continue

        print(f"[..]  pip  {spec} (installing into venv: {venv_label})")
        try:
            run([venv_python, "-m", "pip", "install", spec])
            print(f"[OK]  pip  {spec} (installed into venv: {venv_label})")
            results.append(Result(f"{venv_label}:{spec}", "installed", "installed"))
        except subprocess.CalledProcessError as e:
            print(f"[ERR] pip  {spec} (failed in venv: {venv_label})")
            results.append(Result(f"{venv_label}:{spec}", "failed", str(e)))

    return results


def install_commands(items: List[Dict[str, Any]], *, dry_run: bool) -> List[Result]:
    results: List[Result] = []
    for it in items or []:
        name = (it or {}).get("name", "command")
        check_cmd = (it or {}).get("check")
        install_cmd = (it or {}).get("install")

        if not check_cmd or not install_cmd:
            print(f"[SKIP] cmd  {name} (missing check/install)")
            results.append(Result(name, "skipped", "missing check/install"))
            continue

        already = False
        try:
            subprocess.run(check_cmd, shell=True, check=True, text=True)
            already = True
        except subprocess.CalledProcessError:
            already = False

        if already:
            print(f"[OK]  cmd  {name} (already installed)")
            results.append(Result(name, "ok", "already installed"))
            continue

        if dry_run:
            print(f"[..]  cmd  {name} (would run install)")
            results.append(Result(name, "planned", "would run install"))
            continue

        print(f"[..]  cmd  {name} (installing)")
        try:
            subprocess.run(install_cmd, shell=True, check=True, text=True)
            print(f"[OK]  cmd  {name} (installed)")
            results.append(Result(name, "installed", "installed"))
        except subprocess.CalledProcessError as e:
            print(f"[ERR] cmd  {name} (failed)")
            results.append(Result(name, "failed", str(e)))

    return results


def copy_files(items: List[Dict[str, Any]], *, dry_run: bool) -> List[Result]:
    results: List[Result] = []
    for it in items or []:
        if not isinstance(it, dict):
            continue

        src = str((it or {}).get("src") or "").strip()
        dst = str((it or {}).get("dst") or "").strip()
        overwrite = bool((it or {}).get("overwrite", False))

        if not src or not dst:
            print("[SKIP] copy (missing src/dst)")
            results.append(Result("copy", "skipped", "missing src/dst"))
            continue

        src_path = Path(src).expanduser()
        dst_path = Path(dst).expanduser()

        if not src_path.exists():
            print(f"[MISS] copy {src_path} (source missing)")
            results.append(Result(str(src_path), "skipped", "missing source"))
            continue

        if src_path.is_dir():
            print(f"[ERR] copy {src_path} (source is a directory)")
            results.append(Result(str(src_path), "failed", "source is a directory"))
            continue

        if dst_path.exists() and not overwrite:
            print(f"[SKIP] copy {src_path} -> {dst_path} (destination exists)")
            results.append(Result(f"{src_path} -> {dst_path}", "skipped", "destination exists"))
            continue

        if dry_run:
            action = "would overwrite" if dst_path.exists() else "would copy"
            print(f"[..]  copy {src_path} -> {dst_path} ({action})")
            results.append(Result(f"{src_path} -> {dst_path}", "planned", action))
            continue

        print(f"[..]  copy {src_path} -> {dst_path} (copying)")
        try:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)
            print(f"[OK]  copy {src_path} -> {dst_path} (copied)")
            detail = "overwritten" if dst_path.exists() and overwrite else "copied"
            results.append(Result(f"{src_path} -> {dst_path}", "copied", detail))
        except Exception as e:
            print(f"[ERR] copy {src_path} -> {dst_path} (failed)")
            results.append(Result(f"{src_path} -> {dst_path}", "failed", str(e)))

    return results


def summarize(results: List[Result]) -> int:
    ok = sum(1 for r in results if r.action == "ok")
    installed = sum(1 for r in results if r.action == "installed")
    copied = sum(1 for r in results if r.action == "copied")
    planned = sum(1 for r in results if r.action == "planned")
    failed = sum(1 for r in results if r.action == "failed")
    skipped = sum(1 for r in results if r.action == "skipped")

    print("\n=== Summary ===")
    print(f"OK:        {ok}")
    print(f"Installed: {installed}")
    print(f"Copied:    {copied}")
    print(f"Planned:   {planned}")
    print(f"Failed:    {failed}")
    print(f"Skipped:   {skipped}")

    return 0 if failed == 0 else 2


def load_config(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")

    # Decide by extension when possible
    ext = path.suffix.lower()
    if ext in (".json",):
        return json.loads(text)

    if ext in (".yml", ".yaml"):
        return load_yaml_or_die(text)

    # Unknown extension: try YAML first, then JSON
    try:
        return load_yaml(text)
    except Exception:
        return json.loads(text)


def load_yaml(text: str) -> Dict[str, Any]:
    import yaml  # type: ignore
    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        raise ValueError("YAML root must be an object/map")
    return data


def load_yaml_or_die(text: str) -> Dict[str, Any]:
    try:
        return load_yaml(text)
    except ImportError:
        # Important: explain the interpreter mismatch you hit
        print("Missing dependency: PyYAML (import yaml).")
        print("You are running:", sys.executable)
        print("Fix options:")
        print("  1) Use system python (sees apt modules): /usr/bin/python3 bootstrap.py ...")
        print("  2) Or install for your current python:  python3 -m pip install --user pyyaml")
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="System bootstrap (apt/snap/pipx + multiple venvs with pip) driven by YAML or JSON config."
    )
    p.add_argument("--config", default="bootstrap.yml", help="Config file path (.yml/.yaml/.json). Default: bootstrap.yml")
    p.add_argument("--dry-run", action="store_true", help="Print what would happen, but do not change anything")
    p.add_argument("--print-example", choices=["yaml", "json"], help="Print an example config and exit")
    return p


def main() -> int:
    args = build_parser().parse_args()

    if args.print_example:
        print(EXAMPLE_YAML if args.print_example == "yaml" else EXAMPLE_JSON)
        return 0

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        print(f"Config not found: {cfg_path}")
        print("Tip: run --print-example yaml or --print-example json")
        return 1

    cfg = load_config(cfg_path)

    results: List[Result] = []
    results += install_apt(cfg.get("apt", []) or [], dry_run=args.dry_run)

    venvs = cfg.get("venvs", []) or []
    if not isinstance(venvs, list):
        print("[ERR] 'venvs' must be a list")
        return 1

    for vcfg in venvs:
        if not isinstance(vcfg, dict):
            continue
        vinfo = ensure_venv(vcfg, dry_run=args.dry_run)
        vname = str(vcfg.get("name") or "").strip() or "venv"
        if not vinfo:
            continue
        results += install_pip_into_venv(vcfg.get("pip", []) or [], vinfo["python"], vname, dry_run=args.dry_run)

    results += install_snap(cfg.get("snap", []) or [], dry_run=args.dry_run)
    results += install_pipx(cfg.get("pipx", []) or [], dry_run=args.dry_run)
    results += install_commands(cfg.get("commands", []) or [], dry_run=args.dry_run)

    copy_items = cfg.get("copy", []) or []
    if not isinstance(copy_items, list):
        print("[ERR] 'copy' must be a list")
        return 1
    results += copy_files(copy_items, dry_run=args.dry_run)

    return summarize(results)


if __name__ == "__main__":
    sys.exit(main())
