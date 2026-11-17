#!/usr/bin/env bash
# One-time setup on a fresh RunPod pod (Ubuntu): Chrome, Node, ffmpeg, Vulkan, then the repo.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
LOG=/workspace/setup.log
exec > >(tee -a "$LOG") 2>&1

apt-get update -q
apt-get install -y -q --no-install-recommends ca-certificates curl gnupg git ffmpeg \
  libvulkan1 vulkan-tools mesa-utils fonts-liberation fonts-dejavu-core

if ! command -v node >/dev/null; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y -q nodejs
fi

if ! command -v google-chrome >/dev/null; then
  curl -fsSL -o /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
  apt-get install -y -q /tmp/chrome.deb
fi

# NVIDIA's Vulkan ICD is not always registered inside containers
if [ ! -e /usr/share/vulkan/icd.d/nvidia_icd.json ] && [ ! -e /etc/vulkan/icd.d/nvidia_icd.json ]; then
  mkdir -p /etc/vulkan/icd.d
  cat > /etc/vulkan/icd.d/nvidia_icd.json <<'J'
{ "file_format_version": "1.0.0", "ICD": { "library_path": "libGLX_nvidia.so.0", "api_version": "1.3" } }
J
fi

cd /workspace
if [ -d whyshorts/.git ]; then git -C whyshorts pull --ff-only; else git clone --depth 1 https://github.com/123boko/whyshorts; fi
cd whyshorts && npm ci --silent
echo SETUP_DONE
