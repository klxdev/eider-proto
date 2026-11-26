#!/usr/bin/env python3
"""Compares the FileDescriptorProtos Eider builds (tests/descriptor_test.ei emit) with protoc's for the same files.

  python3 check_descriptors.py <include dir> <eider.txt> <root.proto relative to the include dir>...

protoc (grpc_tools) writes a descriptor set with its imports; every file of `eider.txt` (`<name> <hex>` lines) is parsed as a
FileDescriptorProto and compared with protoc's by the end of its name. Options (go_package, gogoproto, packed...) and the order
of nested types are not compared: names, numbers, labels, types, type names, oneofs, proto3_optional, json_name, maps (map_entry), enums,
services, methods and streaming flags are."""
import subprocess, sys, tempfile, os
from google.protobuf import descriptor_pb2

inc, eider, *roots = sys.argv[1:]
with tempfile.TemporaryDirectory() as t:
    ds = os.path.join(t, "ds.bin")
    subprocess.check_call([sys.executable, "-m", "grpc_tools.protoc", "-I" + inc, "--include_imports", "--descriptor_set_out=" + ds] + roots)
    fds = descriptor_pb2.FileDescriptorSet()
    fds.ParseFromString(open(ds, "rb").read())

def norm_msg(m):
    if not (m.HasField("options") and m.options.map_entry):
        m.ClearField("options")
    else:
        keep = m.options.map_entry
        m.ClearField("options"); m.options.map_entry = keep
    for f in m.field: f.ClearField("options")
    for e in m.enum_type: norm_enum(e)
    for n in m.nested_type: norm_msg(n)
    nested = sorted(m.nested_type, key=lambda x: x.name)
    del m.nested_type[:]
    m.nested_type.extend(nested)
    for o in m.oneof_decl: o.ClearField("options")

def norm_enum(e):
    e.ClearField("options")
    for v in e.value: v.ClearField("options")

def norm(f):
    f.ClearField("options"); f.ClearField("source_code_info")
    for m in f.message_type: norm_msg(m)
    for e in f.enum_type: norm_enum(e)
    for s in f.service:
        s.ClearField("options")
        for m in s.method: m.ClearField("options")
    ms = sorted(f.message_type, key=lambda x: x.name)
    del f.message_type[:]
    f.message_type.extend(ms)

def tail(n):
    for pre in ("github.com/moby/buildkit/", "github.com/tonistiigi/fsutil/", "github.com/planetscale/vtprotobuf/"):
        if n.startswith(pre): return n[len(pre):]
    return n

theirs = {tail(f.name): f for f in fds.file}
bad = 0
n = 0
for line in open(eider).read().splitlines():
    if not line.strip(): continue
    name, hexs = line.split()
    a = descriptor_pb2.FileDescriptorProto()
    a.ParseFromString(bytes.fromhex(hexs))
    b = theirs.get(tail(name))
    if b is None:
        print("no protoc descriptor for", name); bad += 1; continue
    norm(a); norm(b)
    a.name = b.name = tail(name)
    a_deps = [tail(d) for d in a.dependency]
    b_deps = [tail(d) for d in b.dependency]
    a.ClearField("dependency"); b.ClearField("dependency")
    a.dependency.extend(a_deps); b.dependency.extend(b_deps)
    n += 1
    if a != b:
        bad += 1
        print("DIFFERENT", name)
        import difflib
        d = list(difflib.unified_diff(str(b).splitlines(), str(a).splitlines(), "protoc", "eider", lineterm="", n=1))
        print("\n".join(d[:30]))
print(f"{n} descriptors compared, {bad} different")
sys.exit(1 if bad else 0)
