from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq


def write_rows(path: Path, rows: list[dict], schema: pa.Schema) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    pq.write_table(pa.Table.from_pylist(rows, schema=schema), tmp)
    tmp.replace(path)


def read_rows(path: Path) -> list[dict]:
    return pq.ParquetFile(path).read().to_pylist()


def upload_tree(root: Path, endpoint: str, bucket: str) -> None:
    import boto3
    from botocore.exceptions import ClientError
    s3 = boto3.client('s3', endpoint_url=endpoint, aws_access_key_id='minioadmin', aws_secret_access_key='minioadmin', region_name='us-east-1')
    try:
        s3.head_bucket(Bucket=bucket)
    except ClientError as exc:
        if exc.response['Error']['Code'] not in ('404', 'NoSuchBucket', 'NotFound'):
            raise
        s3.create_bucket(Bucket=bucket)
    for path in root.rglob('*.parquet'):
        s3.upload_file(str(path), bucket, path.relative_to(root).as_posix())
