from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

resp = es.search(
    index="internal_medicine",
    query={"match_all": {}},
    size=10  # 顯示前 10 筆
)

for i, hit in enumerate(resp["hits"]["hits"], 1):
    src = hit["_source"]
    print(f"\n第 {i} 筆資料")
    print(f"PatientID：{src.get('patientID')}")
    print(f"Ward     ：{src.get('ward')}")
    
    print("DART：")
    for k in ["Data", "Action", "Response", "Teaching"]:
        print(f"  {k}：{src['DART'].get(k, '')}")
    
    vector = src.get("vector", [])
    print(f"Vector（共 {len(vector)} 維）：{vector[:10]} ...")  # 只印前10維防爆版
