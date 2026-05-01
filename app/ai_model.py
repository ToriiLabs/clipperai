from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch
import logging
from .config import Config
from .models import VectorMemory, Conversation, db

logger = logging.getLogger(__name__)

model_info = {'model': None, 'tokenizer': None, 'pipeline': None}
vector_memory = VectorMemory()


def load_model():
    if model_info['pipeline']:
        return
    try:
        logger.info(f"Loading {Config.MODEL_PATH} ... (This may take 5-15 minutes the first time)")

        model = AutoModelForCausalLM.from_pretrained(
            Config.MODEL_PATH,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )

        tokenizer = AutoTokenizer.from_pretrained(
            Config.MODEL_PATH,
            trust_remote_code=True
        )

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model_info['model'] = model
        model_info['tokenizer'] = tokenizer
        model_info['pipeline'] = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            device_map="auto"
        )

        logger.info("✅ Qwen2.5-7B-Instruct loaded successfully!")
    except Exception as e:
        logger.error(f"Model loading failed: {e}")
        raise


def generate_response(user_message: str, session_id: str = "default") -> str:
    try:
        if not model_info['pipeline']:
            load_model()

        past_memories = vector_memory.search_memory(user_message, n_results=4)
        memory_context = "\n".join(past_memories) if past_memories else ""

        prompt = f"""<|im_start|>system
You are ClipperAI, a helpful, creative, and honest brainstorming assistant.
Always start your response with the safety disclaimer.
<|im_end|>
<|im_start|>user
Previous relevant context:
{memory_context}

{user_message}
<|im_end|>
<|im_start|>assistant
"""

        outputs = model_info['pipeline'](
            prompt,
            max_new_tokens=512,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            repetition_penalty=1.1
        )

        response = outputs[0]['generated_text'].split("<|im_start|>assistant")[-1].strip()

        # Save conversation
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
