import psycopg2

def get_db_connection():
    """建立與 PostgreSQL 的連線"""
    conn = psycopg2.connect(
        dbname="mydatabase",
        user="mythesis",
        password="thesis1234",
        host="localhost",  # 這裡 Flask 直接連接 localhost
        port="5432"
    )
    return conn


# def insert_patient_data(patient_id, patient_name, gender, age, ward_id, date, time, temperature, respiration, pulse, blood_pressure):
#     conn = get_db_connection()
#     cursor = conn.cursor()

#     try:
#         cursor.execute("SELECT WardID FROM Ward WHERE WardID = %s", (ward_id,))
#         if cursor.fetchone() is None:
#             cursor.execute(
#                 "INSERT INTO Ward (WardID, WardName) VALUES (%s, %s)",
#                 (ward_id, ward_id)  
#             )


#         cursor.execute(
#             "INSERT INTO Patient (PatientID, PatientName, Gender, Age, WardID) VALUES (%s, %s, %s, %s, %s)",
#             (patient_id, patient_name, gender, age, ward_id)
#         )


#         cursor.execute(
#             "INSERT INTO Vitals (PatientID, Date, Time, Temperature, Respiration, Pulse, BloodPressure) VALUES (%s, %s, %s, %s, %s, %s, %s)",
#             (patient_id, date, time, temperature, respiration, pulse, blood_pressure)
#         )


#         conn.commit()

#     except Exception as e:
#         conn.rollback()
#         print("Database Error:", e)
#         raise e
#     finally:
#         cursor.close()
#         conn.close()