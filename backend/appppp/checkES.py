from elasticsearch import Elasticsearch
import json

es = Elasticsearch(["http://localhost:9200"])

res = es.search(index="internal_medicine", size=1)

print(json.dumps(res.body, indent=2, ensure_ascii=False))
