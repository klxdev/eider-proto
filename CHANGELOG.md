# Changelog

eider-proto's versions (semver). Before 1.0 the MAJOR.MINOR is the Eider toolchain's it goes
with (`eider` in eider.toml), the PATCH its own.

## Unreleased

First version (eider-lang#247): the proto3 wire format as a `std/serial` format with unknown fields kept (`proto`), a `.proto` parser (`proto/parser`), a generator of Eider types and registries (`proto/gen`, `proto/wkt`, `tools/protoc_eider.ei`). Verified against Google's protobuf for Python on 498 messages of BuildKit's control, ops, policy, worker and status protos, both directions (`tests/golden*`).
