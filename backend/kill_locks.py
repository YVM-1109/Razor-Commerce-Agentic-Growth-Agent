import psycopg
conn = psycopg.connect("postgresql://postgres:postgres@localhost:5433/postgres")
conn.autocommit = True
cur = conn.cursor()
cur.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid() AND datname = 'agentic_commerce';")
print("Locks cleared!")
cur.close()
conn.close()
