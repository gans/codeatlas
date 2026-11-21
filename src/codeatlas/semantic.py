"""Optional, explicitly local semantic retrieval and explanation helpers."""
import json
from pathlib import Path
from urllib.request import Request, urlopen


def search(graph: Path, query: str, limit: int = 5, model: Path = Path('verified/CodeRankEmbed')) -> list[dict]:
    import faiss
    import numpy as np
    from .storage import read_rows
    symbols = read_rows(graph / 'symbols' / 'part-00000.parquet')
    if not symbols:
        return []
    from .verification import verify_directory
    verify_directory(model)
    import os
    os.environ['HF_HUB_OFFLINE'] = '1'
    from sentence_transformers import SentenceTransformer
    encoder = SentenceTransformer(str(model.resolve()), local_files_only=True, trust_remote_code=True,
                                  model_kwargs={'use_safetensors': True})
    vectors = np.asarray(encoder.encode([f"{s['language']} {s['kind']} {s['qualified_name']} {s['path']}" for s in symbols], normalize_embeddings=True), dtype='float32')
    index = faiss.IndexFlatIP(vectors.shape[1]); index.add(vectors)
    q = np.asarray(encoder.encode(['Represent this query for searching relevant code: ' + query], normalize_embeddings=True), dtype='float32')
    distances, indices = index.search(q, min(limit, len(symbols)))
    return [symbols[int(i)] | {'score': float(score)} for i, score in zip(indices[0], distances[0])]


def explain(evidence: str, model: str = 'qwen3:8b', endpoint: str = 'http://localhost:11434') -> str:
    prompt = 'Explain the following static-analysis evidence. State uncertainty and do not claim security compliance.\n' + evidence
    request = Request(endpoint.rstrip('/') + '/api/generate', data=json.dumps({'model': model, 'prompt': prompt, 'stream': False}).encode(), headers={'Content-Type': 'application/json'})
    with urlopen(request, timeout=120) as response:
        return json.load(response)['response']
