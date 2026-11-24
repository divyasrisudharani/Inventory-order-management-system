from app.redis_client import redis_client

try:
    redis_client.set("redis_test", "connected")

    result = redis_client.get("redis_test")

    print("Redis connection successful!")
    print("Test result:", result)

except Exception as e:
    print("Redis connection failed:", e)