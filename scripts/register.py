"""Register a selected local input snapshot and the current graph in Trino."""
import argparse
from pathlib import Path
import pyarrow as pa
import trino
from codeatlas.schemas import ACL, FILE, SCHEMAS

p = argparse.ArgumentParser()
p.add_argument('input', type=Path)
p.add_argument('--root', type=Path, default=Path('data'))
p.add_argument('--bucket', default='codeatlas')
a = p.parse_args()
input_location = a.input.parent.relative_to(a.root).as_posix()
con = trino.dbapi.connect(host='localhost', port=8080, user='codeatlas', catalog='hive')
c = con.cursor()
c.execute(f"CREATE SCHEMA IF NOT EXISTS hive.codeatlas WITH (location = 's3a://{a.bucket}/warehouse/')")

def register(name, schema, location):
    columns = ', '.join('"' + field.name + '" ' + ('INTEGER' if pa.types.is_int32(field.type) else 'VARCHAR') for field in schema)
    c.execute(f'DROP TABLE IF EXISTS hive.codeatlas.{name}')
    c.execute(f"CREATE TABLE hive.codeatlas.{name} ({columns}) WITH (format = 'PARQUET', external_location = 's3a://{a.bucket}/{location}/')")

register('github_file_v2', FILE, input_location)
for name, schema in SCHEMAS.items(): register(name, schema, f'code_intelligence_v1/{name}')
register('acl_findings', ACL, 'acl_analysis_v1/findings')
print('Registered snapshot and graph in hive.codeatlas')
