#!/usr/bin/env bash
# Unisoc T618 bootloader ritual runner for WSL
# Usage: sudo ./unlock_relock_ritual.sh unlock|lock

set -euo pipefail

RITUAL_LOG="${HOME}/FoCg.log"
DISTRO="$(. /etc/os-release && echo "${NAME:-WSL-Linux}")"
OPERATION="${1:-}"

timestamp() { date -Iseconds; }
logritual() {
  local level="$1"; shift
  printf "%s | %s | %s\n" "$(timestamp)" "$level" "$*" | tee -a "$RITUAL_LOG"
}

# ---------- Guardrails ----------
if [[ $EUID -ne 0 ]]; then
  logritual "guard" "Run with sudo for clean USB access."
  echo "Usage: sudo $0 unlock|lock"
  exit 1
fi

if [[ "$OPERATION" != "unlock" && "$OPERATION" != "lock" ]]; then
  echo "Usage: sudo $0 unlock|lock"
  exit 2
fi

# ---------- Environment checks ----------
logritual "start" "Bootloader ritual start | op=${OPERATION} | distro=${DISTRO}"

# Check that unisoc_unlock executable is available
if ! command -v unisoc_unlock >/dev/null 2>&1; then
  logritual "error" "unisoc_unlock not found in PATH. Install with: pipx install unisoc-unlock"
  exit 4
fi

logritual "versions" "python=$(python3 --version) | pip=$(pip3 --version)"

# ---------- USB checks ----------
logritual "probe" "Checking USB device presence via lsusb"
if ! lsusb | grep -Ei "Android|Google|Unisoc|Spreadtrum|Fastboot" >/dev/null 2>&1; then
  logritual "warn" "No Android/Fastboot device detected. Ensure usbipd attach --wsl has been run."
  exit 5
fi

# ---------- Operation ----------
logritual "action" "Running unisoc_unlock ${OPERATION}"
set +e
unisoc_unlock "${OPERATION}"
rc=$?
set -e

if [[ $rc -ne 0 ]]; then
  logritual "error" "Operation failed with exit code ${rc}."
  logritual "next" "If device rebooted, re-run usbipd attach --wsl --busid <BUS_ID> in Windows."
  exit $rc
fi

logritual "confirm" "On RG405M: press Home/Back to confirm even if screen says 'Volume Down'."
logritual "success" "Operation complete | status=${OPERATION}ed"
