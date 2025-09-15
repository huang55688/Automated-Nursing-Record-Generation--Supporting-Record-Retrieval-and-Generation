FROM python:3.9-slim

WORKDIR /app

# 安裝 Python 套件
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 複製 backend/ 下所有檔案 (含 appppp/資料夾) 到 /app
COPY . /app/

EXPOSE 8000

# 預設啟動: 執行 appppp/initapp.py (可自行調整檔名/入口)
CMD ["python", "appppp/initapp.py"]
