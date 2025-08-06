from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from kafka import KafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic
import json
import psycopg2
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Kafka producer with retry and topic creation
def init_kafka_producer():
    max_retries = 10
    for attempt in range(max_retries):
        try:
            # Create Kafka admin client to ensure topic exists
            admin_client = KafkaAdminClient(bootstrap_servers='kafka:9092')
            topic_list = admin_client.list_topics()
            if 'bids' not in topic_list:
                topic = NewTopic(name='bids', num_partitions=3, replication_factor=1)
                admin_client.create_topics(new_topics=[topic], validate_only=False)
                logger.info("Created Kafka topic 'bids'")
            admin_client.close()

            producer = KafkaProducer(
                bootstrap_servers='kafka:9092',
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                retries=5
            )
            logger.info("Kafka producer initialized successfully")
            return producer
        except Exception as e:
            logger.error(f"Attempt {attempt + 1}/{max_retries} - Failed to connect to Kafka: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
    logger.error("Failed to initialize Kafka producer after retries")
    return None

producer = init_kafka_producer()

# PostgreSQL connection
def get_db_connection():
    max_retries = 10
    for attempt in range(max_retries):
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
            logger.error(f"Attempt {attempt + 1}/{max_retries} - Failed to connect to PostgreSQL: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
    logger.error("Failed to connect to PostgreSQL after retries")
    return None

class Bid(BaseModel):
    name: str
    price: int

@app.post("/submit_bid")
async def submit_bid(bid: Bid):
    if producer is None:
        logger.error("Kafka producer not available")
        raise HTTPException(status_code=500, detail="Kafka producer not available")
    try:
        producer.send("bids", bid.dict())
        producer.flush()
        logger.info(f"Bid sent to Kafka: {bid.dict()}")
        return {"message": "Bid submitted successfully"}
    except Exception as e:
        logger.error(f"Failed to send bid to Kafka: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send bid to Kafka: {str(e)}")

@app.get("/highest_bid")
async def highest_bid():
    conn = get_db_connection()
    if conn is None:
        logger.error("Database connection failed")
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT MAX(price) FROM bids")
        result = cur.fetchone()
        highest = result[0] if result and result[0] is not None else 0
        logger.info(f"Highest bid retrieved: {highest}")
        return {"highest_bid": highest}
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/bids")
async def get_bids():
    conn = get_db_connection()
    if conn is None:
        logger.error("Database connection failed")
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, price, bid_ts FROM bids ORDER BY bid_ts DESC")
        bids = cur.fetchall()
        logger.info(f"Retrieved {len(bids)} bids")
        return [{"id": bid[0], "name": bid[1], "price": bid[2], "bid_ts": bid[3]} for bid in bids]
    except Exception as e:
        logger.error(f"Failed to retrieve bids: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve bids: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/")
async def serve_html():
    return FileResponse("static/index.html")