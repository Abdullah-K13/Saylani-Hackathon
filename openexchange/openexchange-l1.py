import requests
import pandas as pd
import boto3
from datetime import datetime
import pytz
import io
import os 

s3 = boto3.client('s3')
BUCKET = os.getenv('BUCKET')
SOURCE = os.getenv('SOURCE')
APP_ID = os.getenv('APP_ID')

def lambda_handler(event, context):
    now = datetime.now(pytz.UTC)
    date_folder = now.strftime(f"raw/{SOURCE}/%Y/%m/%d")
    timestamp_str = datetime.utcnow().strftime("%H%M")  # HourMinute as HHMM
    file_name = f"{timestamp_str}.csv"
    s3_key = f"{date_folder}/{file_name}"

    # Fetch data from Open Exchange Rates
    url = f"https://openexchangerates.org/api/latest.json?app_id={APP_ID}"
    response = requests.get(url)
    data = response.json()

    # Convert to DataFrame
    base = data.get('base', 'USD')
    timestamp = datetime.utcfromtimestamp(data.get('timestamp')).isoformat()

    rates = data.get('rates', {})
    df = pd.DataFrame(list(rates.items()), columns=['currency', 'rate'])
    df['base'] = base
    df['exchange_timestamp'] = timestamp
    df['ingest_timestamp'] = now.isoformat()
    df['source'] = SOURCE
    df['status'] = 'success'

    # Save to CSV in memory
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)

    # Upload to S3
    s3.put_object(Bucket=BUCKET, Key=s3_key, Body=buffer.getvalue())

    return {
        "statusCode": 200,
        "body": f"Exchange rate data uploaded to s3://{BUCKET}/{s3_key}"
    }
