import os
from github import Github, Auth

ENV_GITHUB_TOKEN = "GITHUB_TOKEN"
ENV_GITHUB_BASE_URL = "GITHUB_BASE_URL"
ENV_FORGE_URL = "FORGE_URL"

class GithubClient(object):

	def __init__(self, token=None, base_url=None, forge_url=None):
		if not token:
			token = os.getenv(ENV_GITHUB_TOKEN)
			if not token: raise Exception(f"{ENV_GITHUB_TOKEN} not specified")
		if not base_url:
			base_url = os.getenv(ENV_GITHUB_BASE_URL)
			if not base_url: raise Exception(f"{ENV_GITHUB_BASE_URL} not specified")
		if not forge_url:
			forge_url = os.getenv(ENV_FORGE_URL)
			if not forge_url: raise Exception(f"{ENV_FORGE_URL} not specified")
			self.forge_url = forge_url
		self.client = Github(auth=Auth.Token(token))

	def handle_webhook(self, payload):
		repo_id = payload['repository']['id']
		pr_num = payload['pull_request']['number']
		pr_url = payload['pull_request']['html_url']
		redirect = f"{self.forge_url}?prUrl={pr_url}"
		repo = self.client.get_repo(repo_id)
		pr = repo.get_pull(pr_num)
		comment = []
		comment.append("### Review Forge")
		comment.append(f"[Click Here for AI Insights]({redirect})")
		pr.create_issue_comment("\n".join(comment))