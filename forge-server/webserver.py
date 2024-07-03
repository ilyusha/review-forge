import pprint, json, requests, logging, hashlib
from typing import List
from flask import Flask, request
import flask_cors
from flask_cors import CORS, cross_origin
from config import ForgeConfig
from pr_analyzer import PullRequestAnalyzer, download_diff
from components import ComponentRegistry, UserInputComponent
from state import PRState, RedisBackend

from dataclasses import dataclass

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

cors = CORS(app)

config = ForgeConfig()
component_registry = ComponentRegistry(config)
analyzer = PullRequestAnalyzer(config)
state_provider = RedisBackend()


@dataclass
class DiffInfo:
	diff_id: str
	diff: str


def _get_diff(pr_url):
	diff_url = pr_url if pr_url.endswith(".diff") else pr_url + ".diff"
	diff = state_provider.get_diff(diff_url)
	if not diff:
		diff = download_diff(diff_url)
		state_provider.set_diff(diff_url, diff)
	return diff

def get_analysis_results(components, diff_info) -> PRState:
	state_id = diff_info.diff_id
	state: PRState = state_provider.get(state_id)
	missing_components = [component for component in components if not state.contains(component.label)]
	if missing_components:
		logger.info(f"state for {state_id} missing {[c.label for c in missing_components]}")
		response = analyzer.analyze_pr(diff_info.diff, missing_components)
		for label, data in response:
			state.add(label, data)
		state_provider.set(state)
	else:
		logger.info(f"all required state for {state_id} exists")

	return state


def _analyze(components, diff_info, refresh=False):
	if refresh:
		logger.info(f"clearing state for {pr_url}")
		state_provider.delete(pr_url, [c.label for c in components])
	return get_analysis_results(components, diff_info)


def _get_url():
	return request.args.get("url")


def _is_refresh():
	val = request.args.get("refresh")
	return val and val.lower() == "true"


def get_diff_from_request() -> DiffInfo:
	pr_url = diff = None
	if request.method == "GET":
		pr_url = _get_url()
		if not pr_url:
			raise Exception("missing required 'url' parameter")
		diff = _get_diff(pr_url)
		return DiffInfo(pr_url, diff)
	else:
		diff_bytes = request.get_data()
		diff_hash = hashlib.md5(diff_bytes).hexdigest()
		return DiffInfo(diff_hash, diff_bytes.decode("utf-8"))


@app.route("/comments", methods=["GET", "POST"])
def analyze_comments():
	component = component_registry.get("comments")
	diff_info = get_diff_from_request()
	analysis_state = _analyze([component], diff_info, refresh=_is_refresh())
	response_object = json.loads(analysis_state.get("comments"))
	return response_object, 200


@app.route("/analyze/<component_name>", methods=["GET", "POST"])
def analyze_component(component_name):
	component = component_registry.get(component_name)
	if not component:
		return f"invalid component: {component_name}", 400
	diff_info = get_diff_from_request()
	analysis_state = _analyze([component], diff_info, refresh=_is_refresh())
	component_result = analysis_state.get(component_name)
	return component_result, 200


@app.route("/diff")
def get_diff():
	pr_url = _get_url()
	if not pr_url:
		return "missing required 'url' parameter", 400
	diff_url = pr_url if pr_url.endswith(".diff") else pr_url + ".diff"
	return _get_diff(diff_url)


@app.route("/components")
def get_components():
	return component_registry.labels(), 200


@app.route("/clear-cache", methods=["POST"])
def clear_cache():
	state_provider.clear()
	return "OK", 200


@app.route("/custom", methods=["POST"])
def analyze_custom():
	pr_url = _get_url()
	if not pr_url:
		return "missing required 'url' parameter", 400
		
	try:
		prompt = request.json.get('prompt')
	except Exception as e:
		return "missing prompt", 400
	component = UserInputComponent(config.user_input, prompt)
	analysis_state =_analyze(pr_url, [component], refresh=_is_refresh())
	component_result = analysis_state.get(component.label)
	return component_result, 200


if __name__ == "__main__":
    app.run(debug=True)