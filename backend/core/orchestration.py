# -*- coding: utf-8 -*-
"""
v11 Orchestration Engine - 核心编排引擎
企业级多Agent系统的大脑
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio
import json
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class Task:
    """任务定义"""
    id: str
    name: str
    agent_type: str
    input_data: Dict[str, Any]
    dependencies: List[str] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.dependencies is None:
            self.dependencies = []


class OrchestrationEngine:
    """
    v11 编排引擎
    
    职责：
    1. 构建任务图
    2. 并行执行任务
    3. 管理Agent状态
    4. 处理错误和重试
    5. 记录审计日志
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化编排引擎"""
        self.config = config
        self.agents = {}
        self.task_queue = []
        self.results = {}
        self.execution_history = []
        
        logger.info("✓ Orchestration Engine v11 初始化成功")
    
    def register_agent(self, agent_type: str, agent_instance):
        """注册 Agent"""
        self.agents[agent_type] = agent_instance
        logger.info(f"✓ Agent '{agent_type}' 已注册")
    
    async def execute_query(
        self, 
        query: str, 
        org_id: str, 
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行查询 - 核心方法
        
        Args:
            query: 用户查询
            org_id: 组织ID（多租户隔离）
            user_id: 用户ID
            metadata: 额外元数据
            
        Returns:
            最终结果
        """
        execution_id = f"exec_{org_id}_{datetime.now().timestamp()}"
        logger.info(f"🚀 开始执行查询: {execution_id}")
        
        try:
            # 第一步：构建任务图
            task_graph = self._build_task_graph(query)
            logger.info(f"📊 任务图已构建: {len(task_graph)} 个任务")
            
            # 第二步：并行执行任务
            results = await self._execute_task_graph(
                task_graph, 
                org_id, 
                user_id,
                execution_id
            )
            
            # 第三步：综合结果
            final_result = await self._synthesize_results(results, query)
            
            # 第四步：记录历史
            self._record_execution(
                execution_id, 
                org_id, 
                user_id, 
                query, 
                final_result
            )
            
            logger.info(f"✓ 查询执行完成: {execution_id}")
            return {
                "execution_id": execution_id,
                "status": "success",
                "result": final_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"✗ 查询执行失败: {str(e)}")
            return {
                "execution_id": execution_id,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _build_task_graph(self, query: str) -> List[Task]:
        """
        构建任务图
        
        这是v11的关键：根据查询类型动态构建任务流
        """
        tasks = []
        
        # 第一阶段：理解
        tasks.append(Task(
            id="task_1",
            name="intent_classification",
            agent_type="classifier",
            input_data={"query": query}
        ))
        
        # 第二阶段：提取
        tasks.append(Task(
            id="task_2",
            name="entity_extraction",
            agent_type="extractor",
            input_data={"query": query},
            dependencies=["task_1"]
        ))
        
        # 第三阶段：检索
        tasks.append(Task(
            id="task_3",
            name="memory_retrieval",
            agent_type="retriever",
            input_data={"query": query},
            dependencies=["task_2"]
        ))
        
        # 第四阶段：分析
        tasks.append(Task(
            id="task_4",
            name="trend_analysis",
            agent_type="analyzer",
            input_data={"query": query},
            dependencies=["task_3"]
        ))
        
        # 第五阶段：生成
        tasks.append(Task(
            id="task_5",
            name="insight_generation",
            agent_type="synthesizer",
            input_data={"query": query},
            dependencies=["task_4"]
        ))
        
        return tasks
    
    async def _execute_task_graph(
        self, 
        task_graph: List[Task],
        org_id: str,
        user_id: str,
        execution_id: str
    ) -> Dict[str, Any]:
        """
        并行执行任务图
        
        支持依赖关系的异步执行
        """
        results = {}
        pending_tasks = {t.id: t for t in task_graph}
        
        while pending_tasks:
            # 找出可执行的任务（依赖已完成）
            executable = [
                t for t in pending_tasks.values()
                if all(dep in results for dep in t.dependencies)
            ]
            
            if not executable:
                break
            
            # 并行执行
            tasks_to_run = [
                self._execute_single_task(t, org_id, user_id, results)
                for t in executable
            ]
            
            task_results = await asyncio.gather(*tasks_to_run)
            
            # 记录结果
            for task, result in zip(executable, task_results):
                results[task.id] = result
                del pending_tasks[task.id]
                logger.info(f"✓ 任务完成: {task.name}")
        
        return results
    
    async def _execute_single_task(
        self,
        task: Task,
        org_id: str,
        user_id: str,
        previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行单个任务"""
        try:
            # 获取Agent
            agent = self.agents.get(task.agent_type)
            if not agent:
                raise ValueError(f"Agent '{task.agent_type}' not found")
            
            # 准备输入
            task_input = task.input_data.copy()
            
            # 注入前序结果
            for dep_id in task.dependencies:
                if dep_id in previous_results:
                    task_input[f"prev_{dep_id}"] = previous_results[dep_id]
            
            # 执行（支持异步Agent）
            if hasattr(agent, 'execute_async'):
                result = await agent.execute_async(task_input, org_id)
            else:
                result = agent.execute(task_input, org_id)
            
            task.status = TaskStatus.COMPLETED
            task.result = result
            
            return result
            
        except Exception as e:
            logger.error(f"✗ 任务执行失败 {task.name}: {str(e)}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            return {"error": str(e)}
    
    async def _synthesize_results(
        self,
        results: Dict[str, Any],
        original_query: str
    ) -> Dict[str, Any]:
        """综合最终结果"""
        synthesizer = self.agents.get("synthesizer")
        
        if not synthesizer:
            return {"raw_results": results}
        
        final_result = await synthesizer.synthesize(
            results=results,
            original_query=original_query
        )
        
        return final_result
    
    def _record_execution(
        self,
        execution_id: str,
        org_id: str,
        user_id: str,
        query: str,
        result: Dict[str, Any]
    ):
        """记录执行历史（审计日志）"""
        record = {
            "execution_id": execution_id,
            "org_id": org_id,
            "user_id": user_id,
            "query": query,
            "result_preview": str(result)[:500],
            "timestamp": datetime.now().isoformat()
        }
        
        self.execution_history.append(record)
        logger.info(f"📝 执行记录已保存: {execution_id}")
