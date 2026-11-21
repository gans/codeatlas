"""Wait for local port forwarding, coordinator startup and the Hive connection."""
import time
from urllib.request import urlopen
from trino.dbapi import connect

deadline = time.monotonic() + 120
while True:
    try:
        with urlopen('http://127.0.0.1:9000/minio/health/ready', timeout=2):
            pass
        with connect(host='127.0.0.1', port=8080, user='codeatlas', request_timeout=4, max_attempts=1) as connection:
            connection.cursor().execute('SHOW SCHEMAS FROM hive').fetchall()
        break
    except Exception as exc:
        if time.monotonic() >= deadline:
            raise SystemExit(f'Stack readiness deadline exceeded: {exc}') from exc
        time.sleep(2)
