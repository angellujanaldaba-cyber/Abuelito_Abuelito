#!/bin/bash
set -euo pipefail
cd "$CODEBUILD_SRC_DIR"
test "$(uname -m)" = aarch64
version=v1.37.0
curl --fail --location --retry 3 "https://dl.k8s.io/release/$version/bin/linux/arm64/kubectl" -o /tmp/kubectl
curl --fail --location --retry 3 "https://dl.k8s.io/release/$version/bin/linux/arm64/kubectl.sha256" -o /tmp/kubectl.sha256
printf '%s  /tmp/kubectl\n' "$(cat /tmp/kubectl.sha256)" | sha256sum --check
install -m 0755 /tmp/kubectl /usr/local/bin/kubectl
python3 deploy/scripts/codebuild_execute.py
