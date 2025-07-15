import yaml
import requests
from openai import OpenAI

class LLMBackend:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        self.current_model = self.config.get("default_model", "openai")
        openai_key = self.config.get("openai", {}).get("api_key")
        if openai_key:
            self.client = OpenAI(api_key=openai_key)
        else:
            self.client = None
            print("[LLMBackend] Warning: OpenAI API key not found in config.")
        self.available_backends = []
        self.detect_backends()

    def detect_backends(self):
        self.available_backends.clear()
        if self.check_openai():
            self.available_backends.append("openai")
        if self.check_ollama():
            self.available_backends.append("ollama")
        if self.current_model not in self.available_backends:
            self.current_model = self.available_backends[0] if self.available_backends else None
        print(f"[LLMBackend] Available backends: {self.available_backends}")
        print(f"[LLMBackend] Current backend: {self.current_model}")

    def check_openai(self):
        key = self.config.get("openai", {}).get("api_key")
        if not key:
            return False
        try:
            r = requests.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {key}"},
                timeout=4,
            )
            return r.status_code == 200
        except Exception:
            return False

    def check_ollama(self):
        url = self.config.get("ollama", {}).get("url")
        model = self.config.get("ollama", {}).get("model")
        if not url or not model:
            return False
        try:
            resp = requests.get(f"{url}/api/tags", timeout=2)
            if resp.status_code != 200:
                return False
            models = resp.json().get("models", [])
            return any(m["name"] == model for m in models)
        except Exception:
            return False

    def switch_model(self):
        if not self.available_backends:
            print("[LLMBackend] No backends available to switch.")
            return False
        idx = self.available_backends.index(self.current_model) if self.current_model in self.available_backends else -1
        next_idx = (idx + 1) % len(self.available_backends)
        self.current_model = self.available_backends[next_idx]
        print(f"[LLMBackend] Switched backend to: {self.current_model}")
        return True

    def generate(self, prompt):
        if not self.current_model:
            return "[LLMBackend] No backend available."
        try:
            if self.current_model == "openai":
                return self._generate_openai(prompt)
            elif self.current_model == "ollama":
                return self._generate_ollama(prompt)
            else:
                return f"[LLMBackend] Unknown backend: {self.current_model}"
        except Exception as e:
            print(f"[LLMBackend] Error in generate: {e}")
            fallback_idx = (self.available_backends.index(self.current_model) + 1) % len(self.available_backends)
            fallback_backend = self.available_backends[fallback_idx]
            print(f"[LLMBackend] Fallback to backend: {fallback_backend}")
            self.current_model = fallback_backend
            try:
                if fallback_backend == "openai":
                    return self._generate_openai(prompt)
                elif fallback_backend == "ollama":
                    return self._generate_ollama(prompt)
            except Exception as e2:
                print(f"[LLMBackend] Fallback failed: {e2}")
            return "[LLMBackend] All backends failed."

    def _generate_openai(self, prompt):
        if self.client is None:
            raise RuntimeError("OpenAI client not initialized")
        response = self.client.chat.completions.create(
            model=self.config["openai"].get("model", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256,
        )
        return response.choices[0].message.content.strip()

    def _generate_ollama(self, prompt):
        ollama_cfg = self.config.get("ollama", {})
        url = ollama_cfg.get("url")
        model = ollama_cfg.get("model")
        if not url or not model:
            raise RuntimeError("Ollama configuration missing")
        resp = requests.post(
            f"{url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
