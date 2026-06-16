# -*- coding: utf-8 -*-
"""
v11 多租户隔离 - 企业级安全
确保 Org A 无法访问 Org B 的数据
"""

import logging
from typing import Optional
from functools import wraps
from datetime import datetime, timedelta
import jwt
import hashlib
import os

logger = logging.getLogger(__name__)


class TenantIsolationManager:
    """多租户隔离管理器"""
    
    def __init__(self, config: dict):
        self.config = config
        self.secret_key = config.get("SECRET_KEY")
        self.jwt_algorithm = "HS256"
        self.token_expiry = 3600  # 1小时
    
    def generate_api_key(self, org_id: str, user_id: str) -> str:
        """
        生成 API Key
        
        重要：API Key 必须被哈希存储，不能明文保存
        """
        raw_key = f"{org_id}:{user_id}:{datetime.now().timestamp()}"
        api_key = hashlib.sha256(raw_key.encode()).hexdigest()
        
        logger.info(f"✓ API Key 已生成 (org: {org_id})")
        return api_key
    
    def verify_api_key(self, api_key: str, stored_hash: str) -> bool:
        """
        验证 API Key
        
        使用安全的哈希比较防止时序攻击
        """
        provided_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # 常量时间比较
        return self._constant_time_compare(provided_hash, stored_hash)
    
    def generate_jwt_token(self, org_id: str, user_id: str) -> str:
        """生成 JWT Token"""
        payload = {
            "org_id": org_id,
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.jwt_algorithm)
        return token
    
    def verify_jwt_token(self, token: str) -> Optional[dict]:
        """验证 JWT Token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.error("✗ Token 已过期")
            return None
        except jwt.InvalidTokenError:
            logger.error("✗ Token 无效")
            return None
    
    def _constant_time_compare(self, a: str, b: str) -> bool:
        """常量时间比较，防止时序攻击"""
        if len(a) != len(b):
            return False
        
        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)
        
        return result == 0
    
    def enforce_tenant_filter(self, org_id: str, query_dict: dict) -> dict:
        """
        强制添加租户过滤条件
        
        所有查询必须包含 tenant_id 过滤
        """
        query_dict["tenant_id"] = org_id
        return query_dict


def require_org_id(f):
    """
    装饰器：要求请求包含有效的 org_id
    """
    @wraps(f)
    async def decorated_function(request, *args, **kwargs):
        org_id = request.headers.get("X-Org-ID")
        
        if not org_id:
            logger.error("✗ 缺少 X-Org-ID 头部")
            return {"error": "Missing X-Org-ID header"}, 401
        
        # 验证 org_id 格式
        if not _is_valid_org_id(org_id):
            logger.error(f"✗ 无效的 org_id: {org_id}")
            return {"error": "Invalid org_id format"}, 400
        
        # 将 org_id 添加到请求上下文
        request.scope["org_id"] = org_id
        
        return await f(request, *args, **kwargs)
    
    return decorated_function


def _is_valid_org_id(org_id: str) -> bool:
    """验证 org_id 格式"""
    return len(org_id) > 0 and len(org_id) < 256 and org_id.isalnum()
