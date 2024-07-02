from components import *
from openai import OpenAI
from abc import ABC, abstractmethod
from typing import List
import json, os, pprint


ENV_OPENAI_ORG_ID = "OPENAI_ORG_ID"
ENV_OPENAI_PROJECT_ID = "OPENAI_PROJECT_ID"
ENV_OPENAI_API_KEY = "OPENAI_API_KEY"

def _get_env(var_name):
	value = os.getenv(var_name)
	if not value:
		raise Exception(f"{var_name} not set")
	return value


def _strip_code_block(content):
	if content.startswith("```json"):
		content = content.strip("`json\n")
	return content


class AIClient(object):

	def __init__(self, organization=None, project=None, api_key=None, model="gpt-3.5-turbo", **kwargs):
		if not organization:
			organization = _get_env(ENV_OPENAI_ORG_ID)
		if not project:
			project = _get_env(ENV_OPENAI_PROJECT_ID)
		if not api_key:
			api_key = _get_env(ENV_OPENAI_API_KEY)
		self.client = OpenAI(organization=organization, project=project, api_key=api_key)
		print(f"USING MODEL {model}")
		self.model = model

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
			print(e.message)
