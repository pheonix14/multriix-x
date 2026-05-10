import threading

class StandaloneHandler:
    def __init__(self, model_name="Qwen/Qwen2.5-0.5B-Instruct"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.loading = False
        self.lock = threading.Lock()

    def load(self):
        with self.lock:
            if self.model is not None:
                return
            
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            self.loading = True
            print(f"[INFO] Loading standalone model {self.model_name}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype="auto",
                device_map="auto"
            )
            self.loading = False
            print(f"[PASS] Standalone model {self.model_name} loaded.")

    async def generate(self, prompt, system="", temperature=0.7, max_tokens=512):
        if self.model is None:
            self.load()
            
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=True
        )
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        # Simulate streaming for UI consistency
        for char in response:
            yield {"response": char, "done": False}
        yield {"done": True}
