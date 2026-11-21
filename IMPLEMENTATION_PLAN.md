# Implementation plan

1. Stand up MinIO, PostgreSQL, Hive Metastore and Trino with local-only credentials. Generate a deterministic `github_file_v2` Parquet fixture from a local Git repository and preserve its Hive-style S3 layout.
2. Extract a language-neutral code graph using Tree-sitter for Java, Kotlin, TypeScript and Python. Publish explicit, versioned Arrow schemas and retain unchanged files incrementally using content hashes and extractor version.
3. Register the Parquet datasets in Hive and provide Trino queries. Exercise ingestion, incremental processing and schemas in integration tests.
4. Add an independent ACL analyzer that consumes the graph and produces evidence and conservative compliance findings. Test cross-language adoption and uncertain cases.
5. Add optional local embeddings/FAISS and Ollama explanations, documentation and expected fixture results. Validate each stage with pytest and, when Docker is available, a live stack smoke test.
