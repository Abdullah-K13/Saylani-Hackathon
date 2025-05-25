import os
import pyodbc

# Ensure Lambda uses your .so libraries from /opt/lib
os.environ["LD_LIBRARY_PATH"] = "/opt/lib"

server = '0.tcp.in.ngrok.io,19347'
database = 'test'
username = 'abd'
password = '123456789'

def lambda_handler(event, context):
    conn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT GETDATE()")
    return {"result": str(cursor.fetchone())}
