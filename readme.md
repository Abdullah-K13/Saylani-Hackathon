# 📊 Data Engineering Hackathon – Real-Time Data Ingestion & Processing Pipeline

Welcome to the **Data Engineering Hackathon – Case Study**, where we designed and implemented a scalable, serverless architecture using AWS to ingest, process, and store real-time data from multiple sources.

---

## 🚀 Overview

This project demonstrates a modern data engineering architecture using:

- **AWS Lambda**
- **Amazon S3**
- **Amazon EventBridge**
- **Amazon SNS & SQS**
- **Snowflake**
- **SQL Server**
- **Python (yfinance, BeautifulSoup, requests)**

The pipeline supports **minute-level real-time ingestion** and processing of:

- **Yahoo Finance OHLCV data** (for S&P 500 stocks)
- **Top 10 cryptocurrencies from CoinMarketCap**
- **Live foreign exchange rates from Open Exchange Rates**

---

## 📁 Architecture Breakdown

### 📌 Data Sources

| Source            | Description                                                                 |
|-------------------|-----------------------------------------------------------------------------|
| **Yahoo Finance** | Minute-level OHLCV data for S&P 500 tickers using `yfinance`.              |
| **CoinMarketCap** | Top 10 cryptocurrencies scraped from the "All Crypto" page.                |
| **Open Exchange Rates** | Live forex data using their API (requires an App ID).                    |

---

## 🔧 Task 1 – Data Acquisition (Serverless Ingestion)

### ⚙️ Technologies Used
- **AWS Lambda**
- **Amazon EventBridge**
- **Amazon S3**

### 🧩 Workflow
1. **Lambda Functions**:
   - `finance-ingest-coinmarketcap-minute`
   - `finance-ingest-openexchange-minute`
   - `finance-ingest-yahoofinace-minute`

2. **Triggering**:
   - Each function is triggered **every minute** via **Amazon EventBridge**.

3. **Storage**:
   - Data is saved to S3 in the following format:
     ```
     s3://data-hackathon-smit-abdullah-khan/raw/{source}/YYYY/MM/DD/{HHMM}.csv
     ```

4. **Metadata (Contract)**:
   - Each file includes metadata such as:
     - `symbol`
     - `source`
     - `timestamp`
     - `status`

---

## 🔁 Task 2 – Real-Time Data Processing

### ⚙️ Technologies Used
- **Amazon SNS**
- **Amazon SQS**
- **AWS Lambda**
- **Snowflake & SQL Server**

### 🧩 Step-by-Step Workflow

#### 1. SNS Notification
- **S3 triggers an SNS topic** on every new object creation.
- SNS **filters messages by data source** using metadata and routes to the correct FIFO queue.

#### 2. SQS Queues
- Three FIFO queues handle message ordering and decoupling:
  - `yahoo-finance-queue`
  - `coinmarketcap-queue`
  - `openexchangerates-queue`

#### 3. Lambda Consumers
- Each queue has a **dedicated Lambda function** that:
  - Reads messages every minute.
  - Processes the message and fetches the relevant file from S3.

#### 4. Data Sink
- **Yahoo Finance → Snowflake**: Transformed OHLCV data inserted into a Snowflake table.
- **CoinMarketCap → S3 (processed folder)**: Cleaned and structured crypto data stored.
- **Open Exchange Rates → SQL Server**: Parsed forex rates inserted into SQL Server.

---

## ✅ Setup Instructions

### 1. AWS Setup
- Create your S3 bucket:

- Deploy all 3 Lambda functions.
- Set up EventBridge rules (cron: `rate(1 minute)`).
- Configure SNS topic and filters for each data source.
- Create the 3 SQS FIFO queues.
- Connect S3 Event Notifications → SNS Topic.

### 2. Credentials
- Store AWS, SQL Server, Snowflake, and API credentials securely using:
- **AWS Secrets Manager**, or
- **Environment variables**

---

## 📊 Example Output Paths
s3://data-hackathon-smit-abdullah-khan/raw/yahoofinance/2025/05/25/0233.csv
s3://data-hackathon-smit-abdullah-khan/processed/coinmarketcap/2025/05/25/0233.json


---

## 🧠 Learnings

- How to build a **fully serverless data pipeline**.
- Real-time processing with **FIFO queues and triggers**.
- Integrating **external APIs** and ingesting **structured data** into warehouses.
- Using metadata for **contract-driven data flow**.

---

## 🙌 Contributors

- **Abdullah Khan** – [@yourgithub](https://github.com/abdullah-k13)
- Supervised by: *SMIT Data Engineering Team*

---



