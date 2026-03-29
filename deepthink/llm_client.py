"""
llm_client — 统一模型调用入口
支持 QClaw 本地代理 / OpenAI / DeepSeek
"""

import os
import json
import urllib.request
import urllib.error
import socket
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum


class ModelProvider(Enum):
    QCLAW = "qclaw"       # QClaw 本地代理 (默认)
    OPENAI = "openai"     # OpenAI API
    DEEPSEEK = "deepseek" # DeepSeek API


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: ModelProvider = ModelProvider.QCLAW
    model: str = "modelroute"
    api_key: str = ""
    base_url: str = "http://127.0.0.1:19000/proxy/llm"
    timeout: int = 120
    max_retries: int = 2


class LLMClient:
    """
    统一 LLM 客户端
    
    用法:
        client = LLMClient()
        resp = client.chat("你好")
        print(resp)
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or self._load_config()
        self._session_count = 0
    
    # ========== 配置加载 ==========
    
    def _load_config(self) -> LLMConfig:
        """从环境变量/配置文件加载配置"""
        # 优先使用环境变量
        provider_str = os.environ.get("DEEPTHINK_PROVIDER", "qclaw").lower()
        
        if provider_str == "openai":
            return LLMConfig(
                provider=ModelProvider.OPENAI,
                model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                api_key=os.environ.get("OPENAI_API_KEY", ""),
                base_url="https://api.openai.com/v1",
            )
        elif provider_str == "deepseek":
            return LLMConfig(
                provider=ModelProvider.DEEPSEEK,
                model=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
                api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
                base_url="https://api.deepseek.com/v1",
            )
        else:
            # QClaw 本地代理
            return LLMConfig(
                provider=ModelProvider.QCLAW,
                model=os.environ.get("QCLAW_MODEL", "modelroute"),
                api_key=os.environ.get("QCLAW_LLM_API_KEY", "__QCLAW_AUTH_TOKEN"),
                base_url=os.environ.get("QCLAW_LLM_BASE_URL", "http://127.0.0.1:19000/proxy/llm"),
                timeout=int(os.environ.get("QCLAW_LLM_TIMEOUT", "30")),
            )
    
    # ========== 核心调用 ==========
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        发送对话请求，返回文本内容
        
        Args:
            messages: [{"role": "user", "content": "..."}]
            model: 覆盖默认模型
            temperature: 温度参数
            max_tokens: 最大 token 数
            timeout: 覆盖默认超时（秒）
        
        Returns:
            模型回复的文本
        """
        model = model or self.config.model
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs
        }
        
        content = self._post(payload, timeout=timeout)
        return content
    
    def chat_once(
        self,
        prompt: str,
        system: str = "",
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        timeout: Optional[int] = None,
    ) -> str:
        """单轮对话（最常用）"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages, model=model, temperature=temperature, max_tokens=max_tokens, timeout=timeout)
    
    # ========== 内部实现 ==========
    
    def _post(self, payload: dict, timeout: Optional[int] = None) -> str:
        """发送 POST 请求，带重试"""
        last_err = None
        effective_timeout = timeout or self.config.timeout

        for attempt in range(self.config.max_retries):
            try:
                return self._do_post(payload, timeout=effective_timeout)
            except (urllib.error.HTTPError, urllib.error.URLError, socket.timeout, TimeoutError) as e:
                last_err = e
                if attempt < self.config.max_retries - 1:
                    wait = 2 ** attempt
                    print(f"  ⚠️ 请求失败（{attempt+1}次），{wait}秒后重试... {type(e).__name__}")

        raise RuntimeError(f"LLM 调用失败（已重试{self.config.max_retries}次）: {last_err}")

    def _do_post(self, payload: dict, timeout: Optional[int] = None) -> str:
        """执行 POST 请求"""
        url = self._get_url()
        body = json.dumps(payload).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }

        req = urllib.request.Request(
            url,
            data=body,
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=timeout or self.config.timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
        
        # 解析响应
        return self._parse_response(data)
    
    def _get_url(self) -> str:
        """获取 API URL"""
        if self.config.provider == ModelProvider.OPENAI:
            return f"{self.config.base_url.rstrip('/')}/chat/completions"
        elif self.config.provider == ModelProvider.DEEPSEEK:
            return f"{self.config.base_url.rstrip('/')}/chat/completions"
        else:
            # QClaw: 无 /v1 前缀
            return f"{self.config.base_url.rstrip('/')}/chat/completions"
    
    def _parse_response(self, data: dict) -> str:
        """解析 API 响应"""
        if "choices" in data:
            return data["choices"][0]["message"]["content"].strip()
        elif "error" in data:
            raise RuntimeError(f"API Error: {data['error']}")
        else:
            raise RuntimeError(f"未知响应格式: {data}")
    
    # ========== 工具方法 ==========
    
    def set_timeout(self, seconds: int):
        """修改超时时间"""
        self.config.timeout = seconds
    
    def __repr__(self):
        return f"LLMClient(provider={self.config.provider.value}, model={self.config.model})"


# ========== 全局单例 ==========

_client: Optional[LLMClient] = None


def get_client() -> LLMClient:
    """获取全局 LLM 客户端（延迟初始化）"""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client


# ========== 单元测试 ==========

if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    
    print("🦞 LLM Client 测试")
    print("=" * 50)
    
    client = get_client()
    print(f"配置: {client}")
    
    # 快速测试
    resp = client.chat_once("你好，介绍一下自己", max_tokens=100)
    print(f"回复: {resp}")
    
    # 多轮对话
    resp2 = client.chat([
        {"role": "user", "content": "1+1等于几？"},
        {"role": "assistant", "content": "2"},
        {"role": "user", "content": "再加2呢？"},
    ], max_tokens=50)
    print(f"多轮回复: {resp2}")
    
    print("✅ LLM Client 测试通过！")
