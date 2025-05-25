import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import boto3
from io import StringIO
import os


def lambda_handler(event, context):
    url = "https://coinmarketcap.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    tbody = soup.find("tbody")
    if not tbody:
        raise Exception("Could not find the table body on the page.")

    rows = tbody.find_all("tr")
    if len(rows) < 10:
        raise Exception("Less than 10 rows found on the page.")

    data = []

    for row in rows[:10]:
        cols = row.find_all("td")

        try:
            # Extract the name and symbol separately from <p> tags
            name_cell = cols[2]
            name_tag = name_cell.find_all("p")[0] if name_cell.find_all("p") else None
            symbol_tag = name_cell.find_all("p")[1] if len(name_cell.find_all("p")) > 1 else None

            name = name_tag.text.strip() if name_tag else ""
            symbol = symbol_tag.text.strip() if symbol_tag else ""

            price = cols[3].text.strip()
            change_24h = cols[4].text.strip()
            change_7d = cols[5].text.strip()
            market_cap = cols[6].text.strip()

            data.append({
                "Name": name,
                "Symbol": symbol,
                "Price": price,
                "24h Change": change_24h,
                "7d Change": change_7d,
                "Market Cap": market_cap,
                "Timestamp": datetime.utcnow().isoformat()
            })

        except Exception as e:
            print(f"Skipping row due to error: {e}")
            continue

    df = pd.DataFrame(data)

    # Write DataFrame to CSV in-memory
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)

    # S3 bucket info — change these to your bucket and desired folder structure
    bucket_name = os.environ['BUCKET_NAME']

    now = datetime.utcnow()
    
    date_folder = now.strftime(f"raw/coinmarketcap/%Y/%m/%d")
    timestamp_str = datetime.utcnow().strftime("%H%M")  # HourMinute as HHMM
    file_name = f"{timestamp_str}.csv"
    s3_key = f"{date_folder}/{file_name}"

    s3 = boto3.client("s3")
    s3.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=csv_buffer.getvalue(),
        ContentType="text/csv"
    )

    return {
        "statusCode": 200,
        "body": f"Top 10 cryptos saved to s3://{bucket_name}/{s3_key}"
    }
