import sqlite3
from pathlib import Path


DB_PATH = Path('base_workflow/outputs/tutorial.db')
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
con = sqlite3.connect(DB_PATH)
cursor = con.cursor()

cursor.execute('CREATE TABLE movie(title, year, score)')
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cursor.fetchall())  # 打印数据库中所有表名

con.close()
