from concurrent.futures import ThreadPoolExecutor, wait
from typing import List
import requests
from client import AIClient
from components import AnalysisComponent
from config import ForgeConfig


def download_diff(diff_url):
	print(f"fetching diff for {diff_url}")
	return requests.get(diff_url).content.decode("utf-8")


def _do_request(client, diff, component, results_list):
	print(f"sending request for {component.label}")
	response = client.request(diff, component)
	results_list.append((component.label, response))
	print(f"request for {component.label} finished")


class PullRequestAnalyzer(object):

	def __init__(self, config: ForgeConfig, client: AIClient = None):
		if not client:
			print("initializing default OpenAI client")
			client = AIClient(**config.gpt_config)
		self.client = client


	def analyze_pr(self, diff, components: List[AnalysisComponent]):
		results = []
		futures = []
		with ThreadPoolExecutor(max_workers=4) as executor:
			for component in components:
				futures.append(executor.submit(_do_request, self.client, diff, component, results))
		wait(futures)
		return results