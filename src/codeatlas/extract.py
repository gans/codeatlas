"""Language-neutral syntax evidence; intentionally contains no ACL policy."""
import hashlib
from pathlib import Path
from tree_sitter_language_pack import get_parser
from .schemas import SCHEMAS
from .storage import read_rows, write_rows

VERSION = '1.0.1'
SYMBOL_TYPES = {
    'class_definition': 'class', 'function_definition': 'function',
    'class_declaration': 'class', 'interface_declaration': 'interface',
    'method_declaration': 'method', 'constructor_declaration': 'constructor',
    'function_declaration': 'function', 'method_definition': 'method',
    'object_declaration': 'object',
}
IMPORT_TYPES = {'import_statement', 'import_from_statement', 'import_declaration', 'import_header'}
ANNOTATION_TYPES = {'annotation', 'marker_annotation', 'decorator'}
CALL_TYPES = {'call', 'call_expression', 'method_invocation'}


def ident(*parts: object) -> str:
    return hashlib.sha256('\0'.join(map(str, parts)).encode()).hexdigest()


def parse_file(row: dict) -> dict[str, list[dict]]:
    data = row['content'].encode()
    root = get_parser(row['language']).parse(data).root_node
    if root.has_error:
        raise ValueError(f"Tree-sitter parse error in {row['path']}")
    common = {k: row[k] for k in ('repository', 'path', 'language', 'content_hash')}
    common['extractor_version'] = VERSION
    result = {name: [] for name in SCHEMAS}
    result['files'].append(common)
    def text(node):
        return data[node.start_byte:node.end_byte].decode()
    def visit(node, parent_id=None, ancestors=()):
        typ = node.type
        name_node = node.child_by_field_name('name')
        if name_node is None and row['language'] == 'kotlin' and typ in SYMBOL_TYPES:
            name_node = next((c for c in node.named_children if c.type in ('simple_identifier', 'type_identifier')), None)
        symbol_id = parent_id
        names = ancestors
        if typ in SYMBOL_TYPES and name_node:
            name = text(name_node)
            names = (*ancestors, name)
            symbol_id = ident(row['repository'], row['path'], typ, node.start_byte, name)
            result['symbols'].append(dict(common, symbol_id=symbol_id, name=name, kind=SYMBOL_TYPES[typ], qualified_name='.'.join(names), start_line=node.start_point[0]+1, end_line=node.end_point[0]+1))
            if parent_id:
                result['relationships'].append(dict(common, source_id=parent_id, target=symbol_id, kind='contains', resolution='resolved', line=node.start_point[0]+1))
        if typ in IMPORT_TYPES:
            result['imports'].append(dict(common, import_id=ident(row['repository'], row['path'], typ, node.start_byte), target=text(node), line=node.start_point[0]+1))
        if typ in ANNOTATION_TYPES:
            raw = text(node).lstrip('@').strip()
            name = raw.split('(', 1)[0].strip()
            args = raw[len(name):].strip()
            result['annotations'].append(dict(common, annotation_id=ident(row['repository'], row['path'], typ, node.start_byte), symbol_id=symbol_id, name=name, arguments=args, line=node.start_point[0]+1))
        if typ in CALL_TYPES:
            target_node = node.child_by_field_name('function') or node.child_by_field_name('name')
            if target_node is None and row['language'] == 'kotlin' and node.named_children:
                target_node = node.named_children[0]
            if target_node:
                result['relationships'].append(dict(common, source_id=symbol_id, target=text(target_node), kind='calls', resolution='unresolved', line=node.start_point[0]+1))
        # Python decorators precede the declaration; associate them with its symbol.
        if typ == 'decorated_definition':
            declaration = node.child_by_field_name('definition')
            if declaration is not None:
                visit(declaration, parent_id, ancestors)
                symbol = next((s for s in reversed(result['symbols']) if s['start_line'] == declaration.start_point[0]+1), None)
                for child in node.named_children:
                    if child.type == 'decorator':
                        visit(child, symbol['symbol_id'] if symbol else parent_id, ancestors)
                return
        for child in node.named_children:
            visit(child, symbol_id, names)
    visit(root)
    return result


def process(input_file: Path, output: Path) -> dict[str, int]:
    incoming = read_rows(input_file)
    keys = [(r['repository'], r['path']) for r in incoming]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate repository/path in input snapshot')
    has_graph = any(output.glob('*/part-00000.parquet'))
    old = {name: read_rows(output / name / 'part-00000.parquet') if has_graph else [] for name in SCHEMAS}
    previous = {(r['repository'], r['path']): r for r in old['files']}
    unchanged = {key for key, row in zip(keys, incoming) if key in previous and previous[key]['content_hash'] == row['content_hash'] and previous[key]['extractor_version'] == VERSION}
    merged = {name: [r for r in rows if (r['repository'], r['path']) in unchanged] for name, rows in old.items()}
    for row, key in zip(incoming, keys):
        if key not in unchanged:
            parsed = parse_file(row)
            for name in SCHEMAS:
                merged[name].extend(parsed[name])
    for name, schema in SCHEMAS.items():
        write_rows(output / name / 'part-00000.parquet', merged[name], schema)
    return {'processed': len(incoming) - len(unchanged), 'unchanged': len(unchanged), 'deleted': len(set(previous) - set(keys))}
