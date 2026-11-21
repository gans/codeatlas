-- Inventory of reusable symbols
SELECT language, kind, count(*) AS symbols
FROM hive.codeatlas.symbols GROUP BY language, kind ORDER BY language, kind;

-- Unresolved calls are evidence, not resolved call-graph edges
SELECT path, source_id, target, line FROM hive.codeatlas.relationships
WHERE kind = 'calls' AND resolution = 'unresolved' ORDER BY path, line;

-- ACL adoption signals across languages
SELECT language, path, subject, evidence FROM hive.codeatlas.acl_findings
WHERE finding = 'acl_adoption' ORDER BY language, path;

-- Java/Kotlin methods requiring human review
SELECT path, subject, evidence, line FROM hive.codeatlas.acl_findings
WHERE finding = 'annotation_compliance' AND status = 'review_required';
