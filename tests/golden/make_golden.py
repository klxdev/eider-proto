#!/usr/bin/env python3
"""Golden files for eider-proto from the reference implementation (Google's protobuf for Python).

  python3 make_golden.py gen   <proto include dir> <generated python dir> > python.txt
  python3 make_golden.py check <proto include dir> <generated python dir> python.txt eider.txt

`gen` writes `<full message name> <hex>` lines: random populated instances (every field kind, nested messages, repeated,
packed, maps, oneofs, unknown fields) of the BuildKit control, ops, policy, worker and status messages, from a fixed seed.
`check` parses what Eider wrote after decoding and re-encoding each line (`eider.txt`) with the same classes and compares
it with the original message: the Eider encoder's output is accepted by the reference parser and means the same.
Needs `pip install protobuf grpcio-tools`; the generated python is `python -m grpc_tools.protoc -I<include> --python_out=<dir> ...`."""
import importlib, random, sys
sys.path.insert(0, sys.argv[3])
for d in ("github", "github/com"):
    import os
    os.makedirs(os.path.join(sys.argv[3], d), exist_ok=True)
    open(os.path.join(sys.argv[3], d, "__init__.py"), "a").close()
from google.protobuf import descriptor_pool, message_factory
from google.protobuf.descriptor import FieldDescriptor as F
mods = ["github.com.moby.buildkit.api.services.control.control_pb2", "github.com.moby.buildkit.solver.pb.ops_pb2",
        "github.com.moby.buildkit.sourcepolicy.pb.policy_pb2", "github.com.moby.buildkit.api.types.worker_pb2", "google.rpc.status_pb2"]
loaded = [importlib.import_module(m) for m in mods]
pool = descriptor_pool.Default()
classes = {}
def cls(desc):
    return message_factory.GetMessageClass(desc)
def all_messages():
    out = []
    for m in loaded:
        def walk(d):
            if d.GetOptions().map_entry: return
            out.append(d)
            for n in d.nested_types: walk(n)
        for d in m.DESCRIPTOR.message_types_by_name.values(): walk(d)
    return out

def scalar(r, f):
    t = f.type
    if t in (F.TYPE_INT32, F.TYPE_SINT32, F.TYPE_SFIXED32): return r.choice([0, 1, -1, 127, 128, -2**31, 2**31 - 1, r.randint(-1000, 1000)])
    if t in (F.TYPE_INT64, F.TYPE_SINT64, F.TYPE_SFIXED64): return r.choice([0, 1, -1, -2**63, 2**63 - 1, r.randint(-10**12, 10**12)])
    if t in (F.TYPE_UINT32, F.TYPE_FIXED32): return r.choice([0, 1, 2**32 - 1, r.randint(0, 100000)])
    if t in (F.TYPE_UINT64, F.TYPE_FIXED64): return r.choice([0, 1, 2**64 - 1, r.randint(0, 10**15)])
    if t == F.TYPE_BOOL: return r.choice([True, False])
    if t == F.TYPE_DOUBLE: return r.choice([0.0, 1.5, -2.25, 1e300, r.random()])
    if t == F.TYPE_FLOAT: return r.choice([0.0, 0.5, -3.0, 1024.0])
    if t == F.TYPE_STRING: return r.choice(["", "a", "héllo wörld", "x" * r.randint(1, 200), "日本語"])
    if t == F.TYPE_BYTES: return bytes(r.randint(0, 255) for _ in range(r.randint(0, 40)))
    if t == F.TYPE_ENUM: return r.choice([v.number for v in f.enum_type.values] + [r.randint(0, 20)])
    raise Exception(t)

def fill(r, msg, depth):
    d = msg.DESCRIPTOR
    chosen_oneofs = {}
    for f in d.fields:
        if f.containing_oneof is not None:
            if f.containing_oneof.name in chosen_oneofs and chosen_oneofs[f.containing_oneof.name] != f.name: continue
            if r.random() < 0.5: continue
            chosen_oneofs[f.containing_oneof.name] = f.name
        elif r.random() < 0.3: continue
        is_map = f.message_type is not None and f.message_type.GetOptions().map_entry
        if is_map:
            k, v = f.message_type.fields_by_name["key"], f.message_type.fields_by_name["value"]
            m = getattr(msg, f.name)
            for _ in range(r.randint(0, 3)):
                key = scalar(r, k)
                if v.type == F.TYPE_MESSAGE:
                    if depth > 0: fill(r, m[key], depth - 1) if r.random() < 0.8 else m[key].SetInParent()
                    else: m[key].SetInParent()
                else: m[key] = scalar(r, v)
        elif f.is_repeated:
            for _ in range(r.randint(0, 4)):
                if f.type == F.TYPE_MESSAGE:
                    if depth > 0: fill(r, getattr(msg, f.name).add(), depth - 1)
                    else: getattr(msg, f.name).add()
                else: getattr(msg, f.name).append(scalar(r, f))
        elif f.type == F.TYPE_MESSAGE:
            if depth > 0: fill(r, getattr(msg, f.name), depth - 1)
            else: getattr(msg, f.name).SetInParent()
        else:
            setattr(msg, f.name, scalar(r, f))

def varint(n):
    out = bytearray()
    while n >= 128: out.append((n & 127) | 128); n >>= 7
    out.append(n); return bytes(out)

def gen():
    r = random.Random(20261126)
    for d in all_messages():
        c = cls(d)
        for i in range(6):
            m = c()
            fill(r, m, 3)
            data = m.SerializeToString()
            if i == 5:  # an unknown field of each wire type, which a reader that does not know it must keep
                data += varint((900 << 3) | 0) + varint(12345) + varint((901 << 3) | 2) + varint(3) + b"abc" + varint((902 << 3) | 5) + b"\x01\x02\x03\x04" + varint((903 << 3) | 1) + b"\x01\x02\x03\x04\x05\x06\x07\x08"
            print(d.full_name, data.hex() if data else "-")

def check(golden, eider):
    by = {d.full_name: cls(d) for d in all_messages()}
    a = [l.split() for l in open(golden).read().splitlines() if l.strip()]
    b = [l.split() for l in open(eider).read().splitlines() if l.strip()]
    assert len(a) == len(b), (len(a), len(b))
    bad = 0
    for (n1, h1), (n2, h2) in zip(a, b):
        assert n1 == n2
        m1, m2 = by[n1](), by[n2]()
        m1.ParseFromString(b"" if h1 == "-" else bytes.fromhex(h1))
        m2.ParseFromString(b"" if h2 == "-" else bytes.fromhex(h2))
        if m1 != m2:
            bad += 1
            if bad < 5: print("DIFFERENT", n1)
    print(f"{len(a)} messages, {bad} different")
    sys.exit(1 if bad else 0)

if sys.argv[1] == "gen": gen()
else: check(sys.argv[4], sys.argv[5])
