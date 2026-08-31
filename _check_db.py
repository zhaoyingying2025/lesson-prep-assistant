import sqlite3
import sys

path = sys.argv[1]
conn = sqlite3.connect(path)
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
print(f"数据库: {path}")
print(f"表 ({len(tables)}):")
for t in tables:
    c.execute(f"SELECT COUNT(*) FROM [{t[0]}]")
    count = c.fetchone()[0]
    print(f"  {t[0]}: {count} 行")
if "courses" in [t[0] for t in tables]:
    c.execute("SELECT id, name, created_at FROM courses")
    print("\n课程列表:")
    for r in c.fetchall():
        print(f"  id={r[0]}, name={r[1]}, created_at={r[2]}")
conn.close()