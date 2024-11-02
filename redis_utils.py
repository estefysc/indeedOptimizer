import redis
import time
import json

from logging_config import app_logger
from colorama import Fore
from datetime import datetime

# Set up logging
logger = app_logger.getChild('redis')

# Connect to Redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()  # Test the connection
    logger.info(Fore.YELLOW + "Successfully connected to Redis")
except redis.ConnectionError as e:
    logger.error(Fore.RED + f"Failed to connect to Redis: {e}")
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
        logger.error(Fore.RED + "Redis connection not available")
        raise redis.ConnectionError("Redis connection not available")

    key = f"{state_type}_{job_type}_{location}"
    try:
        r.set(key, value)
        logger.info(Fore.YELLOW + f"Successfully set state for {key}")
    except redis.RedisError as e:
        logger.error(Fore.RED + f"Failed to set state for {key}: {e}")
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
        logger.error(Fore.RED + "Redis connection not available")
        raise redis.ConnectionError("Redis connection not available")

    key = f"{state_type}_{job_type}_{location}"
    try:
        value = r.get(key)
        logger.info(Fore.YELLOW + f"Successfully retrieved state for {key}")
        return value.decode('utf-8') if value else None
    except redis.RedisError as e:
        logger.error(Fore.RED + f"Failed to get state for {key}: {e}")
        raise

def set_last_scrape(job_type, location):
    value = int(time.time())
    state_type = "last_scrape"
    set_state(state_type, job_type, location, value)

# This will have to be called by the window?
def set_jobs_as_viewed(job_type, location):
    state_type = "jobs_viewed"
    set_state(state_type, job_type, location, 1)

def set_jobs_as_not_viewed(job_type, location):
    state_type = "jobs_viewed"
    set_state(state_type, job_type, location, 0)

def should_scrape_by_jobs_state(job_type, location):
    state = get_state("jobs_viewed", job_type, location)
    # None = no scrap history
    # 1 = jobs viewed
    # 0 = jobs not viewed
    # Return True if state is None or 1, False otherwise
    return state is None or state == '1'

# interval seconds represent the amount of time a specific scrap should wait until it runs again
def should_scrape_by_time(job_type, location, interval_seconds):
    last_scrape = get_state("last_scrape", job_type, location)
    if not last_scrape:
        return True
    # the number of seconds that have elapsed since the last scrape >= to the given interval
    # the program should wait to scrape again
    return (int(time.time()) - int(last_scrape)) >= interval_seconds

def save_job_to_redis(job_id: str, job_report: dict) -> None:
    """
    Save a job description to Redis as a JSON string.

    Args:
        job_id (str): The unique identifier for the job.
        job_report (dict): The job report data to be saved.

    Raises:
        redis.RedisError: If there is an error saving to Redis.
    """
    # Serialize the job description to a JSON string
    job_description = json.dumps(job_report)

    # Get current time and format it as a string
    timestamp = datetime.now().strftime('%Y-%m-%d-%H:%M:%S')

    key = f"{job_id}_{timestamp}"

    try:
        # Use the Redis JSON set method to save the job description
        response = r.json().set(key, "$", job_description)
        logger.info(Fore.YELLOW + f"Successfully saved job '{job_id}' at '{timestamp}' with response: {response}")
    except redis.RedisError as e:
        logger.error(Fore.RED + f"Failed to save job '{job_id}' at '{timestamp}' in function 'save_job_to_redis'. Error: {e}. Job description: {job_description}")
        raise