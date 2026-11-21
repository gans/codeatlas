"""Check downloaded wheel bytes against the publisher's PyPI release metadata."""
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

wheelhouse = Path('verified/wheels')
hashes = {}
requirements = []
for wheel in sorted(wheelhouse.glob('*.whl')):
    name, version, *_ = wheel.name.split('-')
    with urlopen(f'https://pypi.org/pypi/{name}/{version}/json', timeout=30) as response:
        artifacts = json.load(response)['urls']
    artifact = next(item for item in artifacts if item['filename'] == wheel.name)
    digest = artifact['digests']['sha256']
    if artifact['yanked'] or hashlib.sha256(wheel.read_bytes()).hexdigest() != digest:
        raise ValueError(f'Wheel rejected: {wheel.name}')
    hashes[wheel.name] = digest
    requirements.append(f'{name}=={version} --hash=sha256:{digest}')
if not requirements:
    raise ValueError('Empty wheelhouse')
Path('verified/wheels.sha256.json').write_text(json.dumps(hashes, indent=2) + '\n')
Path('verified/requirements.txt').write_text('\n'.join(requirements) + '\n')
