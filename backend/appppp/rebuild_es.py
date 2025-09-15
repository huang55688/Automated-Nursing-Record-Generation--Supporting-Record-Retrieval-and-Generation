# rebuild_es.py

from elasticsearch import Elasticsearch
import json
import os
from vectorizer import generate_vector

index_name = "internal_medicine"
es = Elasticsearch("http://localhost:9200")

# 1. 刪除舊索引
if es.indices.exists(index=index_name):
    es.indices.delete(index=index_name)
    print(f"✅ 已刪除索引 {index_name}")

# 2. 建立新索引，設定正確的 dense_vector
# 建立新索引，設定正確的 dense_vector
index_settings = {
    "settings": {
        "index": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        }
    },
    "mappings": {
        "properties": {
            "vector": {
                "type": "dense_vector",
                "dims": 384,
                "index": False   
            },
            "patientID": {"type": "keyword"},
            "ward": {"type": "text"},
            "DART": {
                "properties": {
                    "Data": {"type": "text"},
                    "Action": {"type": "text"},
                    "Response": {"type": "text"},
                    "Teaching": {"type": "text"}
                }
            }
        }
    }
}

es.indices.create(index=index_name, body=index_settings)
print(f"✅ 已建立索引 {index_name}")

# 3. 匯入資料（來自 mdata.json）
script_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(script_dir, "mdata.json")

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

records = data["records"]
success_count = 0
fail_count = 0

for i, record in enumerate(records, start=1):
    try:
        vector = generate_vector(record).tolist()
        record['vector'] = vector
        es.index(index=index_name, document=record)
        print(f"[{i}] ✅ 寫入成功")
        success_count += 1
    except Exception as e:
        print(f"[{i}] ❌ 寫入失敗：{e}")
        fail_count += 1

print(f"\n=== 匯入完成！成功 {success_count} 筆，失敗 {fail_count} 筆 ===")
