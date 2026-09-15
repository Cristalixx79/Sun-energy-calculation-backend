import psycopg2

try:
    psycopg2.connect(
        host="localhost",
        port=5433,
        user="myuser",
        password="mypassword",
        dbname="sun_panels_db",
    )
    print("Подключение успешно!")
except UnicodeDecodeError as e:
    # достаём и правильно декодируем оригинальные байты ошибки
    print("Реальный текст ошибки:", e.object.decode("cp1251", errors="replace"))
except Exception as e:
    print("Ошибка:", repr(e))