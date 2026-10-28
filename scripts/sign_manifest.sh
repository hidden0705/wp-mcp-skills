#!/usr/bin/env bash
# Sign a feed manifest with the offline RSA key.
#
# Usage: sign_manifest.sh dist/manifest.json dist/manifest.json.sig
# Key:   WPMCP_SKILLS_SIGNING_KEY_FILE (default: $RUNNER_TEMP/signing-key.pem)
set -euo pipefail

manifest="${1:?usage: sign_manifest.sh <manifest.json> <output.sig>}"
out="${2:?usage: sign_manifest.sh <manifest.json> <output.sig>}"
key="${WPMCP_SKILLS_SIGNING_KEY_FILE:-${RUNNER_TEMP:-/tmp}/signing-key.pem}"

if [ ! -s "$key" ]; then
	echo "signing key not found at $key" >&2
	exit 1
fi

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

openssl dgst -sha256 -sign "$key" -out "$tmp" "$manifest"
base64 -w0 "$tmp" >"$out"
echo "signed $(basename "$manifest") -> $(basename "$out") ($(wc -c <"$out") bytes base64)"
