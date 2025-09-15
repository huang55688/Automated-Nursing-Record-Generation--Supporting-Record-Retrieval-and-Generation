import psycopg2

def get_db_connection():
    """建立與 PostgreSQL 的連線"""
    conn = psycopg2.connect(
        dbname="mydatabase",
        user="mythesis",
        password="thesis1234",
        host="localhost",
        port="5432"
    )
    return conn

def delete_all_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # **先刪除有外鍵關聯的表**
        cursor.execute("DELETE FROM Vitals")
        cursor.execute("DELETE FROM Symptoms")
        cursor.execute("DELETE FROM Patient")
        cursor.execute("DELETE FROM Ward")

        # **重置自增主鍵**
        cursor.execute("ALTER SEQUENCE vitals_recordid_seq RESTART WITH 1")
        cursor.execute("ALTER SEQUENCE symptoms_symptomid_seq RESTART WITH 1")

        conn.commit()
        print("✅ 所有資料已成功刪除！")
    
    except Exception as e:
        conn.rollback()
        print("❌ 刪除資料時發生錯誤:", e)
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    delete_all_data()
