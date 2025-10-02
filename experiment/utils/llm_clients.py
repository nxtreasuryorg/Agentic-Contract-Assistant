from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import boto3
from botocore.config import Config as BotoConfig


@dataclass
class LLMResponse:
    text: str
    latency_s: float


class BedrockConverseClient:
    def __init__(self, region_name: Optional[str] = None, timeout_s: int = 180):
        cfg = BotoConfig(connect_timeout=timeout_s, read_timeout=timeout_s, retries={"max_attempts": 3})
        self._client = boto3.client("bedrock-runtime", region_name=region_name, config=cfg)

    def generate(self, model_id: str, prompt: str) -> LLMResponse:
        t0 = time.time()
        resp = self._client.converse(
            modelId=model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
        )
        dt = time.time() - t0
        msg = resp.get("output", {}).get("message", {})
        parts = msg.get("content", [])
        text = ""
        for p in parts:
            if "text" in p:
                text += p["text"]
        return LLMResponse(text=text, latency_s=dt)


class SageMakerEndpointClient:
    def __init__(self, region_name: Optional[str] = None, timeout_s: int = 180):
        cfg = BotoConfig(connect_timeout=timeout_s, read_timeout=timeout_s, retries={"max_attempts": 3})
        self._client = boto3.client("sagemaker-runtime", region_name=region_name, config=cfg)

    def generate(self, endpoint_name: str, prompt: str, content_type: str = "application/json") -> LLMResponse:
        payload = json.dumps({"inputs": prompt}).encode("utf-8")
        t0 = time.time()
        resp = self._client.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType=content_type,
            Body=payload,
        )
        dt = time.time() - t0
        body = resp["Body"].read()
        try:
            data = json.loads(body.decode("utf-8"))
            # Common HF text-generation response shapes
            if isinstance(data, list) and data and isinstance(data[0], dict) and "generated_text" in data[0]:
                text = data[0]["generated_text"]
            elif isinstance(data, dict) and "generated_text" in data:
                text = data["generated_text"]
            elif isinstance(data, dict) and "outputs" in data and isinstance(data["outputs"], list):
                text = "\n".join(str(x) for x in data["outputs"])  # best-effort
            else:
                text = body.decode("utf-8")
        except Exception:
            text = body.decode("utf-8")
        return LLMResponse(text=text, latency_s=dt)


def build_client(provider: str, *, region_name: Optional[str] = None, timeout_s: int = 180):
    provider = provider.strip().lower()
    if provider == "bedrock":
        return BedrockConverseClient(region_name=region_name, timeout_s=timeout_s)
    if provider == "sagemaker_endpoint":
        return SageMakerEndpointClient(region_name=region_name, timeout_s=timeout_s)
    raise ValueError(f"Unsupported provider: {provider}")
