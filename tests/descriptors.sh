#!/bin/sh
# The descriptors Eider builds (what server reflection serves) against protoc's.
#
#   sh tests/descriptors.sh      (needs python3 with `pip install protobuf grpcio-tools`, else `skip`)
#
# tests/descriptor_test.ei emits the FileDescriptorProto of each file of the generated BuildKit control modules; tests/golden/check_descriptors.py
# has protoc build them for the same .proto files (tests/golden/protos) and compares them (options and the order of nested types aside).
here=$(cd "$(dirname "$0")/.." && pwd -P)
cd "$here" || exit 1
py=${PYTHON:-python3}
if ! $py -c 'import google.protobuf, grpc_tools' >/dev/null 2>&1; then
  echo "skip descriptors (protoc): python3 with protobuf and grpcio-tools is not installed"
  exit 0
fi
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
mkdir -p "$T/inc/github.com/moby/buildkit"
cp -r tests/golden/protos/api tests/golden/protos/solver tests/golden/protos/sourcepolicy "$T/inc/github.com/moby/buildkit/"
cp -r tests/golden/protos/google "$T/inc/"
. scripts/env.sh
ei run tests/descriptor_test.ei emit > "$T/eider.txt" 2>&1 || { echo "FAIL descriptors: eider"; head -5 "$T/eider.txt"; exit 1; }
if out=$($py tests/golden/check_descriptors.py "$T/inc" "$T/eider.txt" github.com/moby/buildkit/api/services/control/control.proto 2>&1); then echo "ok   descriptors: $out"; else echo "FAIL descriptors: $out"; exit 1; fi
