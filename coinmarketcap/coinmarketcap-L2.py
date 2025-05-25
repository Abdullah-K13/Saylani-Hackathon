import json
import boto3
import pandas as pd
from io import StringIO
import os


def lambda_handler(event, context):
    # Initialize AWS clients
    sqs = boto3.client('sqs')
    s3 = boto3.client('s3')
    sns = boto3.client('sns')  

    # Your SQS queue URL
    queue_url = os.getenv('QUEUE_URL')
    topic_arn = os.getenv('TOPIC_ARN')

    # Poll messages from SQS (max 10)
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=0
    )

    if 'Messages' not in response:
        return {
            'statusCode': 200,
            'body': 'No messages in queue.'
        }

    messages = response['Messages']

    for msg in messages:
        # Parse SQS message body (SNS format)
        sqs_body = json.loads(msg['Body'])
        sns_message_str = sqs_body['Message']
        sns_message = json.loads(sns_message_str)

        # Extract S3 bucket and key from the message
        s3_record = sns_message['Records'][0]['s3']
        bucket = s3_record['bucket']['name']
        key = s3_record['object']['key']

        # Fetch CSV content from S3
        obj = s3.get_object(Bucket=bucket, Key=key)
        csv_content = obj['Body'].read().decode('utf-8')

        # Load into pandas DataFrame
        df = pd.read_csv(StringIO(csv_content))

        # === Data processing step (customize as needed) ===
        df['processed_timestamp'] = pd.Timestamp.utcnow()

        # Convert processed DataFrame back to CSV
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)

        # Define processed S3 path
        processed_bucket = bucket
        processed_key = key.replace('raw/', 'processed/')

        # Upload processed CSV to S3
        s3.put_object(
            Bucket=processed_bucket,
            Key=processed_key,
            Body=csv_buffer.getvalue().encode('utf-8')
        )

        # 🔔 Publish SNS notification
        sns.publish(
            TopicArn=topic_arn,
            Subject='Processed Crypto Data',
            Message=f"Processed file saved to s3://{processed_bucket}/{processed_key}"
        )

        # Delete message from SQS
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=msg['ReceiptHandle']
        )

    return {
        'statusCode': 200,
        'body': f"Processed {len(messages)} messages, saved processed data to S3."
    }
