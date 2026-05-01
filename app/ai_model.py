# app/ai_model.py
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch
import logging
from .config import Config
from .models import Conversation, db
from .vector_memory import VectorMemory   # ← Now exists

logger = logging.getLogger(__name__)

model_info = {'pipeline': None}
vector_memory = VectorMemory()

def load_model():
    if model_info['pipeline']:
        return model_info['pipeline']
    
    try:
        logger.info(f"🚀 Loading {Config.MODEL_PATH} (1.5B) — first load can take 3-10 minutes...")
        
        model = AutoModelForCausalLM.from_pretrained(
            Config.MODEL_PATH,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
            trust_remote_code=True,
            low_cpu_mem_usage=True,
        )

        tokenizer = AutoTokenizer.from_pretrained(Config.MODEL_PATH, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            device_map="auto"
        )

        model_info['pipeline'] = pipe
        logger.info("✅ Model loaded successfully!")
        return pipe
    except Exception as e:
        logger.error(f"❌ Model loading failed: {e}")
        raise

def generate_response(user_message: str, session_id: str = "default") -> str:
    try:
        pipe = load_model()

        # Retrieve memory
        memory_clips = vector_memory.search_memory(user_message)
        memory_context = "\n\n".join(memory_clips) if memory_clips else "No memory clips yet."

        prompt = f"""<|im_start|>system
You are ClipperAI — a sharp, creative, honest brainstorming partner.
Always begin your reply with: "⚠️ Safety Note: This is for brainstorming only."
Use the memory clips below when relevant.
<|im_end|>
<|im_start|>user
Memory clips:
{memory_context}

Question: {user_message}
<|im_end|>
<|im_start|>assistant
"""

        outputs = pipe(
            prompt,
            max_new_tokens=512,
            temperature=0.75,
            top_p=0.9,
            do_sample=True,
            repetition_penalty=1.12
        )

        full_text = outputs[0]['generated_text']
        response = full_text.split("<|im_start|>assistant")[-1].strip()

        # Save conversation
        try:
            conv = Conversation(
                session_id=session_id,
                user_message=user_message,
                ai_response=response
            )
            db.session.add(conv)
            db.session.commit()
        except Exception as db_e:
            logger.warning(f"DB save skipped: {db_e}")
            db.session.rollback()

        return response

    except Exception as e:
        logger.error(f"Generation error: {e}")
        return "❌ The model hit an error. Check terminal for details and try again."
