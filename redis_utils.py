import redis
import time
import json
import os

import numpy as np
import pandas as pd
import requests

from redis.commands.search.field import (
    NumericField,
    TagField,
    TextField,
    VectorField,
)
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from sentence_transformers import SentenceTransformer

from logging_config import app_logger
from colorama import Fore
from datetime import datetime
from docker_utils import DockerEnvironment

# Set up logging
logger = app_logger.getChild('redis')

class RedisConnection:
    """
    A singleton class that manages the Redis connection.
    
    This class implements a lazy loading pattern for Redis connection,
    creating the connection only when first needed and reusing it afterwards.
    """
    def __init__(self):
        """Initialize RedisConnection with no active connection."""
        self._redis_client = None
    
    def get_connection(self) -> redis.Redis:
        """
        Get or create a Redis connection.

        Returns:
            redis.Redis: An active Redis connection instance.

        Raises:
            redis.ConnectionError: If unable to establish connection to Redis.

        Note:
            - Uses 'redis' as host when running in Docker, 'localhost' otherwise
            - Connection is created only once and reused for subsequent calls
            - Performs a ping test to verify connection is working
        """
        if self._redis_client is None:
            try:
                host = 'redis' if DockerEnvironment.is_running_in_docker() else 'localhost'
                self._redis_client = redis.Redis(host=host, port=6379, db=0)
                # Test the connection. If connection fails, error will happen here.
                self._redis_client.ping()  

                if host == 'redis':
                    logger.info(Fore.YELLOW + "Successfully connected to Redis Stack")
                else:
                    logger.info(Fore.YELLOW + "Successfully connected to Redis (local)")
            except redis.ConnectionError as e:
                logger.error(Fore.RED + f"Failed to connect to Redis: {e}")
                raise
        return self._redis_client
    
# Create a singleton instance
redis_connection = RedisConnection()

def set_state(state_type: str, job_type: str, location: str, value: int) -> None:
    """
    Set a key-value pair in Redis.

    Args:
        state_type (str): The type of state being set.
        job_type (str): The type of job.
        location (str): The location for the job.
        value (int): The value to store.

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
    r = redis_connection.get_connection()
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

def get_state(state_type: str, job_type: str, location: str) -> str:
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
    r = redis_connection.get_connection()
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

def set_last_scrape(job_type: str, location: str) -> None:
    """
    Set the last scrape time for a specific job and location.

    Args:
        job_type (str): The type of job.
        location (str): The location for the job.
    """
    value = int(time.time())
    state_type = "last_scrape"
    set_state(state_type, job_type, location, value)

def set_jobs_as_viewed(job_type: str, location: str) -> None:
    """
    Mark jobs as viewed for a specific job type and location.

    Args:
        job_type (str): The type of job.
        location (str): The location for the job.
    """
    state_type = "jobs_viewed"
    set_state(state_type, job_type, location, 1)

def set_jobs_as_not_viewed(job_type: str, location: str) -> None:
    """
    Mark jobs as not viewed for a specific job type and location.

    Args:
        job_type (str): The type of job.
        location (str): The location for the job.
    """
    state_type = "jobs_viewed"
    set_state(state_type, job_type, location, 0)

def should_scrape_by_jobs_state(job_type: str, location: str) -> bool:
    """
    Determine if scraping should occur based on the jobs viewed state.

    Args:
        job_type (str): The type of job.
        location (str): The location for the job.

    Returns:
        bool: True if there is no scrap history or jobs have been viewed, False otherwise.
    """
    state = get_state("jobs_viewed", job_type, location)
    # None = no scrap history
    # 1 = jobs viewed
    # 0 = jobs not viewed
    # Return True if state is None or 1, False otherwise
    return state is None or state == '1'

# interval seconds represent the amount of time a specific scrap should wait until it runs again
def should_scrape_by_time(job_type: str, location: str, interval_seconds: int) -> bool:
    """
    Determine if scraping should occur based on the time since the last scrape.

    Args:
        job_type (str): The type of job.
        location (str): The location for the job.
        interval_seconds (int): The minimum interval in seconds between scrapes.

    Returns:
        bool: True if enough time has passed since the last scrape or if no last scrape is recorded.
    """
    last_scrape = get_state("last_scrape", job_type, location)
    if last_scrape is None:
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

    # Get current time and format it as a string
    timestamp = datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
    key = f"job:{job_id}_{timestamp}"

    try:
        r = redis_connection.get_connection()
        # Use the Redis JSON set method to save the job description
        response = r.json().set(key, "$", job_report)
        logger.info(Fore.YELLOW + f"Successfully saved job '{job_id}' at '{timestamp}' with response: {response}")
    except redis.RedisError as e:
        logger.error(Fore.RED + f"Failed to save job '{job_id}' at '{timestamp}' in function 'save_job_to_redis'. Error: {e}. Job description: {job_description}")
        raise

def get_job_descriptions() -> tuple[list[str], list[str]]:
    """
    Retrieve all job descriptions from Redis.

    Returns:
        tuple[list[str], list[str]]: A tuple containing (redis_keys, descriptions)
    """
    r = redis_connection.get_connection()
    keys = r.keys("job:*")
    job_descriptions = r.json().mget(keys, "$.jobDescription")
    descriptions = [item for sublist in job_descriptions for item in sublist]
    return keys, descriptions

def generate_embeddings(descriptions: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a list of job descriptions.

    Args:
        descriptions (list[str]): List of job descriptions to embed

    Returns:
        list[list[float]]: List of embedding vectors
    """
    embedder = SentenceTransformer('msmarco-distilbert-base-v4')
    return embedder.encode(descriptions).astype(np.float32).tolist()

def store_embeddings(keys: list[str], embeddings: list[list[float]]) -> None:
    """
    Store job description embeddings back into the job objects in Redis.

    Args:
        keys (list[str]): Redis keys for the job descriptions
        embeddings (list[list[float]]): List of embedding vectors to store
    """
    r = redis_connection.get_connection()
    for key, embedding in zip(keys, embeddings):
        r.json().set(key, "$.description_embedding", embedding)

def process_job_description_embeddings() -> None:
    """
    Orchestrate the process of creating and storing embeddings for all job descriptions.
    """
    keys, descriptions = get_job_descriptions()
    embeddings = generate_embeddings(descriptions)
    store_embeddings(keys, embeddings)
