import redis

r = redis.Redis(
  host='redis-12161.c53.west-us.azure.redns.redis-cloud.com',
  port=12161,
  password='gFHEW6XuTLDLVXzlShXf12KLCDm2SfLm')

# Kiểm tra kết nối
try:
    r.ping()
    print("Kết nối thành công!")
except redis.ConnectionError:
    print("Không thể kết nối tới Redis.")
