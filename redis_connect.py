import redis

redis_client = redis.Redis(host='localhost', port=6380, db=0, decode_responses=True)
def save_to_redis(key: str, value: set):

    redis_client.sadd(key, *value)

    print(f"Saved to Redis: {key} -> {value}")
   

def get_from_redis(key: str):
    value =  redis_client.smembers(key)
    print(f"Fetched from Redis: {key} -> {value}")
    return value
