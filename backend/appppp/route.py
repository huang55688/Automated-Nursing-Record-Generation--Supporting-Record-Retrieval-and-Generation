from flask import Blueprint, request, render_template, jsonify, redirect, url_for, flash
from elasticsearch import Elasticsearch
from database import get_db_connection
# from database import insert_patient_data
from vectorizer import generate_vector
import time
import re
import logging


main_bp = Blueprint('main', __name__)

logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

# 連接 Elasticsearch
es_client = Elasticsearch(["http://localhost:9200"])
index_name = "internal_medicine"

# Elasticsearch 索引支援 kNN
def create_index():
    es_client.indices.delete(index='internal_medicine', ignore_unavailable=True)
    if not es_client.indices.exists(index=index_name):
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
                        "index": False,
                        "similarity": "cosine"
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
        es_client.indices.create(index=index_name, body=index_settings)



@main_bp.route('/')
def index():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT PatientID, PatientName FROM Patient ORDER BY PatientID")
        patients = cursor.fetchall()
        # Debug: 印出取回的資料
        # print("DEBUG: patients fetched:", patients)
        logger.debug("patients fetched: %s", patients)
    except Exception as e:
        logger.exception("Database Error: %s", e)
        patients = []
    finally:
        cursor.close()
        conn.close()

    return render_template('input.html', patients=patients, time=int(time.time()))

