# -*- coding: utf-8 -*-
"""
v11 API Gateway
企业级 FastAPI 应用
"""

import logging
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import time

from backend.core.orchestration import OrchestrationEngine
from backend.core.agents import AgentPool
from backend.security.tenant_isolation import TenantIsolationManager

logger = logging.getLogger(__name__)

# 初始化 FastAPI
app = FastAPI(
    title="Codex AI v11",
    version="11.0.0",
    description="Enterprise AI Intelligence Platform"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化核心组件
config = {
    "SECRET_KEY": "your-secret-key-here",
    "MAX_REQUESTS_PER_MINUTE": 100
}

agent_pool = AgentPool()
orchestration_engine = OrchestrationEngine(config)
tenant_manager = TenantIsolationManager(config)

# 注册所有 Agent
for agent_type, agent in agent_pool.get_all_agents().items():
    orchestration_engine.register_agent(agent_type, agent)

logger.info("✓ v11 API Gateway 启动成功")


# ============================================================================
# 路由
# ============================================================================

@app.post("/v1/query")
async def query(
    request: Request,
    org_id: str,
    user_id: str,
    query: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    核心查询端点
    
    Args:
        org_id: 组织ID（多租户隔离）
        user_id: 用户ID
        query: 查询字符串
        metadata: 额外元数据
    """
    
    # 验证租户
    if not _verify_tenant(org_id, user_id):
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # 执行查询
    result = await orchestration_engine.execute_query(
        query=query,
        org_id=org_id,
        user_id=user_id,
        metadata=metadata
    )
    
    return result


@app.get("/v1/health")
async def health_check() -> Dict[str, Any]:
    """健康检查"""
    return {
        "status": "healthy",
        "version": "11.0.0",
        "agents": agent_pool.health_check()
    }


@app.get("/v1/insights/{execution_id}")
async def get_insight(
    execution_id: str,
    org_id: str
) -> Dict[str, Any]:
    """获取洞察结果"""
    
    # 在实际系统中，这将从数据库检索
    return {
        "execution_id": execution_id,
        "org_id": org_id,
        "status": "completed",
        "insight": "sample insight"
    }


# ============================================================================
# 辅助函数
# ============================================================================

def _verify_tenant(org_id: str, user_id: str) -> bool:
    """验证租户和用户"""
    # 在实际系统中，这将验证 org_id 和 user_id
    return True


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """添加处理时间"""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 启动 v11 API Server")
    logger.info("📝 API 文档: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
