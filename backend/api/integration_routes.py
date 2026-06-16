# -*- coding: utf-8 -*-
"""
集成路由 - Codex 和 n8n 之间的通信
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
import logging

from backend.integrations.n8n_connector import N8NConnector
from backend.integrations.event_bus import EventBus, EventTypes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])

# 初始化连接器
n8n_connector = N8NConnector(
    n8n_url="http://localhost:5678",
    api_key="your-n8n-api-key"
)

event_bus = EventBus()


@router.post("/n8n/trigger/{workflow_id}")
async def trigger_n8n_workflow(
    workflow_id: str,
    org_id: str,
    user_id: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    从 Codex 触发 n8n 工作流
    
    使用场景：
    - 查询完成后自动触发获客工作流
    - 发送通知
    - 数据同步
    """
    
    try:
        result = n8n_connector.trigger_workflow(
            workflow_id=workflow_id,
            input_data=data,
            org_id=org_id
        )
        
        # 发布事件
        await event_bus.publish(
            EventTypes.WORKFLOW_TRIGGERED,
            {
                "workflow_id": workflow_id,
                "org_id": org_id,
                "execution_id": result.get("workflow_execution_id")
            }
        )
        
        return {
            "status": "success",
            "workflow_id": workflow_id,
            "execution_id": result.get("workflow_execution_id")
        }
    
    except Exception as e:
        logger.error(f"✗ 触发工作流失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/n8n/workflows")
async def list_n8n_workflows(org_id: str) -> Dict[str, Any]:
    """列出所有 n8n 工作流"""
    
    try:
        workflows = n8n_connector.list_workflows()
        
        return {
            "status": "success",
            "workflows": workflows
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/n8n/webhook")
async def n8n_webhook(request: Request) -> Dict[str, Any]:
    """
    n8n 回调 Webhook
    
    n8n 工作流完成时调用此端点
    """
    
    try:
        body = await request.json()
        
        logger.info(f"📡 收到 n8n Webhook 回调")
        
        # 发布事件
        await event_bus.publish(
            EventTypes.WORKFLOW_COMPLETED,
            {
                "workflow_execution_id": body.get("executionId"),
                "status": body.get("status"),
                "data": body.get("data")
            }
        )
        
        return {"status": "received"}
    
    except Exception as e:
        logger.error(f"✗ Webhook 处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-data")
async def sync_codex_n8n_data(
    org_id: str,
    sync_type: str = "insights"
) -> Dict[str, Any]:
    """
    同步数据
    
    同步类型：
    - insights: 同步洞察数据
    - leads: 同步线索数据
    - campaigns: 同步活动数据
    """
    
    try:
        logger.info(f"🔄 开始数据同步: {sync_type} (org: {org_id})")
        
        # 根据同步类型执行不同的逻辑
        if sync_type == "insights":
            # 从 Codex 获取最新洞察
            # 推送到 n8n
            pass
        
        elif sync_type == "leads":
            # 从 n8n 获取线索
            # 保存到 Codex
            pass
        
        return {
            "status": "success",
            "sync_type": sync_type,
            "org_id": org_id
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
