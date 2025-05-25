import boto3
import os
import json
import pandas as pd
import pyodbc
from io import StringIO

# AWS clients
sqs = boto3.client('sqs')
s3 = boto3.client('s3')

# Environment variables
QUEUE_URL = os.environ['QUEUE_URL']
BUCKET = os.environ['BUCKET_NAME']
SQL_SERVER_HOST = os.environ['SQL_SERVER_HOST']
SQL_SERVER_PORT = os.environ.get('SQL_SERVER_PORT', '1433')
SQL_SERVER_DB = os.environ['SQL_SERVER_DB']
SQL_SERVER_USER = os.environ['SQL_SERVER_USER']
SQL_SERVER_PASSWORD = os.environ['SQL_SERVER_PASSWORD']

# SQL Server connection string
CONN_STRING = f'DRIVER={{ODBC Driver 18 for SQL Server}};' \
              f'SERVER={SQL_SERVER_HOST},{SQL_SERVER_PORT};' \
              f'DATABASE={SQL_SERVER_DB};' \
              f'UID={SQL_SERVER_USER};PWD={SQL_SERVER_PASSWORD};' \
              'Encrypt=no;TrustServerCertificate=yes;Connection Timeout=30;'

def lambda_handler(event, context):
    # Step 1: Receive message from SQS
    response = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=5
    )
    
    if 'Messages' not in response:
        return {'statusCode': 204, 'body': 'No messages in queue'}
    
    message = response['Messages'][0]
    receipt_handle = message['ReceiptHandle']
    body = json.loads(message['Body'])
    
    # Step 2: Extract S3 object info
    s3_info = json.loads(body['Message']) if 'Message' in body else body
    s3_bucket = s3_info['Records'][0]['s3']['bucket']['name']
    s3_key = s3_info['Records'][0]['s3']['object']['key']
    
    print(f"Processing file: s3://{s3_bucket}/{s3_key}")
    
    # Step 3: Read file from S3
    s3_obj = s3.get_object(Bucket=s3_bucket, Key=s3_key)
    df = pd.read_csv(s3_obj['Body'])
    
    # Step 4: Connect to SQL Server
    try:
        conn = pyodbc.connect(CONN_STRING)
        cursor = conn.cursor()
    except Exception as e:
        return {'statusCode': 500, 'body': f'Failed DB connection: {str(e)}'}
    
    # Step 5: Insert into SQL Server (adjust table & columns as per schema)
    for _, row in df.iterrows():
        try:
            cursor.execute("""
                INSERT INTO YourTableName (Datetime, Open, High, Low, Close, Volume, symbol, source, ingest_timestamp, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, 
            row.get('Datetime'), row.get('Open'), row.get('High'), row.get('Low'), 
            row.get('Close'), row.get('Volume'), row.get('symbol'),
            row.get('source'), row.get('ingest_timestamp'), row.get('status'))
        except Exception as e:
            print(f"Row insert failed: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    # Step 6: Delete message from SQS
    sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=receipt_handle)

    return {
        'statusCode': 200,
        'body': f'Successfully processed and inserted data from {s3_key}'
    }
