# Changelog

eider-proto's versions (semver). Before 1.0 the MAJOR.MINOR is the Eider toolchain's it goes
with (`eider` in eider.toml), the PATCH its own.

## 0.8.0

For Eider 0.8: the version and the `eider` series move to 0.8 with the toolchain; no source changes.

## 0.7.1

Recursive messages (eider-proto#1 follow-up; eider-lang#249). Generated modules for them need Eider 0.7.11 (`Serialize` and `Deserialize` for `Box[T]`); the library itself builds on 0.7.10.

- **`proto/gen`**: a message that contains itself by value (directly, through a oneof, or through other messages: `message Node { Node next = 1; }`) is generated instead of refused. The field that closes the cycle is `Option[Box[Node]]`, a oneof member `Box[Node]`; the other fields are as before (the DFS in declaration order picks the field, so the output is stable). Repeated fields and maps are unchanged. Test: `tests/recursive_test.ei` (generated `tests/recursive/tree.ei`): a chain, a tree, a oneof that holds a node, a cycle through two messages; the bytes parse with Google's protobuf for Python. `tests/cycle_test` now lists what is boxed.

## 0.7.0

First version (eider-lang#247): the proto3 wire format as a `std/serial` format with unknown fields kept (`proto`), a `.proto` parser (`proto/parser`), a generator of Eider types and registries (`proto/gen`, `proto/wkt`, `tools/protoc_eider.ei`). `proto/gen` exposes a `Resolver` for generators of service stubs (eider-rpc's `rpc/gen`) and generates `unknown_fields` with `@[serial(default)]` so JSON decoding does not need it. A message that contains itself by value (directly, through a oneof or through other messages) is refused with the cycle named (`tests/cycle_test`): Eider records cannot contain themselves and `std/serial` cannot yet derive `Box[T]` (eider-lang#249); repeated fields and maps are fine. `proto/descriptor` builds the serialized `FileDescriptorProto` of a parsed file, and the generated modules have `file_desc()` / `add_descs` for server reflection (identical to protoc's for the BuildKit control files: `tests/descriptors.sh`). Verified against Google's protobuf for Python on 498 messages of BuildKit's control, ops, policy, worker and status protos, both directions (`tests/golden*`).
