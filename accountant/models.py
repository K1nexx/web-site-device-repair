import psycopg

def get_connection(user_data):
    """Создание подключения к PostgreSQL 17"""
    try:
        conn = psycopg.connect(
            dbname="rz_gse_a7",
            user=str(user_data['username']),
            password=str(user_data['password']),
            host="localhost",
            port="5433",
        )
        return conn
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        return None