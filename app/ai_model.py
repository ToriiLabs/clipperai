from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
import torch
import logging
from collections import deque
from .config import Config

logger = logging.getLogger(__name__)

# Global model and conversation store (simple in-memory for now)
model_info = {'model': None, 'tokenizer': None, 'pipeline': None}
conversation_history = deque(maxlen=Config.MAX_HISTORY)  # Persists across requests

def load_model():
    try:
        logger.info(f"Loading FLAN-T5 model from {Config.MODEL_PATH}...")
        model = AutoModelForSeq2SeqLM.from_pretrained(
            Config.MODEL_PATH, 
            use_auth_token=Config.HUGGINGFACE_API_KEY
        )
        tokenizer = AutoTokenizer.from_pretrained(
            Config.MODEL_PATH, 
            use_auth_token=Config.HUGGINGFACE_API_KEY
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model.eval()
        if torch.cuda.is_available():
            model = model.cuda()

        model_info['model'] = model
        model_info['tokenizer'] = tokenizer
        model_info['pipeline'] = pipeline(
            'text2text-generation', 
            model=model, 
            tokenizer=tokenizer, 
            device=0 if torch.cuda.is_available() else -1
        )
        logger.info("FLAN-T5 model loaded successfully.")
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise

def generate_response(user_message: str) -> str:
    try:
        if not model_info['pipeline']:
            load_model()

        # Build prompt with history
        history_str = ' '.join(list(conversation_history))
        prompt = f"Given the conversation so far: {history_str} Answer logically: {user_message}"

        inputs = model_info['tokenizer'](prompt, return_tensors='pt', truncation=True, padding=True, max_length=512)
        input_ids = inputs['input_ids'].cuda() if torch.cuda.is_available() else inputs['input_ids']
        attention_mask = inputs['attention_mask'].cuda() if torch.cuda.is_available() else inputs['attention_mask']

        # Greedy decoding (deterministic + anti-repetition)
        result = model_info['model'].generate(
            input_ids,
            attention_mask=attention_mask,
            max_length=150,
            num_return_sequences=1,
            do_sample=False,
            no_repeat_ngram_size=3,
            early_stopping=True
        )

        response = model_info['tokenizer'].decode(result[0], skip_special_tokens=True).strip()

        # Store AI response in history
        conversation_history.append(f"Clipper: {response}")
        return response

    except Exception as e:
        logger.error(f"Generation error: {e}")
        return "Sorry, I'm having trouble generating a response right now."
