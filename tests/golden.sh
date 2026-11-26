#!/bin/sh
# The other direction of tests/golden_test.ei: what Eider writes is read by the reference implementation.
#
#   sh tests/golden.sh      (needs python3 with `pip install protobuf grpcio-tools`, else `skip`)
#
# Generates Python from the .proto files in tests/golden/protos (a copy of the BuildKit ones), has Eider decode and
# re-encode each of the 498 golden messages in tests/golden/python.txt, and has Python parse every re-encoding and
# compare it with the original message (unknown fields included). Regenerate the golden file with
# `python3 tests/golden/make_golden.py gen <include> <python dir> > tests/golden/python.txt`.
here=$(cd "$(dirname "$0")/.." && pwd -P)
cd "$here" || exit 1
py=${PYTHON:-python3}
if ! $py -c 'import google.protobuf, grpc_tools' >/dev/null 2>&1; then
  echo "skip golden (reference parser): python3 with protobuf and grpcio-tools is not installed"
  exit 0
fi
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
mkdir -p "$T/inc/github.com/moby/buildkit" "$T/py"
cp -r tests/golden/protos/api tests/golden/protos/solver tests/golden/protos/sourcepolicy "$T/inc/github.com/moby/buildkit/"
cp -r tests/golden/protos/google "$T/inc/"
$py -m grpc_tools.protoc -I"$T/inc" --python_out="$T/py" github.com/moby/buildkit/api/services/control/control.proto github.com/moby/buildkit/solver/pb/ops.proto github.com/moby/buildkit/api/types/worker.proto github.com/moby/buildkit/sourcepolicy/pb/policy.proto google/rpc/status.proto || exit 1
. scripts/env.sh
ei run tests/golden_test.ei emit > "$T/eider.txt" 2>&1 || { echo "FAIL golden: eider"; head -5 "$T/eider.txt"; exit 1; }
if out=$($py tests/golden/make_golden.py check "$T/inc" "$T/py" tests/golden/python.txt "$T/eider.txt" 2>&1); then echo "ok   golden: $out"; else echo "FAIL golden: $out"; exit 1; fi
