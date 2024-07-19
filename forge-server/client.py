from components import *
from openai import OpenAI
from abc import ABC, abstractmethod
from typing import List
import json, os, pprint, logging

ENV_OPENAI_API_KEY = "OPENAI_API_KEY"

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def _get_env(var_name):
	value = os.getenv(var_name)
	if not value:
		raise Exception(f"{var_name} not set")
	return value


def _strip_code_block(content):
	if content.startswith("```json"):
		content = content.strip("`json\n")
	return content


class OpenAIClient(object):

	def __init__(self, api_key=None, model="gpt-3.5-turbo", **kwargs):
		if not api_key:
			api_key = _get_env(ENV_OPENAI_API_KEY)
		self.client = OpenAI(api_key=api_key)
		self.model = model
		logger.info(f"using OpenAI model {self.model}")

	def _build_request(self, prompt, analysis_component):
		return {
			"model": self.model,
			"messages": analysis_component.build_messages(prompt)
		}

	def request(self, prompt, analysis_component: AnalysisComponent):
		try:
			request = self._build_request(prompt, analysis_component)
			response = self.client.chat.completions.create(**request)
			return _strip_code_block(response.choices[0].message.content)
		except Exception as e:
			logger.error(e)
