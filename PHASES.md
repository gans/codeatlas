# Delivery record

| Phase | State | Evidence |
|---|---|---|
| 1. Plan, infrastructure, Git snapshots | Passed local and live integration. | Tests read committed source in four languages, check SHA-256 and exact partition keys. Compose renders with pinned native ARM64 images. |
| 2. Tree-sitter graph | Passed local integration | Explicit Arrow schemas, hash reuse, extractor-version invalidation, changed/deleted files and parse-error behavior. |
| 3. Trino publication and SQL | Passed live integration | MinIO upload, Hive registration and Trino SELECT assertions passed on the isolated stack. |
| 4. Independent ACL analysis | Passed local integration | Fixture findings span all four languages and distinguish direct annotation evidence from review requests. |
| 5. Optional AI | Implemented, model inference unverified | Optional local model integrations, independent of graph extraction and ACL decisions. |
