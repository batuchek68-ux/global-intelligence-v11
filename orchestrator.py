import os


class Orchestrator:
    def __init__(self, github_client):
        self.github_client = github_client
        self.repo_name = os.getenv("GITHUB_REPO", "global-intelligence-v11")

    def check_workflow_status(self, workflow_name):
        if not self.github_client:
            return "no_client"
        repo = self.github_client.get_user().get_repo(self.repo_name)
        workflows = repo.get_workflows()
        for workflow in workflows:
            if workflow.name == workflow_name:
                return workflow.state
        return None

    def analyze_leads(self, lead_data):
        # 分析潜在客户数据
        if self.is_conversion_rate_low(lead_data):
            return {
                "action": "optimize_workflow",
                "target": "lead_acquisition",
                "reason": "conversion rate low"
            }
        return None

    def is_conversion_rate_low(self, lead_data):
        # 判断转化率是否低于阈值
        conversion_rate = lead_data['conversion_rate']
        return conversion_rate < 0.2  # 假设阈值为20%

    def generate_fix_plan(self, optimization_action):
        # 根据优化行动生成修复方案
        if optimization_action['target'] == "lead_acquisition":
            return {
                "modify_n8n_nodes": True,
                "adjust_scoring_model": True,
                "replace_api": False
            }

    def commit_changes(self, message):
        if not self.github_client:
            return None
        repo = self.github_client.get_user().get_repo(self.repo_name)
        repo.create_git_commit(message, [], [])