#呈現舊病人資料
@main_bp.route('/get_latest_patient_data/<patient_id>')
def get_latest_patient_data(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 先JOIN查 WardName, Patient資料 + Vitals最新一筆
    cursor.execute("""
        SELECT p.PatientID, p.PatientName, p.Gender, p.Age, w.WardName,
               v.Date, v.Time, v.Temperature, v.Respiration, v.Pulse, v.BloodPressure
        FROM Patient p
        JOIN Ward w ON p.WardID = w.WardID
        JOIN Vitals v ON p.PatientID = v.PatientID
        WHERE p.PatientID = %s
        ORDER BY v.Date DESC, v.Time DESC
        LIMIT 1
    """, (patient_id,))
    vitals_row = cursor.fetchone()

    # 再抓 Symptoms 最新一筆
    cursor.execute("""
        SELECT Date, Time, Data, Action, Response, Teaching
        FROM Symptoms
        WHERE PatientID = %s
        ORDER BY Date DESC, Time DESC
        LIMIT 1
    """, (patient_id,))
    symptom_row = cursor.fetchone()

    cursor.close()
    conn.close()

    # 若連 Vitals 都沒有，就直接回傳錯誤
    if not vitals_row:
        return jsonify({"error": "No Vitals data found for this patient."}), 404

    # 整理 Vitals
    data = {
        "patient_id": vitals_row[0],
        "patient_name": vitals_row[1],
        "gender": vitals_row[2],
        "age": vitals_row[3],
        "ward_name": vitals_row[4],
        "date": str(vitals_row[5]),
        "time": str(vitals_row[6]),
        "temperature": vitals_row[7],
        "respiration": vitals_row[8],
        "pulse": vitals_row[9],
        "blood_pressure": vitals_row[10]
    }

    # 若有抓到 Symptom，則一併放進 JSON
    if symptom_row:
        data["symptom_date"] = str(symptom_row[0])
        data["symptom_time"] = str(symptom_row[1])
        data["sym_data"] = symptom_row[2]
        data["sym_action"] = symptom_row[3]
        data["sym_response"] = symptom_row[4]
        data["sym_teaching"] = symptom_row[5]
    else:
        # 沒有症狀資料也沒關係，就放空或給個提示
        data["sym_data"] = ""
        data["sym_action"] = ""
        data["sym_response"] = ""
        data["sym_teaching"] = ""

    return jsonify(data)
@main_bp.route('/check_abnormalities', methods=['POST'])
def check_abnormalities():
    """
    接收前端送來的生理數據 (temperature, pulse, respiration, blood_pressure)
    依據判斷規則回傳異常狀態。
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400

    temperature = float(data.get('temperature', 0))
    pulse = float(data.get('pulse', 0))
    respiration = float(data.get('respiration', 0))
    bp_string = data.get('blood_pressure', '')  # 例如 "120/80"

    # 先拆解血壓 "收縮壓/舒張壓"
    systolic, diastolic = 0, 0
    if '/' in bp_string:
        parts = bp_string.split('/')
        if len(parts) == 2:
            systolic = float(parts[0])
            diastolic = float(parts[1])

    # 建立一個清單來放異常狀態
    abnormalities = []

    # 1) 體溫
    if temperature >= 38.0:
        abnormalities.append("fever")#發燒
    elif temperature < 35.0:
        abnormalities.append("hypothermia")#低溫

    # 2) 心跳
    if pulse < 60:
        abnormalities.append("bradycardia")#心跳過慢
    elif pulse > 100:
        abnormalities.append("tachycardia")#心跳過快

    # 3) 呼吸頻率
    if respiration < 12:
        abnormalities.append("bradypnea")#呼吸過慢
    elif respiration > 20:
        abnormalities.append("tachypnea")#呼吸過快

    # 4) 血壓
    # 收縮壓 (Systolic)
    if systolic != 0 and diastolic != 0:
        if systolic < 90 or diastolic < 60:
            abnormalities.append("hypotension")#低血壓
        if systolic > 140 or diastolic > 90:
            abnormalities.append("hypertension")#高血壓

    # 將結果回傳給前端
    # 例如: { "abnormalities": "fever, tachycardia" }
    if abnormalities:
        return jsonify({
            "abnormalities": ", ".join(abnormalities)
        })
    else:
        # 沒有異常就回傳空字串
        return jsonify({"abnormalities": ""})

# 基本資料寫入+檢索
@main_bp.route('/search', methods=['GET', 'POST'])
def search_records():
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        patient_name = request.form['patient_name']
        gender = request.form['gender']
        age = int(request.form['age'])
        ward_name = request.form['ward']
        date = request.form['date']
        time_data = request.form['time']
        temperature = float(request.form['temperature'])
        respiration = int(request.form['respiration'])
        pulse = int(request.form['pulse'])
        blood_pressure = request.form['blood_pressure']
        keyword = request.form.get('q')
        keyword_clean = re.sub(r'<[^>]+>', '', keyword)
        logger.debug("[CLEANED KEYWORD] %s", keyword_clean)
        

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 檢查 WardName 是否已存在
        cursor.execute("SELECT WardID FROM Ward WHERE WardName = %s", (ward_name,))
        ward_result = cursor.fetchone()

        if ward_result:
            ward_id = ward_result[0] 
        else:
            cursor.execute("SELECT COUNT(*) FROM Ward")
            count = cursor.fetchone()[0]
            ward_id = f"W{count + 1}"  
            cursor.execute(
                "INSERT INTO Ward (WardID, WardName) VALUES (%s, %s)",
                (ward_id, ward_name)
            )

        # 檢查 PatientID 是否已存在
        cursor.execute("SELECT COUNT(*) FROM Patient WHERE PatientID = %s", (patient_id,))
        patient_exists = cursor.fetchone()[0]

        if patient_exists == 0:
            cursor.execute("""
                INSERT INTO Patient (PatientID, PatientName, Gender, Age, WardID)
                VALUES (%s, %s, %s, %s, %s)
            """, (patient_id, patient_name, gender, age, ward_id))
        else:
    # 存在 -> UPDATE
            cursor.execute("""
                UPDATE Patient
                SET PatientName=%s, Gender=%s, Age=%s, WardID=%s
                WHERE PatientID=%s
            """, (patient_name, gender, age, ward_id, patient_id))    

        # 檢查Vitals是否已經存在
        cursor.execute("SELECT COUNT(*) FROM Vitals WHERE PatientID=%s AND Date=%s AND Time=%s", (patient_id, date, time_data))
        vitals_exists = cursor.fetchone()[0]

        if vitals_exists == 0:
            cursor.execute("""
                INSERT INTO Vitals (PatientID, Date, Time, Temperature, Respiration, Pulse, BloodPressure)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (patient_id, date, time_data, temperature, respiration, pulse, blood_pressure))

        conn.commit()
        cursor.close()
        conn.close()

        # Elasticsearch 查詢
        if not keyword:
            results = []
        else:
            query_record = {"DART": {
                "Data": keyword,
                "Action": "",
                "Response": "",
                "Teaching": ""
            }}

           
            
            try:
                  query_vector_np = generate_vector(query_record)
                  query_vector = query_vector_np.tolist()

                  logger.debug("Query vector length: %d | first5: %s", len(query_vector), query_vector[:5])
                  if len(query_vector) != 384:
                    logger.error("Vector length error: %d (expected 384)", len(query_vector))
                    raise ValueError(f"[錯誤] 向量長度為 {len(query_vector)} 正確應是384維啦 ")


            except Exception as e:
                  logger.exception("Vector generation error: %s", e)
                  return render_template('output.html', keyword=keyword, results=[],patient_id=patient_id, date=date, time=time_data)


            query_body = {
                "size": 5,
                "query": {
                    "script_score": {
                        "query": {
                            "bool": {
                                "must": [
                                    {
                                        "match": {
                                            "ward": {
                                                "query": ward_name,
                                                "operator": "or"  # 或者and，反正到時候再看情況
                                            }
                                        }
                                    }
                                ]
                            }
                        },
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'vector') + 1.0",
                            "params": {
                                "query_vector": query_vector
                            }
                        }
                    }
                }
            }




            try:
                t0 = time.perf_counter()          # 起始時間 (高精度)
                es_results = es_client.search(index=index_name, body=query_body)
                rtt_ms = (time.perf_counter() - t0) * 1000  # 往返時間 (ms)

                # ES 伺服器端處理時間 (ms)
                es_ms = es_results.get('took', 'N/A')

                logger.info("[Latency] ES RTT %.2f ms (server took %s ms)", rtt_ms, es_ms)

                hits = es_results["hits"]["hits"]
                results = [hit['_source'] for hit in hits]
            except Exception as e:
                logger.exception("Elasticsearch Error: %s", e)
                results = []

        return render_template('output.html', keyword=keyword, results=results,
                               patient_id=patient_id, date=date, time=time_data)

    return render_template('input.html', time=int(time.time()))





