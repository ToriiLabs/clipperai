# app/ai_model.py
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch
import logging
import os
from .config import Config
from .models import Conversation, db
from .vector_memory import VectorMemory

logger = logging.getLogger(__name__)

model_info = {'pipeline': None}
vector_memory = VectorMemory()

# Create offload folder
os.makedirs(Config.OFFLOAD_FOLDER, exist_ok=True)

def load_model():
    if model_info['pipeline']:
        return model_info['pipeline']
    
    try:
        logger.info(f"🚀 Loading {Config.MODEL_PATH} (1.5B) — first load can take 5-15 minutes...")
        logger.info("💡 Using low CPU memory usage + offloading to reduce RAM pressure")
        
        model = AutoModelForCausalLM.from_pretrained(
            Config.MODEL_PATH,
            torch_dtype=Config.TORCH_DTYPE,
            device_map="auto",
            trust_remote_code=True,
            low_cpu_mem_usage=Config.LOW_CPU_MEM_USAGE,
            offload_folder=Config.OFFLOAD_FOLDER,
        )

        tokenizer = AutoTokenizer.from_pretrained(Config.MODEL_PATH, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            device_map="auto",
        )

        model_info['pipeline'] = pipe
        logger.info("✅ Model loaded successfully!")
        return pipe
    except Exception as e:
        logger.error(f"❌ Model loading failed: {e}")
        if "CUDA" in str(e) or "memory" in str(e).lower():
            logger.error("💡 Out of Memory detected. Close other apps or consider 4-bit quantization next.")
        raise

def generate_response(user_message: str, session_id: str = "default") -> str:
    try:
        pipe = load_model()

        # Retrieve memory clips (increased for better coverage)
        memory_clips = vector_memory.search_memory(user_message, n_results=8)
        memory_context = "\n\n".join(memory_clips) if memory_clips else "No relevant memory clips found for this query."

        prompt = f"""<|im_start|>system
You are ClipperAI — a sharp, creative, honest brainstorming partner.

CRITICAL RULES:
- ALWAYS base your answer primarily on the Memory clips below.
- If the clips contain relevant information, use them heavily and reference them.
- Do NOT fall back to general knowledge unless the clips are empty or irrelevant.
- Always begin your reply with: "⚠️ Safety Note: This is for brainstorming only."
- Keep answers clear and actionable.

<|im_end|>
<|im_start|>user
Memory clips from uploaded documents:
{memory_context}

Question: {user_message}
<|im_end|>
<|im_start|>assistant
"""

        outputs = pipe(
            prompt,
            max_new_tokens=512,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            repetition_penalty=1.1
        )

        full_text = outputs[0]['generated_text']
        response = full_text.split("<|im_start|>assistant")[-1].strip()

        # Save to database
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
        return "❌ The model hit an error. Check the terminal logs for details and try again."
