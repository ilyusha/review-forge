from abc import ABC, abstractmethod
from typing import List
import yaml, pprint, os, hashlib, logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from config import ForgeConfig

class Msg(object):

	def __init__(self, role, content):
		self.role = role
		self.content = content

	def to_json(self):
		return {"role": self.role, "content": self.content}


class SystemMsg(Msg):

	def __init__(self, prompt):
		super().__init__("system", prompt)


class UserMsg(Msg):

	def __init__(self, prompt):
		super().__init__("user", prompt)


class AnalysisComponent(ABC):

	@abstractmethod
	def get_system_messages(self) -> List[str]:
		pass

	@abstractmethod
	def get_user_messages(self, prompt) -> List[str]:
		pass

	@abstractmethod
	def get_label(self):
		pass

	@property
	def label(self):
		return self.get_label()

	def build_messages(self, diff) -> List[Msg]:
		messages = []
		messages.extend([SystemMsg(msg).to_json() for msg in self.get_system_messages()])
		messages.extend([UserMsg(msg).to_json() for msg in self.get_user_messages(diff)])
		return messages


class YamlComponent(AnalysisComponent):

	def __init__(self, spec: dict):
		self.system_prompts = []
		self.user_prompts = []
		for prompt_spec in spec['prompts']:
			self.configure_prompt(prompt_spec)

	def configure_prompt(self, prompt_spec: dict):
		prompt_type = prompt_spec['type']
		prompt_path = prompt_spec['path']
		dest_list = self.system_prompts if prompt_type == "system" else self.user_prompts
		self._load_prompt(prompt_path, dest_list)

	def _load_prompt(self, path, dest_list):
		with open(path, "r") as f:
			contents = f.read()
			dest_list.append(contents)

	def get_system_messages(self):
		return self.system_prompts


class DefaultComponent(YamlComponent):

	def __init__(self, spec: dict):
		super().__init__(spec)
		self._label = spec['label']

	def get_label(self):
		return self._label

	def get_user_messages(self, diff):
		messages = []
		messages.extend(self.user_prompts)
		messages.append(diff)
		return messages


class UserInputComponent(YamlComponent):

	def __init__(self, spec: dict, user_input):
		super().__init__(spec)
		self.user_input = user_input
		self.input_hash = hashlib.md5(self.user_input.encode('utf-8')).hexdigest()

	def get_label(self):
		return f"custom-{self.input_hash}"

	def get_user_messages(self, diff):
		messages = []
		messages.extend(self.user_prompts)
		messages.extend([self.user_input, diff])
		return messages


class ComponentRegistry(object):

	def __init__(self, config):
		self.components = [DefaultComponent(spec) for spec in config.components]
		self.by_label = {component.label: component for component in self.components}

	def get(self, label):
		return self.by_label.get(label)

	def labels(self):
		return sorted(list(self.by_label.keys()))
