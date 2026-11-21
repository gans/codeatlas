"""Fetch reviewed wheels and jars as data, then check their pinned hashes."""
from pathlib import Path
import subprocess
import sys
from codeatlas.verification import verify_file

root = Path('verified')
(root / 'wheels').mkdir(parents=True, exist_ok=True)
(root / 'hadoop').mkdir(exist_ok=True)
subprocess.run([sys.executable, '-m', 'pip', 'download', '--index-url', 'https://pypi.org/simple',
                '--no-deps', '--only-binary', ':all:', '--require-hashes', '--disable-pip-version-check',
                '-r', 'security/requirements-macos-arm64-py312.txt', '-d', str(root / 'wheels')], check=True)
for location, dest, checksum in (
    ('https://jdbc.postgresql.org/download/postgresql-42.7.14.jar', root / 'postgresql.jar', 'postgresql-42.7.14'),
    ('https://repo.maven.apache.org/maven2/software/amazon/awssdk/bundle/2.24.6/bundle-2.24.6.jar',
     root / 'hadoop/bundle-2.24.6.jar', 'aws-sdk-bundle-2.24.6'),
):
    if not dest.is_file():
        subprocess.run(['curl', '--fail', '--location', '--proto', '=https', location, '-o', str(dest)], check=True)
    verify_file(dest, Path(f'security/{checksum}.sha256'))
