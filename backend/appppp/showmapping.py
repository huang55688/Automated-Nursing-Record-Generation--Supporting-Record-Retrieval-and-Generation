from elasticsearch import Elasticsearch
import json

es = Elasticsearch("http://localhost:9200")
index_name = "internal_medicine"

mapping = es.indices.get_mapping(index=index_name)
print(json.dumps(mapping.body, indent=2, ensure_ascii=False))
