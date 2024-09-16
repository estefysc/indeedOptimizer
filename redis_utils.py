import redis
import time
from logging_config import app_logger

# Set up logging
logger = app_logger.getChild('redis')

# Connect to Redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()  # Test the connection
    logger.info("Successfully connected to Redis")
except redis.ConnectionError as e:
    logger.error(f"Failed to connect to Redis: {e}")
    r = None

def set_state(state_type, job_type, location, value):
    """
    Set a key-value pair in Redis.

    Args:
        state_type (str): The type of state being set.
        job_type (str): The type of job.
        location (str): The location for the job.
        value: The value to store.

    Raises:
        redis.ConnectionError: If unable to connect to Redis.
        redis.RedisError: For other Redis-related errors.

    Note:
        Redis-py automatically handles the encoding of Python objects to bytes:
        1. Strings are encoded to UTF-8 bytes.
        2. Integers are converted to strings and then encoded.
        3. Other types may require explicit conversion before setting.

        This automatic encoding simplifies the process of storing data in Redis,
        but it's important to be aware of it when retrieving and decoding data.
    """
    if r is None:
        logger.error("Redis connection not available")
        raise redis.ConnectionError("Redis connection not available")

    key = f"{state_type}_{job_type}_{location}"
    try:
        r.set(key, value)
        logger.info(f"Successfully set state for {key}")
    except redis.RedisError as e:
        logger.error(f"Failed to set state for {key}: {e}")
        raise

def get_state(state_type, job_type, location):
    """
    Retrieve a value from Redis and decode it to a UTF-8 string.

    Args:
        state_type (str): The type of state being retrieved.
        job_type (str): The type of job.
        location (str): The location for the job.

    Returns:
        str or None: The decoded string value if the key exists, None otherwise.

    Raises:
        redis.ConnectionError: If unable to connect to Redis.

    Note:
        Redis stores data as bytes. We decode the returned value to a UTF-8 string
        because:
        1. Redis stores data in a binary format.
        2. Python 3 distinguishes between strings (sequences of Unicode characters) 
           and bytes.
        3. The Redis-py client returns raw bytes from Redis.
        4. Decoding converts these bytes back into a Python string.

        This approach ensures we always return either a string or None, making it 
        easier to work with in Python code. It also handles cases where the key 
        doesn't exist in Redis (which returns None).
    """
    if r is None:
        logger.error("Redis connection not available")
        raise redis.ConnectionError("Redis connection not available")

    key = f"{state_type}_{job_type}_{location}"
    try:
        value = r.get(key)
        logger.info(f"Successfully retrieved state for {key}")
        return value.decode('utf-8') if value else None
    except redis.RedisError as e:
        logger.error(f"Failed to get state for {key}: {e}")
        raise

def set_last_scrape(location, job_type):
    value = int(time.time())
    state_type = "last_scrape"
    set_state(state_type, job_type, location, value)

# This will have to be called by the window?
def set_jobs_as_viewed(location, job_type):
    state_type = "jobs_viewed"
    set_state(state_type, job_type, location, 1)

def set_jobs_as_not_viewed(location, job_type):
    state_type = "jobs_viewed"
    set_state(state_type, job_type, location, 0)

def check_if_jobs_viewed(location, job_type):
    return bool(get_state("jobs_viewed", job_type, location))

def should_scrape(location, job_type, interval_seconds):
    last_scrape = get_state("last_scrape", job_type, location)
    if not last_scrape:
        return True
    return (int(time.time()) - int(last_scrape)) >= interval_seconds

