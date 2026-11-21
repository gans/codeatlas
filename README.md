# CodeAtlas MVP

CodeAtlas converts a local Git commit into a reusable code graph in Parquet, publishes it to MinIO, and queries it through Trino using a PostgreSQL-backed Apache Hive Metastore. The ACL plugin reads the graph independently.

**CodeAtlas is a test MVP for local evaluation. It is not suitable for production workloads.** The reference stack uses public fixture credentials, and graph updates can leave readers with a partially published snapshot. See the [security review](SECURITY_REVIEW.md) for the known issues in the tested configuration.

If you run CodeAtlas, you are responsible for deciding whether it is appropriate for your use, securing your environment, protecting the source code you process, and verifying results before acting on them. You assume the risks of using it to the extent permitted by applicable law. The [Apache License 2.0](LICENSE) sets out the warranty disclaimer and limits on contributor liability in sections 7 and 8. Third-party components remain subject to their own licenses.

## Run the reference environment

Tested on Apple Silicon with Python 3.12, uv, Git and Docker Compose. The reviewed wheel bundle targets CPython 3.12 on macOS ARM64. The source project supports Python 3.12+. Review new platform artifacts before using another target. See [security review](SECURITY_REVIEW.md) for public image publishers, exact scan results and the local MVP risk decision.

```sh
make fetch      # fetch wheels and the two jars, check against committed hashes
make install    # create .venv, install from uv.lock and the local wheelhouse
make test
make local      # Git → raw Parquet → code graph → ACL findings
make images     # load the four pinned public linux/arm64 images
make up
make smoke      # wait for services, upload, register tables and assert SQL results
```

Run the examples from the repository root with the Trino CLI included in the pinned image:

```sh
docker compose --env-file config/images-arm64.env exec -T trino trino < sql/examples.sql
```

The Trino monitoring UI listens at http://127.0.0.1:8080 and the MinIO console at http://127.0.0.1:9001 (local fixture login `minioadmin / minioadmin`). `make down` stops the services and preserves named volumes. `make clean` removes the local fixture checkout and generated Parquet files.

## Before ingesting another repository

Scan the exact commit at `HEAD` for secrets before running `ingest`. CodeAtlas copies the full text of supported source files into local Parquet without scanning or redacting it. The `upload` command sends every Parquet file under its data directory to MinIO, including older snapshots. Once a snapshot is registered, anyone with read access to the Trino `github_file_v2` table can query its source text.

If you discover a credential after ingestion, revoke or rotate it, remove it from the source, and clean up the affected local snapshots and MinIO objects. Ingesting a corrected commit leaves earlier snapshots in place.

For a different repository, use the path printed by ingestion as the argument to extraction:

```sh
export PYTHONPATH=src
.venv/bin/python -m codeatlas.cli ingest /path/to/repository --output data
.venv/bin/python -m codeatlas.cli extract "$INPUT_PARQUET"
.venv/bin/python -m codeatlas.cli acl
.venv/bin/python -m codeatlas.cli upload
.venv/bin/python scripts/register.py "$INPUT_PARQUET"
```

Substitute the path printed by `ingest`. One input Parquet file represents a complete snapshot of one repository, including tracked `.java`, `.kt`, `.ts` and `.py` files at HEAD. Paths with non-UTF-8 source are unsupported. Each run of `extract` replaces the graph snapshot: omitted files are deleted, so don't combine unrelated repositories by running them sequentially into the same graph directory. Repository identity defaults to the repository directory name. Timestamps use UTC and seconds; avoid generating two snapshots in the same second in the same output directory.

## Data contracts and extension points

Raw files are stored beneath `ingest_name=github_file_v2/year=yyyy/month=mm/day=dd/timestamp=yyyyMMddTHHmmssZ/parquet-files/`. `scripts/register.py` registers the selected snapshot's `parquet-files` directory as `github_file_v2`; it does not discover historical partitions. Run it again to switch snapshots. The remaining tables are separate `files`, `symbols`, `imports`, `annotations`, `relationships`, and `acl_findings` Parquet datasets. Their explicit schemas are in `src/codeatlas/schemas.py`; symbol and annotation line numbers are 1-based. The `files` dataset is the incremental ledger. Unchanged content hashes and extractor version reuse existing rows; changed files are reparsed and deleted files removed. Increment `extract.VERSION` when extraction semantics change. Graph snapshots and local uploads are single-writer operations and are not transactional across datasets; avoid querying while publishing. The uploader overwrites matching objects but does not delete old objects.

Add analyzers as independent consumers of the graph datasets, with their own versioned output directory and explicit schema. `acl.py` is an example. Its name matching is intentionally limited: an observed annotation or ACL-related import/call is evidence only, and absent direct annotations require review. Calls are unresolved textual references. Neither finding proves security compliance, policy applicability, enforcement, or lack thereof. Syntax errors fail the extraction rather than silently yielding an incomplete graph.

## Optional local AI

After reviewing the locked semantic extra and obtaining the model, install it with `uv sync --locked --extra dev --extra semantic --no-install-project --no-build`. Store a reviewed CodeRankEmbed snapshot in `verified/CodeRankEmbed/` and its approved filename-to-SHA-256 JSON inventory at `verified/CodeRankEmbed.sha256.json`. Search embeds symbol metadata in a local FAISS index. The loader runs the verified custom model code offline. For explanations, start a reviewed local Ollama runtime containing the Qwen3 model and pass selected evidence to it.

```python
from pathlib import Path
from codeatlas.semantic import explain, search

results = search(Path('data/code_intelligence_v1'), 'read an ACL guarded resource')
print(explain(str(results[:2])))
```

Set `PYTHONPATH=src` when running these examples. Model inference was not exercised during the fixture test.

## Expected sample results

See [sample results](EXPECTED_RESULTS.md) and [the implementation plan](IMPLEMENTATION_PLAN.md). Run `make integration` for the local end-to-end Git/Parquet/parser/ACL test. Docker-backed registration and Trino queries require a running Docker daemon and are not included in the offline pytest suite.
