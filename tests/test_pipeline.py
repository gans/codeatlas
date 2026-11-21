import hashlib
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import pyarrow.parquet as pq
import pytest
from codeatlas.acl import analyze
from codeatlas.extract import process
from codeatlas.ingest import generate
from codeatlas.schemas import FILE, SCHEMAS
from codeatlas.storage import read_rows


def git(repo, *args):
    subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    path = tmp_path / 'example'
    shutil.copytree('fixtures/repository', path)
    git(path, 'init', '-q')
    git(path, 'add', '.')
    git(path, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'initial')
    return path


@pytest.mark.integration
def test_end_to_end_incremental(repo, tmp_path):
    data = tmp_path / 'data'
    source = generate(repo, data, datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc))
    assert 'ingest_name=github_file_v2/year=2025/month=01/day=02/timestamp=20250102T030405Z/parquet-files/' in str(source)
    assert pq.ParquetFile(source).schema_arrow == FILE
    files = read_rows(source)
    assert {r['language'] for r in files} == {'java', 'kotlin', 'typescript', 'python'}
    assert all(hashlib.sha256(r['content'].encode()).hexdigest() == r['content_hash'] for r in files)
    graph = data / 'code_intelligence_v1'
    assert process(source, graph) == {'processed': 4, 'unchanged': 0, 'deleted': 0}
    assert process(source, graph) == {'processed': 0, 'unchanged': 4, 'deleted': 0}
    for name, schema in SCHEMAS.items():
        assert pq.ParquetFile(graph / name / 'part-00000.parquet').schema_arrow == schema
    symbols = read_rows(graph / 'symbols' / 'part-00000.parquet')
    assert {s['language'] for s in symbols} == {'java', 'kotlin', 'typescript', 'python'}
    findings = analyze(graph, data / 'acl_analysis_v1')
    assert any(f['status'] == 'annotation_observed' for f in findings)
    assert any(f['status'] == 'review_required' for f in findings)
    assert {f['language'] for f in findings if f['finding'] == 'acl_adoption'} >= {'java', 'kotlin', 'typescript', 'python'}
    (repo / 'src/client.py').write_text('def changed():\n    pass\n')
    (repo / 'src/client.ts').unlink()
    git(repo, 'add', '-A')
    git(repo, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'update')
    source = generate(repo, data, datetime(2025, 1, 2, 3, 4, 6, tzinfo=timezone.utc))
    assert process(source, graph) == {'processed': 1, 'unchanged': 2, 'deleted': 1}
    assert not any(s['path'].endswith('client.ts') for s in read_rows(graph / 'symbols' / 'part-00000.parquet'))


def test_extractor_version_invalidates_cache(repo, tmp_path, monkeypatch):
    import codeatlas.extract as extractor
    source = generate(repo, tmp_path / 'data')
    graph = tmp_path / 'graph'
    process(source, graph)
    monkeypatch.setattr(extractor, 'VERSION', 'test-next')
    assert process(source, graph)['processed'] == 4
    assert {r['extractor_version'] for r in read_rows(graph / 'files' / 'part-00000.parquet')} == {'test-next'}


def test_syntax_errors_fail_without_publishing(repo, tmp_path):
    (repo / 'src/client.py').write_text('def broken(:\n')
    git(repo, 'add', '.')
    git(repo, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'bad')
    source = generate(repo, tmp_path / 'data')
    graph = tmp_path / 'graph'
    with pytest.raises(ValueError, match='parse error'):
        process(source, graph)
    assert not graph.exists()


def test_kotlin_call_is_unresolved():
    from codeatlas.extract import parse_file
    content = 'fun view() { checkAcl("read") }'
    graph = parse_file(dict(repository='example', path='View.kt', language='kotlin',
                            content=content, content_hash=hashlib.sha256(content.encode()).hexdigest()))
    function, = graph['symbols']
    edge, = graph['relationships']
    assert (edge['source_id'], edge['target'], edge['resolution']) == (function['symbol_id'], 'checkAcl', 'unresolved')


def test_modified_model_bundle_is_rejected(tmp_path):
    import json
    from codeatlas.verification import verify_directory
    model = tmp_path / 'model'
    model.mkdir()
    (model / 'config.json').write_bytes(b'reviewed')
    model.with_suffix('.sha256.json').write_text(json.dumps({'config.json': hashlib.sha256(b'reviewed').hexdigest()}))
    verify_directory(model)
    (model / 'config.json').write_bytes(b'changed')
    with pytest.raises(ValueError, match='mismatch'):
        verify_directory(model)
