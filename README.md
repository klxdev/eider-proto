# eider-proto

Protocol Buffers (proto3) for [Eider](https://github.com/klxdev/eider-lang), in pure Eider: no capability, and it depends on nothing (no HTTP, no RPC).

- **`proto`**: the wire format as a `std/serial` format. Varints and zigzag, fixed32/64, length-delimited fields, packed repeated fields, maps, oneofs, enums, nested messages; **unknown fields are kept** through a decode and an encode. A type that is `@[derive(Serialize, Deserialize)]` goes to bytes with `proto.encode(registry, "pkg.Message", x)` and back with `proto.decode[T](registry, "pkg.Message", bytes)`. Limits on nesting, size and elements; malformed input is an `Err` that says where.
- **`proto/parser`**: a `.proto` parser (proto3, and the proto2 syntax found in imported files): messages, nested types, `map`, `oneof`, `optional`, enums, `service`/`rpc` with streaming, `reserved`, options. gogoproto and every other option are tolerated.
- **`proto/gen`**: writes Eider modules from parsed files: record types with `@[derive(Serialize, Deserialize)]`, enums, oneof enums, the `Registry` of the schema, `encode_<msg>` / `decode_<msg>`. `proto/wkt` has `Any`, `Timestamp`, `Duration`, `Empty`, `FieldMask` and the wrappers.
- **`examples/protoc/protoc_eider.ei`**: the command line: `eider run examples/protoc/protoc_eider.ei <out dir> <include dir> <strip prefix|-> <package prefix|-> <root.proto>...`.

How proto3 maps to Eider types is in the header of `proto.ei` and `gen.ei` (enum fields are `i32`, `float` is `f64`, a map is `Map[String, V]` with integer keys as text, a singular message is an `Option`).

## Tests

`tests/proto_test` (wire primitives, every field kind, merging, unknown fields, malformed input), `tests/parser_test`, `tests/session_test` (the session services: filesync, auth, secrets, sshforward, upload, exporter and fsutil's wire types), `tests/buildkit_test` (types generated from BuildKit's `control.proto` and what it imports, in `tests/buildkit/`), and **`tests/golden_test`**: 498 random instances of BuildKit's control, ops, policy, worker and status messages written by Google's protobuf for Python (`tests/golden/python.txt`) decode and re-encode without losing a byte; `tests/golden.sh` has the reference parser read what Eider wrote and compare it with the originals (498 of 498 equal).

Used by (planned): eider-rpc (gRPC).
