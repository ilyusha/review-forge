import os, yaml

ENV_CONFIG_FILE = "FORGE_CONFIG_FILE"

class ForgeConfig(object):

	def __init__(self, config_file = None):
		if not config_file:
			config_file = os.getenv(ENV_CONFIG_FILE)
			if not config_file:
				raise Exception(f"{ENV_CONFIG_FILE} not set")
		with open(config_file, "r") as f:
			config = yaml.safe_load(f)
			self.components = config['components']
			self.gpt_config = config.get('gpt', {})