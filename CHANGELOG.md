# Changelog

eider-proto's versions (semver). Before 1.0 the MAJOR.MINOR is the Eider toolchain's it goes
with (`eider` in eider.toml), the PATCH its own.

## Unreleased

First version (eider-lang#247): the proto3 wire format as a `std/serial` format with unknown fields kept (`proto`), a `.proto` parser (`proto/parser`), a generator of Eider types and registries (`proto/gen`, `proto/wkt`, `tools/protoc_eider.ei`). `proto/gen` exposes a `Resolver` for generators of service stubs (eider-rpc's `rpc/gen`) and generates `unknown_fields` with `@[serial(default)]` so JSON decoding does not need it. Verified against Google's protobuf for Python on 498 messages of BuildKit's control, ops, policy, worker and status protos, both directions (`tests/golden*`).
