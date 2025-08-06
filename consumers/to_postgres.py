from kafka import KafkaConsumer
import json
import psycopg2
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kafka consumer with retry
def init_kafka_consumer():
    max_retries = 5
    for attempt in range(max_retries):
        try:
            consumer = KafkaConsumer(
                'bids',
                bootstrap_servers='kafka:9092',
                auto_offset_reset='earliest',
                group_id='postgres-group',
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            logger.info("Kafka consumer initialized for postgres-group")
            return consumer
        except Exception as e:
            logger.error(f"Attempt {attempt + 1}/{max_retries} - Failed to initialize Kafka consumer: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
    logger.error("Failed to initialize Kafka consumer after retries")
    exit(1)

consumer = init_kafka_consumer()

# PostgreSQL connection
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host="postgres",
            dbname="bidsdb",
            user="postgres",
            password="rathi"
        )
        logger.info("PostgreSQL connection established")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        return None

# Consume and insert into PostgreSQL
while True:
    try:
        for message in consumer:
            bid = message.value
            logger.info(f"Received bid: {bid}")
            conn = get_db_connection()
            if conn is None:
                logger.error("Skipping bid due to database connection failure")
                continue
            try:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO bids (name, price) VALUES (%s, %s)",
                    (bid['name'], bid['price'])
                )
                conn.commit()
                logger.info(f"Inserted bid into PostgreSQL: {bid}")
            except Exception as e:
                logger.error(f"Error inserting bid: {e}")
                conn.rollback()
            finally:
                cur.close()
                conn.close()
    except Exception as e:
        logger.error(f"Error in consumer loop: {e}")
        time.sleep(5)  # Wait before retrying