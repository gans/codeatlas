import argparse
import json
from pathlib import Path
from .ingest import generate
from .extract import process
from .acl import analyze
from .storage import upload_tree


def main():
    p = argparse.ArgumentParser(prog='codeatlas')
    sub = p.add_subparsers(dest='command', required=True)
    ingest = sub.add_parser('ingest'); ingest.add_argument('repo', type=Path); ingest.add_argument('--output', type=Path, default=Path('data'))
    extract = sub.add_parser('extract'); extract.add_argument('input', type=Path); extract.add_argument('--output', type=Path, default=Path('data/code_intelligence_v1'))
    acl = sub.add_parser('acl'); acl.add_argument('--graph', type=Path, default=Path('data/code_intelligence_v1')); acl.add_argument('--output', type=Path, default=Path('data/acl_analysis_v1'))
    upload = sub.add_parser('upload'); upload.add_argument('--root', type=Path, default=Path('data')); upload.add_argument('--endpoint', default='http://localhost:9000'); upload.add_argument('--bucket', default='codeatlas')
    args = p.parse_args()
    if args.command == 'ingest': print(generate(args.repo, args.output))
    elif args.command == 'extract': print(json.dumps(process(args.input, args.output)))
    elif args.command == 'acl': print(f'{len(analyze(args.graph, args.output))} findings')
    else: upload_tree(args.root, args.endpoint, args.bucket)

if __name__ == '__main__': main()