#新增DART
@main_bp.route('/save_symptoms', methods=['POST'])
def save_symptoms():
    data = request.get_json()
    if data is None:
        print("[錯誤] 沒有收到 JSON 或格式錯誤")
        return jsonify({"success": 0, "errmsg": "未收到 JSON 或格式錯誤", "data": None})

    patient_id = data.get('patient_id')
    date = data.get('date')
    time_data = data.get('time')
    selected_records = data.get('records', [])

    if not selected_records:
        return jsonify({"message": "未選擇任何記錄"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        for record in selected_records:
            cursor.execute(
                "INSERT INTO Symptoms (PatientID, Data, Action, Response, Teaching, Date, Time) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (patient_id, record["Data"], record["Action"], record["Response"], record["Teaching"], date, time_data)
            )

        conn.commit()
        return jsonify({"message": "儲存成功"}), 200

    except Exception as e:
        conn.rollback()
        print("Database Error:", e)
        return jsonify({"message": "儲存失敗", "error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()
        

# 顯示病人列表
@main_bp.route('/PDlook')
def pdlook():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT PatientID, PatientName FROM Patient ORDER BY PatientID")
    patients = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('PDlook.html', patients=patients, time=int(time.time()))



 # 顯示病人資料
@main_bp.route('/PDEdit/<patient_id>', methods=['GET'])
def pdedit(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT PatientID, PatientName FROM Patient ORDER BY PatientID")
        patients = cursor.fetchall()
        cursor.execute("SELECT * FROM Patient WHERE PatientID = %s", (patient_id,))
        patient = cursor.fetchone()

        if not patient:
            return "沒有這個病人的資料", 404
        
        # 取得 ward_name（從 Ward 表查 ward_id）
        cursor.execute("SELECT WardName FROM Ward WHERE WardID = %s", (patient[4],))
        ward_result = cursor.fetchone()
        ward_name = ward_result[0] if ward_result else 'Unknown Ward'

        patient_data = {
            "patient_id": patient[0],
            "patient_name": patient[1],
            "gender": patient[2],
            "age": patient[3],
            "ward_id": patient[4],
            "ward_name": ward_name   
        }

        # **查詢 Vitals 生理數據**
        cursor.execute("""
            SELECT Date, Time, Temperature, Respiration, Pulse, BloodPressure 
            FROM Vitals WHERE PatientID = %s 
            ORDER BY Date DESC, Time DESC
        """, (patient_id,))
        vitals_records = cursor.fetchall()

        vitals_list = []
        for vitals in vitals_records:
            vitals_list.append({
                "date": vitals[0],
                "time": vitals[1],
                "temperature": vitals[2],
                "respiration": vitals[3],
                "pulse": vitals[4],
                "blood_pressure": vitals[5]
            })
        # **查詢 Symptoms**
        cursor.execute("""
            SELECT Date, Time, Data, Action, Response, Teaching 
            FROM Symptoms WHERE PatientID = %s 
            ORDER BY Date DESC, Time DESC
        """, (patient_id,))
        symptoms_records = cursor.fetchall()

        symptoms_list = []
        for symptom in symptoms_records:
            symptoms_list.append({
                "date": symptom[0],
                "time": symptom[1],
                "data": symptom[2],
                "action": symptom[3],
                "response": symptom[4],
                "teaching": symptom[5]
            })

        return render_template(
            'PDEdit.html',
            patients=patients,
            patient=patient_data,
            vitals_list=vitals_list,
            symptoms_list=symptoms_list
            # time=int(time.time())
        )

    except Exception as e:
        print("Database Error:", e)
        return "資料庫錯誤", 500

    finally:
        cursor.close()
        conn.close()


        
# 修正
@main_bp.route('/update_patient/<patient_id>', methods=['POST'])
def update_patient(patient_id):
    patient_name = request.form['patient_name']
    gender = request.form['gender']
    age = request.form['age']
    ward_name = request.form['wardname']

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 查詢或新增 WardID
        cursor.execute("SELECT WardID FROM Ward WHERE WardName = %s", (ward_name,))
        ward_result = cursor.fetchone()
        if ward_result:
            ward_id = ward_result[0]
        else:
            cursor.execute("SELECT COUNT(*) FROM Ward")
            count = cursor.fetchone()[0]
            ward_id = f"W{count + 1}"
            cursor.execute("INSERT INTO Ward (WardID, WardName) VALUES (%s, %s)", (ward_id, ward_name))

        # 更新 Patient 資料
        cursor.execute("""
            UPDATE Patient 
            SET PatientName = %s, Gender = %s, Age = %s, WardID = %s
            WHERE PatientID = %s
        """, (patient_name, gender, age, ward_id, patient_id))

        # 抓取多筆 Vitals
        dates = request.form.getlist('date')
        times = request.form.getlist('time')
        original_dates = request.form.getlist('original_date')
        original_times = request.form.getlist('original_time')
        temperatures = request.form.getlist('temperature')
        respirations = request.form.getlist('respiration')
        pulses = request.form.getlist('pulse')
        blood_pressures = request.form.getlist('blood_pressure')

        for i in range(len(dates)):
            cursor.execute("""
                SELECT COUNT(*) FROM Vitals WHERE PatientID=%s AND Date=%s AND Time=%s
            """, (patient_id, original_dates[i], original_times[i]))
            exists = cursor.fetchone()[0]

            if exists:
                cursor.execute("""
                    UPDATE Vitals 
                    SET Temperature=%s, Respiration=%s, Pulse=%s, BloodPressure=%s, Date=%s, Time=%s
                    WHERE PatientID=%s AND Date=%s AND Time=%s
                """, (temperatures[i], respirations[i], pulses[i], blood_pressures[i],
                      dates[i], times[i], patient_id, original_dates[i], original_times[i]))
            else:
                cursor.execute("""
                    INSERT INTO Vitals (PatientID, Date, Time, Temperature, Respiration, Pulse, BloodPressure)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (patient_id, dates[i], times[i], temperatures[i], respirations[i], pulses[i], blood_pressures[i]))

        # 抓取多筆 Symptoms
        symptoms_dates = request.form.getlist('symptoms_date')
        symptoms_times = request.form.getlist('symptoms_time')
        symptoms_data = request.form.getlist('symptoms_data')
        symptoms_action = request.form.getlist('symptoms_action')
        symptoms_response = request.form.getlist('symptoms_response')
        symptoms_teaching = request.form.getlist('symptoms_teaching')

        for i in range(len(symptoms_dates)):
            cursor.execute("""
                SELECT COUNT(*) FROM Symptoms WHERE PatientID=%s AND Date=%s AND Time=%s
            """, (patient_id, symptoms_dates[i], symptoms_times[i]))
            exists = cursor.fetchone()[0]

            if exists:
                cursor.execute("""
                    UPDATE Symptoms 
                    SET Data=%s, Action=%s, Response=%s, Teaching=%s
                    WHERE PatientID=%s AND Date=%s AND Time=%s
                """, (symptoms_data[i], symptoms_action[i], symptoms_response[i], symptoms_teaching[i],
                      patient_id, symptoms_dates[i], symptoms_times[i]))
            else:
                cursor.execute("""
                    INSERT INTO Symptoms (PatientID, Date, Time, Data, Action, Response, Teaching)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (patient_id, symptoms_dates[i], symptoms_times[i],
                      symptoms_data[i], symptoms_action[i], symptoms_response[i], symptoms_teaching[i]))

        conn.commit()

    except Exception as e:
        conn.rollback()
        print("Database Update Error:", e)

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('main.pdedit', patient_id=patient_id))




















# 刪除
@main_bp.route('/delete_patient/<patient_id>', methods=['POST'])
def delete_patient(patient_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 只删除 Vitals 和 Symptoms 表的数据，不删除 Patient 表的数据
        cursor.execute("DELETE FROM Symptoms WHERE PatientID = %s", (patient_id,))
        cursor.execute("DELETE FROM Vitals WHERE PatientID = %s", (patient_id,))

        conn.commit()
        flash('Patient data (Vitals and Symptoms) deleted successfully', 'success')

        return redirect(url_for('main.pdlook'))

    except Exception as e:
        conn.rollback()
        flash(f'Error deleting patient data: {e}', 'danger')
        return redirect(url_for('main.pdlook'))

    finally:
        cursor.close()
        conn.close()



