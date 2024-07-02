import os
import redis


ENV_REDIS_HOST = "REDIS_HOST"

def _to_str(bytemap):
	return {k.decode("utf-8"): v.decode("utf-8") for k,v in bytemap.items()}


class PRState(object):

	def __init__(self, url: str, content: dict):
		self.url = url
		self.content = content

	def contains(self, label):
		return label in self.content

	def get(self, label):
		return self.content.get(label)

	def add(self, label, data):
		self.content[label] = data

	def __bool__(self):
		return bool(self.content)


class RedisBackend(object):

	def __init__(self, redis_client=None):
		if not redis_client:
			if redis_host := os.getenv(ENV_REDIS_HOST):
				redis_client = redis.Redis(host=redis_host)	
			else:
				redis_client = redis.Redis()
		self.client = redis_client


	def get(self, url) -> PRState:
		return PRState(url, _to_str(self.client.hgetall(url)))


	def set(self, state: PRState):
		self.client.hset(state.url, mapping=state.content)

	def delete(self, url, components):
		self.client.hdel(url, *components)

	def get_diff(self, diff_url):
		diff = self.client.get(diff_url)
		return None if not diff else diff.decode("utf-8")

	def set_diff(self, diff_url, diff):
		self.client.set(diff_url, diff, ex=600)

	def clear(self):
		self.client.flushdb()