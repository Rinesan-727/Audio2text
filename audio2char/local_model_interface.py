#!/usr/bin/env python3
"""
本地模型接口
支持多种本地大模型部署方案，包括Ollama、LM Studio、vLLM等
"""

import requests
import json
import os
import time
from typing import Optional, Dict, Any

class LocalModelInterface:
    """本地大模型接口类"""
    
    def __init__(self, model_type: str = "ollama", **kwargs):
        """
        初始化本地模型接口
        
        Args:
            model_type: 模型类型 ("ollama", "lmstudio", "vllm", "openai_local")
            **kwargs: 其他配置参数
        """
        self.model_type = model_type.lower()
        self.config = self._get_default_config()
        self.config.update(kwargs)
        
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "ollama": {
                "base_url": "http://localhost:11434",
                "model_name": "qwen2.5:7b",
                "timeout": 60
            },
            "lmstudio": {
                "base_url": "http://localhost:1234",
                "model_name": "local-model",
                "timeout": 60
            },
            "vllm": {
                "base_url": "http://localhost:8000",
                "model_name": "qwen2.5-7b",
                "timeout": 60
            },
            "openai_local": {
                "base_url": "http://localhost:8080",
                "model_name": "local-model",
                "timeout": 60
            }
        }
    
    def chat_completion(self, messages: list, **kwargs) -> Optional[str]:
        """
        调用本地大模型进行对话
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            **kwargs: 其他参数
            
        Returns:
            模型响应文本，失败返回None
        """
        try:
            if self.model_type == "ollama":
                return self._call_ollama(messages, **kwargs)
            elif self.model_type == "lmstudio":
                return self._call_lmstudio(messages, **kwargs)
            elif self.model_type == "vllm":
                return self._call_vllm(messages, **kwargs)
            elif self.model_type == "openai_local":
                return self._call_openai_local(messages, **kwargs)
            else:
                print(f"❌ 不支持的模型类型: {self.model_type}")
                return None
        except Exception as e:
            print(f"❌ 本地模型调用失败: {e}")
            return None
    
    def _call_ollama(self, messages: list, **kwargs) -> Optional[str]:
        """调用Ollama模型"""
        config = self.config["ollama"]
        
        # 构建Ollama格式的请求
        prompt = self._messages_to_prompt(messages)
        
        payload = {
            "model": config["model_name"],
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.3),
                "top_p": kwargs.get("top_p", 0.9),
                "max_tokens": kwargs.get("max_tokens", 2000)
            }
        }
        
        try:
            response = requests.post(
                f"{config['base_url']}/api/generate",
                json=payload,
                timeout=config["timeout"]
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                print(f"❌ Ollama API错误: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Ollama连接失败: {e}")
            return None
    
    def _call_lmstudio(self, messages: list, **kwargs) -> Optional[str]:
        """调用LM Studio模型"""
        config = self.config["lmstudio"]
        
        payload = {
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.3),
            "max_tokens": kwargs.get("max_tokens", 2000),
            "stream": False
        }
        
        try:
            response = requests.post(
                f"{config['base_url']}/v1/chat/completions",
                json=payload,
                timeout=config["timeout"]
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"❌ LM Studio API错误: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ LM Studio连接失败: {e}")
            return None
    
    def _call_vllm(self, messages: list, **kwargs) -> Optional[str]:
        """调用vLLM模型"""
        config = self.config["vllm"]
        
        payload = {
            "model": config["model_name"],
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.3),
            "max_tokens": kwargs.get("max_tokens", 2000),
            "stream": False
        }
        
        try:
            response = requests.post(
                f"{config['base_url']}/v1/chat/completions",
                json=payload,
                timeout=config["timeout"]
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"❌ vLLM API错误: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ vLLM连接失败: {e}")
            return None
    
    def _call_openai_local(self, messages: list, **kwargs) -> Optional[str]:
        """调用本地OpenAI兼容API"""
        config = self.config["openai_local"]
        
        payload = {
            "model": config["model_name"],
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.3),
            "max_tokens": kwargs.get("max_tokens", 2000),
            "stream": False
        }
        
        try:
            response = requests.post(
                f"{config['base_url']}/v1/chat/completions",
                json=payload,
                timeout=config["timeout"]
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"❌ 本地OpenAI API错误: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 本地OpenAI连接失败: {e}")
            return None
    
    def _messages_to_prompt(self, messages: list) -> str:
        """将消息列表转换为提示词"""
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                prompt += f"系统: {content}\n\n"
            elif role == "user":
                prompt += f"用户: {content}\n\n"
            elif role == "assistant":
                prompt += f"助手: {content}\n\n"
        
        prompt += "助手: "
        return prompt
    
    def test_connection(self) -> bool:
        """测试本地模型连接"""
        test_messages = [{"role": "user", "content": "你好，请回复'连接成功'"}]
        
        print(f"🧪 测试 {self.model_type} 连接...")
        response = self.chat_completion(test_messages)
        
        if response:
            print(f"✅ {self.model_type} 连接成功")
            print(f"📝 测试响应: {response[:50]}...")
            return True
        else:
            print(f"❌ {self.model_type} 连接失败")
            return False

def create_local_model_interface(model_type: str = "ollama", **kwargs) -> LocalModelInterface:
    """
    创建本地模型接口实例
    
    Args:
        model_type: 模型类型
        **kwargs: 配置参数
        
    Returns:
        LocalModelInterface实例
    """
    return LocalModelInterface(model_type, **kwargs)

# 使用示例
if __name__ == "__main__":
    # 测试Ollama
    print("=== 测试Ollama ===")
    ollama_interface = create_local_model_interface("ollama", model_name="qwen2.5:7b")
    ollama_interface.test_connection()
    
    # 测试LM Studio
    print("\n=== 测试LM Studio ===")
    lmstudio_interface = create_local_model_interface("lmstudio")
    lmstudio_interface.test_connection()
    
    # 测试vLLM
    print("\n=== 测试vLLM ===")
    vllm_interface = create_local_model_interface("vllm")
    vllm_interface.test_connection()
