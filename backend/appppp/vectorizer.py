
from sentence_transformers import SentenceTransformer
import numpy as np

# 載入模型：語意檢索最佳選擇
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def extract_text(record):
    """
    從 DART 欄位提取文字並組成語意向量輸入
    """
    dart = record.get("DART", {})
    fields = [
        dart.get("Data", ""),
        dart.get("Action", ""),
        dart.get("Response", ""),
        dart.get("Teaching", "")
    ]
    text = "。".join([field.strip() for field in fields if field.strip()])
    return text if text else "無內容"

def generate_vector(record):
    """
    將 DART 記錄轉為 SBERT 向量，並進行防呆檢查
    """
    text = extract_text(record)
    if not text.strip():
        raise ValueError("[錯誤] 輸入內容為空，無法產生向量")

    embedding = model.encode(text)

    if len(embedding) != 384:
        raise ValueError(f"[錯誤] 向量維度錯誤，長度為 {len(embedding)}，應為 384")

    if any(np.isnan(embedding)):
        raise ValueError("[錯誤] 向量中含有 NaN")

    return np.array(embedding, dtype=np.float32)
