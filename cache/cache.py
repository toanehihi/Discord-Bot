import redis, os, json
    
    
class RedisCache:
    def __init__(self, host = 'redis-12161.c53.west-us.azure.redns.redis-cloud.com', port = 12161,password = 'gFHEW6XuTLDLVXzlShXf12KLCDm2SfLm', db=0):
        self.redis_client = redis.Redis(host=host, port=port, password=password, db=db)
    
    def set_song_url(self, song_url, sound_url, expire = 21600):
        self.redis_client.set( song_url,sound_url, expire)
    def get_song_url(self, song_url):
        return self.redis_client.get(song_url)

