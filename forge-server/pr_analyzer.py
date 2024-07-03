from concurrent.futures import ThreadPoolExecutor, wait
from typing import List
import requests
from client import OpenAIClient
from components import AnalysisComponent
from config import ForgeConfig
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def download_diff(diff_url):
	logger.info(f"fetching diff for {diff_url}")
	return requests.get(diff_url).content.decode("utf-8")


def _do_request(client, diff, component, results_list):
	logger.info(f"sending request for {component.label}")
	response = client.request(diff, component)
	results_list.append((component.label, response))
	logger.info(f"request for {component.label} finished")


class PullRequestAnalyzer(object):

	def __init__(self, config: ForgeConfig, client: OpenAIClient = None):
		if not client:
			logger.info("initializing default OpenAI client")
			client = OpenAIClient(**config.gpt)
		self.client = client


	def analyze_pr(self, diff, components: List[AnalysisComponent]):
		results = []
		futures = []
		with ThreadPoolExecutor(max_workers=4) as executor:
			for component in components:
				futures.append(executor.submit(_do_request, self.client, diff, component, results))
		wait(futures)
		return results