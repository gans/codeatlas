"""Scan pinned public images as data. Application images are never executed here."""
import json
import os
import subprocess
from pathlib import Path

PUBLISHERS = {'MINIO': 'cgr.dev/chainguard/minio', 'HIVE': 'apache/hive',
              'POSTGRES': 'postgres', 'TRINO': 'trinodb/trino'}
pins = dict(line.split('=', 1) for line in Path('config/images-arm64.env').read_text().splitlines() if line and not line.startswith('#'))
reports = Path('verified/reports')
reports.mkdir(parents=True, exist_ok=True)
for key, publisher in PUBLISHERS.items():
    image = f"{publisher}@sha256:{pins[key + '_DIGEST']}"
    report = reports / f'{key}.json'
    subprocess.run([os.environ.get('TRIVY', 'trivy'), 'image', '--image-src', 'remote',
                    '--platform', 'linux/arm64', '--scanners', 'vuln', '--format', 'json',
                    '--timeout', '20m', '--output', str(report), image], check=True)
    findings = [v for r in json.loads(report.read_text())['Results'] for v in r.get('Vulnerabilities', [])]
    print(image, {level: sum(v['Severity'] == level for v in findings) for level in ('CRITICAL','HIGH','MEDIUM','LOW')}, flush=True)
