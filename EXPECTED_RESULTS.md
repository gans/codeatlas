# Expected fixture results

- Four Git source files are ingested: one each for Java, Kotlin, TypeScript and Python.
- The first extraction reports `processed: 4, unchanged: 0, deleted: 0`; repeating the same snapshot reports `processed: 0, unchanged: 4, deleted: 0`.
- The graph includes Java and Kotlin classes and methods, a TypeScript function and a Python function, plus imports, annotations/decorators and syntactic call/containment relationships.
- ACL findings include adoption evidence from all four languages. Annotated Java/Kotlin methods have `annotation_observed`; methods without a direct annotation have `review_required`. Neither status is a security compliance verdict.
- Changing one tracked file and deleting another yields one processed, two unchanged and one deleted file on the next snapshot.
