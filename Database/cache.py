import redis
from fuzzywuzzy import fuzz
redis_client = redis.Redis(host='localhost', port=6379, db=0)
#======
def normalize(title):
    return title.lower().replace(' ','')
def similar_title(title1,title2):
    title1 = normalize(title1)
    title2 = normalize(title2)
    return fuzz.ratio(title1,title2)
#======

def cache_song(title,data_url):
    redis_client.set(title,data_url)

def get_cache_song(title):
    return redis_client.keys(title)


