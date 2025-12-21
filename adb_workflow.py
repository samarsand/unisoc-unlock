#!/usr/bin/env python3
import subprocess
import hashlib
import datetime
import os

LOG_DIR = r"C:\SDsave"
LOG_FILE = os.path.join(LOG_DIR, "SDK_Audit.log")

os.makedirs(LOG_DIR, exist_ok=True)


def timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log_entry(message):
    entry = f"{timestamp()} | {message}"
    print(entry)
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()


def adb_command(args, device=None):
    cmd = ["adb"]
    if device:
        cmd += ["-s", device]
    cmd += args
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode()
    except subprocess.CalledProcessError as e:
        log_entry(f"ADB error: {e.output.decode()}")
        return None


def main():
    log_entry("ADB workflow started")

    output = adb_command(["devices"])
    devices = []
    if output:
        for line in output.splitlines()[1:]:
            if line.strip() and "device" in line:
                serial = line.split()[0]
                if not serial.startswith("localhost"):
                    devices.append(serial)

    if not devices:
        log_entry("No physical devices detected")
        return

    target = devices[0]
    log_entry(f"Target device selected: {target}")

    adb_command(["reboot", "bootloader"], device=target)
    log_entry(f"Rebooted {target} into bootloader")

    digest = sha256_file(LOG_FILE)
    log_entry(f"Audit log SHA256: {digest}")

    log_entry("ADB workflow completed")


if __name__ == "__main__":
    main()
