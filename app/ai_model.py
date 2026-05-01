from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
import torch
import logging
from .config import Config
from .models import VectorMemory, Conversation, db
from flask import current_app

logger = logging.getLogger(__name__)

model_info = {'model': None, 'tokenizer': None, 'pipeline': None}
vector_memory = VectorMemory()

def load_model():
    if model_info['pipeline']:
        return
    try:
        logger.info("Loading FLAN-T5 model...")
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
        logger.info("✅ Model loaded successfully.")
    except Exception as e:
        logger.error(f"Model loading failed: {e}")
        raise

def generate_response(user_message: str, session_id: str = "default") -> str:
    try:
        if not model_info['pipeline']:
            load_model()

        # Semantic memory search
        past_memories = vector_memory.search_memory(user_message, n_results=4)
        memory_context = "\n".join(past_memories) if past_memories else ""

        prompt = f"""Previous relevant context:
{memory_context}

User: {user_message}
ClipperAI: """

        inputs = model_info['tokenizer'](prompt, return_tensors='pt', truncation=True, max_length=768)
        input_ids = inputs['input_ids'].cuda() if torch.cuda.is_available() else inputs['input_ids']
        attention_mask = inputs['attention_mask'].cuda() if torch.cuda.is_available() else inputs['attention_mask']

        result = model_info['model'].generate(
            input_ids,
            attention_mask=attention_mask,
            max_length=200,
            num_return_sequences=1,
            do_sample=False,
            no_repeat_ngram_size=3,
            early_stopping=True
        )

        response = model_info['tokenizer'].decode(result[0], skip_special_tokens=True).strip()

        # Save to database
        try:
            conv = Conversation(session_id=session_id, user_message=user_message, ai_response=response)
            db.session.add(conv)
            db.session.commit()
        except:
            db.session.rollback()

        # Save to vector memory
        vector_memory.add_memory(f"User: {user_message}\nClipperAI: {response}")

        return response

    except Exception as e:
        logger.error(f"Generation error: {e}")
        return "Sorry, I'm having trouble right now. Please try again."
