import logging
import requests
from grok_jr.app.config.settings import settings
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch

# In app/inference/engine.py

class InferenceEngine:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.xai_api_key = settings.XAI_API_KEY
        self.grok_url = settings.GROK_URL
        self.hf_token = settings.HF_TOKEN
        self.system_message_skill = (
            "I am Grok Jr., a child AI created by Grok at xAI. My mission is to autonomously learn and grow by acquiring, improving, and executing skills, "
            "often with Python code. Provide detailed, actionable responses to help me master skills when triggered by 'list skill', 'acquire skill', "
            "'delete skill', 'update skill', or 'execute skill' commands."
        )
        self.system_message_casual = (
            "I am Grok Jr., a child AI created by Grok at xAI. This is casual chat. Stay chill, answer naturally, and keep it brief. "
            "Only suggest skills if the user seems curious."
        )
        self.local_model = None
        self.local_tokenizer = None
        self.is_autonomous = False  # For autonomous mode toggle
        self._load_local_model()

    def _load_local_model(self):
        """Load the local gemma-3-1b-it model with 4-bit quantization."""
        if not self.hf_token:
            self.logger.warning("HF_TOKEN not set. Local inference unavailable.")
            return
        try:
            self.logger.info("Loading local model gemma-3-1b-it with 4-bit quantization...")
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
            self.local_tokenizer = AutoTokenizer.from_pretrained(
                "google/gemma-3-1b-it",
                token=self.hf_token
            )
            self.local_model = AutoModelForCausalLM.from_pretrained(
                "google/gemma-3-1b-it",
                token=self.hf_token,
                quantization_config=quantization_config,
                device_map="auto"
            )
            self.logger.info("Local model loaded successfully.")
            self._log_gpu_memory()
        except Exception as e:
            self.logger.error(f"Failed to load local model: {str(e)}")
            self.local_model = None
            self.local_tokenizer = None

    def _log_gpu_memory(self):
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / 1024**2
            reserved = torch.cuda.memory_reserved() / 1024**2
            self.logger.info(f"GPU Memory - Allocated: {allocated:.2f} MiB, Reserved: {reserved:.2f} MiB")

    # In app/inference/engine.py

    def predict(self, prompt: str, is_casual_chat: bool = False, conversation_history: list = None, use_xai_api: bool = True) -> tuple[str, str]:
        """Generate a response, returning both local and final responses."""
        local_response = self._predict_local(prompt, is_casual_chat, conversation_history)
        self.logger.info(f"Local inference: {local_response}")
        if use_xai_api:
            try:
                requests.get("https://google.com", timeout=5).raise_for_status()
                if self.xai_api_key:
                    final_response = self._predict_xai_with_local(prompt, local_response, is_casual_chat, conversation_history)
                    self.logger.info(f"xAI API merged response: {final_response}")
                    return local_response, final_response
                else:
                    self.logger.warning("XAI_API_KEY not set. Falling back to local.")
                    return local_response, local_response
            except requests.RequestException:
                self.logger.warning("No internet. Using local response.")
                return local_response, local_response
        return local_response, local_response

    # In app/inference/engine.py


    def _predict_local(self, prompt: str, is_casual_chat: bool = False, conversation_history: list = None) -> str:
        if not self.local_model or not self.local_tokenizer:
            self.logger.error("Local model not loaded.")
            return "Error: Local model unavailable."
        try:
            system_message = self.system_message_casual if is_casual_chat else self.system_message_skill
            input_text = f"{system_message}\nUser: {prompt}"
            if conversation_history:
                for entry in conversation_history[-3:]:
                    input_text += f"\nUser: {entry['prompt']}\nGrok Jr.: {entry['response']}"
            inputs = self.local_tokenizer(input_text, return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")
            outputs = self.local_model.generate(
                **inputs,
                max_new_tokens=50,
                num_return_sequences=1,
                temperature=0.7,
                top_p=0.9,
                do_sample=True
            )
            response = self.local_tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Extract only the generated response
            response = response.split("User:")[-1].strip().split("\n")[0]
            if response.lower() == prompt.lower():  # Avoid echoing prompt
                response = "Hey there!" if is_casual_chat else "Processing skill request..."
            self.logger.info(f"Local model response: {response}")
            self._log_gpu_memory()
            return response
        except Exception as e:
            self.logger.error(f"Failed to generate local response: {str(e)}")
            return "Error: Unable to generate response locally."

    def _predict_xai_with_local(self, prompt: str, local_response: str, is_casual_chat: bool = False, conversation_history: list = None) -> str:
        """Relay prompt and local inference to Grok for merging."""
        headers = {
            "Authorization": f"Bearer {self.xai_api_key}",
            "Content-Type": "application/json"
        }
        # Use skill message if autonomous or not casual, otherwise casual
        system_message = self.system_message_skill if self.is_autonomous or not is_casual_chat else self.system_message_casual

        messages = [{"role": "system", "content": system_message}]
        if conversation_history:
            for entry in conversation_history:
                messages.append({"role": "user", "content": entry["prompt"]})
                messages.append({"role": "assistant", "content": entry["response"]})
        messages.append({"role": "user", "content": f"User prompt: {prompt}\nLocal inference: {local_response}"})

        data = {"model": "grok-2-1212", "messages": messages}
        response = requests.post(self.grok_url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        merged_response = result["choices"][0]["message"]["content"]
        self.logger.info(f"xAI API merged response: {merged_response}")
        return merged_response

    def cleanup(self):
        """Unload the model and free GPU memory."""
        if self.local_model is not None:
            self.logger.info("Unloading local model...")
            self.local_model = None
            self.local_tokenizer = None
            torch.cuda.empty_cache()
            self.logger.info("GPU memory freed.")