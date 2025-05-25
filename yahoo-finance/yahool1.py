import yfinance as yf
import pandas as pd
import boto3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import io
import time
import os

s3 = boto3.client('s3')
BUCKET = os.environ['BUCKET_NAME']
SOURCE = 'yahoofinance'

# 🧠 Step 1: Get S&P 500 symbols from Wikipedia using BeautifulSoup
def get_sp500_symbols():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table", {"id": "constituents"})
    symbols = []
    for row in table.tbody.find_all("tr")[1:]:
        cols = row.find_all("td")
        symbols.append(cols[0].text.strip())
    return symbols

def lambda_handler(event, context):
    now = datetime.now(pytz.UTC)
    date_folder = now.strftime(f"raw/{SOURCE}/%Y/%m/%d")

    timestamp_str = datetime.utcnow().strftime("%H%M")  # HourMinute as HHMM
    file_name = f"{timestamp_str}.csv"
    s3_key = f"{date_folder}/{file_name}"

    symbols = get_sp500_symbols()[:6]  # Limit to avoid rate limits
    all_data = []

    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1d", interval="1m")
            df.reset_index(inplace=True)

            df["symbol"] = symbol
            df["source"] = SOURCE
            df["ingest_timestamp"] = now.isoformat()
            df["status"] = "success"
            all_data.append(df)
        except Exception as e:
            all_data.append(pd.DataFrame([{
                "Datetime": now,
                "Open": None,
                "High": None,
                "Low": None,
                "Close": None,
                "Volume": None,
                "symbol": symbol,
                "source": SOURCE,
                "ingest_timestamp": now.isoformat(),
                "status": f"error: {e}"
            }]))
        time.sleep(1)  # Respect Yahoo Finance rate limits

    result_df = pd.concat(all_data)
    buffer = io.StringIO()
    result_df.to_csv(buffer, index=False)

    s3.put_object(Bucket=BUCKET, Key=s3_key, Body=buffer.getvalue())

    return {
        "statusCode": 200,
        "body": f"Data uploaded to s3://{BUCKET}/{s3_key}"
    }