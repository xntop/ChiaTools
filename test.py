from utils import delta_to_str, size_to_str
from datetime import timedelta
import time


d1 = timedelta(days=0)
d2 = timedelta(seconds=60*60*18+323)

d = d2 - d1

s = delta_to_str(d)
print(s)

print(size_to_str(2**30))
