"""Exercise the live S3/Hive/Trino path against the bundled fixture."""
from trino.dbapi import connect

with connect(host='localhost', port=8080, user='codeatlas', catalog='hive', schema='codeatlas') as connection:
    cursor = connection.cursor()
    for table in ('github_file_v2', 'files'):
        cursor.execute(f'SELECT count(*), count(DISTINCT language) FROM {table}')
        if tuple(cursor.fetchone()) != (4, 4):
            raise RuntimeError(f'Unexpected fixture inventory in {table}')
    cursor.execute("SELECT status, count(*) FROM acl_findings WHERE finding='annotation_compliance' GROUP BY status")
    if dict(cursor.fetchall()) != {'annotation_observed': 2, 'review_required': 2}:
        raise RuntimeError('Unexpected JVM annotation results')
print('Trino verified the raw input, graph inventory and ACL findings.')
