import pyarrow as pa

S = pa.string()
FILE = pa.schema([(x, S) for x in ("repository", "commit", "path", "language", "content", "content_hash")])
COMMON = [(x, S) for x in ("repository", "path", "language", "content_hash", "extractor_version")]
SCHEMAS = {
    "symbols": pa.schema(COMMON + [(x, S) for x in ("symbol_id", "name", "kind", "qualified_name")] + [("start_line", pa.int32()), ("end_line", pa.int32())]),
    "imports": pa.schema(COMMON + [(x, S) for x in ("import_id", "target")] + [("line", pa.int32())]),
    "annotations": pa.schema(COMMON + [(x, S) for x in ("annotation_id", "symbol_id", "name", "arguments")] + [("line", pa.int32())]),
    "relationships": pa.schema(COMMON + [(x, S) for x in ("source_id", "target", "kind", "resolution")] + [("line", pa.int32())]),
    "files": pa.schema(COMMON),
}
ACL = pa.schema([(x, S) for x in ("repository", "path", "language", "subject_id", "subject", "finding", "status", "evidence")] + [("line", pa.int32())])
