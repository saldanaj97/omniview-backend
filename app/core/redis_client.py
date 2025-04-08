import redis

# Create a Redis connection that can be imported anywhere
redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True, db=0)
