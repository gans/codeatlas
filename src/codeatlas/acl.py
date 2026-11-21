"""Independent policy plugin consuming graph evidence only."""
from pathlib import Path
from .schemas import ACL
from .storage import read_rows, write_rows


def analyze(graph: Path, output: Path) -> list[dict]:
    symbols = read_rows(graph / 'symbols' / 'part-00000.parquet')
    annotations = read_rows(graph / 'annotations' / 'part-00000.parquet')
    imports = read_rows(graph / 'imports' / 'part-00000.parquet')
    calls = read_rows(graph / 'relationships' / 'part-00000.parquet')
    by_symbol = {}
    for a in annotations:
        by_symbol.setdefault(a['symbol_id'], []).append(a)
    findings = []
    def add(r, subject_id, subject, finding, status, evidence, line):
        findings.append({k: r[k] for k in ('repository', 'path', 'language')} | dict(subject_id=subject_id, subject=subject, finding=finding, status=status, evidence=evidence, line=line))
    for symbol in symbols:
        if symbol['language'] not in ('java', 'kotlin') or symbol['kind'] not in ('method', 'function'):
            continue
        matches = [a for a in by_symbol.get(symbol['symbol_id'], []) if a['name'].split('.')[-1] == 'RequiresAcl']
        add(symbol, symbol['symbol_id'], symbol['qualified_name'], 'annotation_compliance', 'annotation_observed' if matches else 'review_required', matches[0]['name'] if matches else 'No direct @RequiresAcl annotation observed; inheritance and policy applicability are unresolved.', symbol['start_line'])
    for r in imports:
        if 'acl' in r['target'].lower():
            add(r, r['import_id'], r['target'], 'acl_adoption', 'evidence_observed', 'ACL-related import; usage and enforcement unresolved.', r['line'])
    for r in calls:
        if r['kind'] == 'calls' and 'acl' in r['target'].lower():
            add(r, r['source_id'], r['target'], 'acl_adoption', 'evidence_observed', 'ACL-related call; target and enforcement unresolved.', r['line'])
    write_rows(output / 'findings' / 'part-00000.parquet', findings, ACL)
    return findings
