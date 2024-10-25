import redis

r = redis.Redis(host='localhost', port=6379, db=0)

r.set("France", "Paris")
r.set("UK", "London")

france_capital = r.get("France")
uk_capital = r.get("UK")

print(france_capital)
print(uk_capital)