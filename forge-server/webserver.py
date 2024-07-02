from flask import Flask, request
import flask_cors
from flask_cors import CORS, cross_origin
import pprint, json, requests, asyncio
from pr_analyzer import PullRequestAnalyzer, download_diff
from components import ComponentLoader, ComponentRegistry
from state import PRState, RedisBackend
from typing import List

app = Flask(__name__)

cors = CORS(app)

component_registry = ComponentRegistry()
analyzer = PullRequestAnalyzer()
state_provider = RedisBackend()


def _get_diff(pr_url):
	diff_url = pr_url if pr_url.endswith(".diff") else pr_url + ".diff"
	diff = state_provider.get_diff(diff_url)
	if not diff:
		diff = download_diff(diff_url)
		state_provider.set_diff(diff_url, diff)
	return diff


def get_analysis_results(pr_url, components) -> PRState:
	state: PRState = state_provider.get(pr_url)
	missing_components = [component for component in components if not state.contains(component.label)]
	if missing_components:
		print(f"state for {pr_url} missing {[c.label for c in missing_components]}")
		diff = _get_diff(pr_url)
		response = analyzer.analyze_pr(diff, missing_components)
		for label, data in response:
			state.add(label, data)
		state_provider.set(state)
	else:
		print(f"all required state for {pr_url} exists")

	return state


def _analyze(pr_url, components, refresh=False):
	if refresh:
		print(f"clearing state for {pr_url}")
		state_provider.delete(pr_url, [c.label for c in components])
	return get_analysis_results(pr_url, components)


def _get_url():
	return request.args.get("url")


def _is_refresh():
	val = request.args.get("refresh")
	return val and val.lower() == "true"


@app.route("/comments")
def analyze_comments():
	component = component_registry.get("comments")
	pr_url = _get_url()
	if not pr_url:
		return "missing required 'url' parameter", 400
	analysis_state = _analyze(pr_url, [component], refresh=_is_refresh())
	response_object = json.loads(analysis_state.get("comments"))
	return response_object, 200
	


@app.route("/analyze/<component_name>")
def analyze_component(component_name):
	component = component_registry.get(component_name)
	if not component:
		return f"invalid component: {component_name}", 400
	pr_url = _get_url()
	if not pr_url:
		return "missing required 'url' parameter", 400
	analysis_state =_analyze(pr_url, [component], refresh=_is_refresh())
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

if __name__ == "__main__":
    app.run(debug=True)