# Local artifact review, 2026-11-21

The reference machine is Apple Silicon with Python 3.12.7. Docker registry manifests confirmed native Linux ARM64 layers. Compose uses the exact architecture digests in `config/images-arm64.env`. The public images come from the PostgreSQL Docker Official Image, the Apache and Trino projects, and Chainguard's maintained MinIO distribution. The MinIO distribution is a third-party fork. The project owner approved the residual findings for the isolated MVP fixture run.

| Running image | Critical | High | Source |
|---|---:|---:|---|
| Chainguard MinIO | 0 | 0 | [Publisher and patch policy](https://www.chainguard.dev/docs/chainguard/containers/getting-started/web-and-data-services/minio) |
| Apache Hive standalone metastore 4.2.1 | 6 | 180 | [Apache standalone image](https://github.com/apache/hive/blob/rel/release-4.2.1/standalone-metastore/packaging/src/docker/README.md) |
| PostgreSQL 16 Alpine | 1 | 26 | [PostgreSQL security advisories](https://www.postgresql.org/support/security/16/) |
| Trino 484 | 0 | 21 | [Project container documentation](https://trino.io/docs/current/installation/containers.html) |

Counts are Trivy package findings across layers and libraries, including repeated CVEs. Package presence alone does not establish runtime reachability. Hive includes Avro CVE-2024-47561. PostgreSQL's bundled Go standard library has CVE-2025-68121. Trino includes Jackson advisories. The database and metastore have no published ports. MinIO and Trino publish on loopback only. These decisions apply to local fixture data.

Trivy 0.76.2 was obtained from the upstream GitHub release and checked against the SHA-256 in the release asset metadata. Scans used its 2026-11-21 vulnerability database and the exact platform digests. To refresh the image reports, run `python3 scripts/review_images.py` with a verified Trivy on PATH. Check the [scanner's release verification instructions](https://github.com/aquasecurity/trivy/blob/main/docs/getting-started/signature-verification.md) when acquiring a scanner.

The pgJDBC 42.7.14 jar matched copies from pgJDBC and Maven Central. Hadoop 3.4.1's S3 connector ships inside the Hive image. Its required AWS SDK v2 bundle 2.24.6 is mounted separately. The jar matched Maven Central's checksum. Scanning the Maven coordinates embedded in the bundle together with pgJDBC returned 1 critical, 17 high, 20 medium and 1 low findings. This inventory can miss shaded components without package metadata. The Hadoop client connects to the local MinIO endpoint with fixture credentials. [Hadoop dependency versions](https://github.com/apache/hadoop/blob/rel/release-3.4.1/hadoop-project/pom.xml) · [pgJDBC release](https://jdbc.postgresql.org/changelogs/2026-10-07-42.7.14-release/)

The Python runtime and test wheels were compared to PyPI's published file hashes and yanked status. The first scan found CVE-2026-25087 in PyArrow 20. The final runtime/test inventory, including PyArrow 24, returned zero reported vulnerabilities. Each install checks wheel content against the committed inventory and installs the dependency graph exported from uv.lock. Optional model weights, custom model code and AI dependencies require their own review before use. Checksums detect byte changes. They do not certify publisher behavior or replace vulnerability review.
