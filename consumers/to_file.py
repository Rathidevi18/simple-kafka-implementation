from kafka import KafkaConsumer
import json
import os
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kafka consumer
try:
    consumer = KafkaConsumer(
        'bids',
        bootstrap_servers='kafka:9092',
        auto_offset_reset='earliest',
        group_id='file-group',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    logger.info("Kafka consumer initialized for file-group")
except Exception as e:
    logger.error(f"Failed to initialize Kafka consumer: {e}")
    exit(1)

# Write to file
output_file = '/app/bids_log/bids.log'
os.makedirs(os.path.dirname(output_file), exist_ok=True)

while True:
    try:
        with open(output_file, 'a') as f:
            for message in consumer:
                bid = message.value
                logger.info(f"Received bid: {bid}")
                try:
                    f.write(json.dumps(bid) + '\n')
                    f.flush()
                    logger.info(f"Wrote bid to file: {bid}")
                except Exception as e:
                    logger.error(f"Error writing to file: {e}")
    except Exception as e:
        logger.error(f"Error in consumer loop: {e}")
        time.sleep(5)  # Wait before retrying