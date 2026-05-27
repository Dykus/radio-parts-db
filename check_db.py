import sqlite3
conn = sqlite3.connect("data/radioparts.db")
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(parts)")
columns = cursor.fetchall()
print("Колонки в таблице parts:")
for col in columns:
    print(col)
conn.close()