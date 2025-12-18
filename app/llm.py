from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from app.config import settings
from app.llm_cache import LRUCache, RedisCache, build_cache_key


class LLMClient:
    def __init__(self) -> None:
        self.backend = settings.llm_backend
        self.model_name = settings.llm_model
        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature
        self.device = settings.llm_device
        self.adapter_path = settings.llm_adapter_path
        self.adapter_type = settings.llm_adapter_type
        self.quantization = settings.llm_quantization
        self.batch_size = settings.llm_batch_size
        self._pipeline = None
        self._cache = (
            RedisCache(settings.llm_cache_redis_url)
            if settings.llm_cache_redis_url
            else LRUCache(settings.llm_cache_size)
        )
        self._loaded_adapter = None

    def _load_local(self):
        if self._pipeline is not None:
            return
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

        tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        model_kwargs = {}
        if self.quantization == "8bit":
            model_kwargs["load_in_8bit"] = True
        model = AutoModelForCausalLM.from_pretrained(self.model_name, **model_kwargs)
        if self.adapter_path:
            try:
                from peft import PeftModel

                model = PeftModel.from_pretrained(model, self.adapter_path)
                self._loaded_adapter = self.adapter_path
            except Exception:
                pass
        self._pipeline = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=self.max_tokens,
            temperature=self.temperature,
            device=0 if self.device == "cuda" else -1,
        )

    def generate(self, prompt: str) -> str:
        if self.backend == "disabled":
            return ""
        if self.backend != "local":
            return ""
        cache_key = build_cache_key(self.model_name, self.adapter_path, prompt)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        self._load_local()
        result = self._pipeline(prompt, num_return_sequences=1)
        if not result:
            return ""
        output = result[0].get("generated_text", "")
        self._cache.set(cache_key, output)
        return output

    def batch_generate(self, prompts: List[str]) -> List[str]:
        if self.backend == "disabled":
            return ["" for _ in prompts]
        if self.backend != "local":
            return ["" for _ in prompts]
        self._load_local()
        outputs: List[str] = []
        for prompt in prompts:
            cache_key = build_cache_key(self.model_name, self.adapter_path, prompt)
            cached = self._cache.get(cache_key)
            if cached is not None:
                outputs.append(cached)
                continue
            result = self._pipeline(prompt, num_return_sequences=1)
            text = result[0].get("generated_text", "") if result else ""
            self._cache.set(cache_key, text)
            outputs.append(text)
        return outputs


def parse_json_block(text: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def parse_findings(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings = payload.get("findings")
    if not isinstance(findings, list):
        return []
    return [item for item in findings if isinstance(item, dict)]
