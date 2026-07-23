import os
from github import Github
from orchestrator import Orchestrator
from decision_engine import DecisionEngine

# 从环境变量读取 GitHub 访问令牌
github_token = os.getenv("GITHUB_TOKEN", "")
if not github_token:
    print("WARNING: GITHUB_TOKEN not set. Set it as an environment variable.")
github_client = Github(github_token) if github_token else None

# 创建 Orchestrator 和 DecisionEngine 实例
orchestrator = Orchestrator(github_client)
decision_engine = DecisionEngine(orchestrator)

# 示例潜在客户数据
lead_data = {
    'conversion_rate': 0.15,  # 示例转化率
    'lead_count': 100          # 示例潜在客户数量
}

# 进行决策
fix_plan = decision_engine.make_decision(lead_data)

if fix_plan:
    print("生成的修复方案:", fix_plan)
else:
    print("没有需要优化的内容。")
