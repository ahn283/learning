import json
import tiktoken     # token counting
import numpy as np 
from collections import defaultdict

class OpenAIFineTuneTools:
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.encoding = tiktoken.get_encoding('cl100k_base')
        
        # dataset
        with open(self.file_path, 'r', encoding='utf-8') as f:
            self.dataset = [json.loads(line) for line in f]
            

    def format_validate(self):
        # check dataset's format error
        format_errors = defaultdict(int)
        
        for ex in self.dataset:
            if not isinstance(ex, dict):
                format_errors["data_type"] += 1
                continue
            self.messages = ex.get("messages", None)
            if not self.messages:
                format_errors["messing_messages_list"] += 1
                continue
            
            for message in self.messages:
                if "role" not in message or "content" not in message:
                    format_errors["message_missing_key"] += 1
                    
                if any(k not in ("role", "content", "name", "fucntion_call", "weight") for k in message):
                    format_errors["message_unrecognized_key"] += 1
                
                if message.get("role", None) not in ("system", "user", "assistant", "function"):
                    format_errors["uncategorized_role"] += 1
                    
                content = message.get("content", None)
                function_call = message.get("function_call", None)
                
                if (not content and not function_call) or not isinstance(content, str):
                    format_errors['missing_content'] += 1
                    
            if not any(message.get("role", None) == "assistant" for message in self.messages):
                format_errors["example_missing_assistant_message"] += 1
        if format_errors:
            msg = "Found errors:\n"
            for k, v in format_errors.items():
                msg += f"{k}: {v}"
        else:
            msg = "No error found"
        
        return msg
    
    def token_count(self, tokens_per_message=3, tokens_per_name=1):   
        # not exact!
        # simplified from https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
        num_tokens = 0
        for message in self.messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(self.encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3
        return num_tokens
    
    def num_assistant_tokens_from_messages(self):
        num_tokens = 0
        for message in self.messages:
            if message['role'] == 'assistant':
                num_tokens += len(self.encoding.encode(message['content']))
        return num_tokens

    def print_distribution(values, name):
        print(f"\n### Distribution of {name}:")
        print(f"min / max : {min(values)}, {max(values)}")
        print(f"mean / median: {np.mean(values)}, {np.median(values)}")
        print(f"p5 / p95: {np.quantile(values, 0.1)}, {np.quantile(values, 0.9)}")
        
    def token_counts_warning(self):
        # warning and tokens counts
        self.n_missing_system = 0
        self.n_missing_user = 0
        self.n_messages = []
        self.convo_lens = []
        self.assistant_message_lens = []

        for ex in self.dataset:
            messages = ex["messages"]
            if not any(message["role"] == "system" for message in messages):
                n_missing_system += 1
            if not any(message["role"] == "user" for message in messages):
                n_missing_user += 1
            self.n_messages.append(len(messages))
            self.convo_lens.append(self.num_assistant_tokens_from_messages(messages))
            self.assistant_message_lens.append(self.num_assistant_tokens_from_messages(messages))
            
        print("Num example  missing system message:", n_missing_system)
        print("Num examples missing user message:", n_missing_user)
        self.print_distribution(self.n_messages, "num_message_per_example")
        self.print_distribution(self.convo_lens, "num_total_tokens_per_example")
        self.print_distribution(self.assistant_message_lens, "num_assistant_token_per_example")
        n_too_long = sum(1 > 16385 for l in self.convo_lens)
        print(f"\n{n_too_long} examples may be over the 16,385 token limit, they will be truncated during fine-tuning")    
        
    def cost_estimation(self):
        # Pricing and default n_epochs estimate
        MAX_TOKENS_PER_EXAMPLE = 16385

        TARGET_EPOCHS = 3
        MIN_TARGET_EXAMPLES = 100
        MAX_TARGET_EXAMPLES = 25000
        MIN_DEFAULT_EPOCHS = 1
        MAX_DEFAULT_EPOCHS = 25

        n_epochs = TARGET_EPOCHS
        n_train_examples = len(self.dataset)
        if n_train_examples * TARGET_EPOCHS < MIN_TARGET_EXAMPLES:
            n_epochs = min(MAX_DEFAULT_EPOCHS, MIN_TARGET_EXAMPLES // n_train_examples)
        elif n_train_examples * TARGET_EPOCHS > MAX_TARGET_EXAMPLES:
            n_epochs = max(MIN_DEFAULT_EPOCHS, MAX_TARGET_EXAMPLES // n_train_examples)

        n_billing_tokens_in_dataset = sum(min(MAX_TOKENS_PER_EXAMPLE, length) for length in self.convo_lens)
        print(f"Dataset has ~{n_billing_tokens_in_dataset} tokens that will be charged for during training")
        print(f"By default, you'll train for {n_epochs} epochs on this dataset")
        print(f"By default, you'll be charged for ~{n_epochs * n_billing_tokens_in_dataset} tokens")           
        