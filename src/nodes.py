# nodes.py
import random
import json
import re
import time
import os
from logger_util import log_event
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# --- Gemini API Configuration ---
try:
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        log_event("gemini_api_key_not_found")
        gemini_model = None
    else:
        genai.configure(api_key=gemini_api_key)
        gemini_model = genai.GenerativeModel('gemini-2.0-flash')
except Exception as e:
    log_event("gemini_configuration_error", {"error": str(e)})
    gemini_model = None

def gemini_generate(prompt, **kwargs):
    if gemini_model is None:
        return "Error: Gemini API not configured."
    try:
        response = gemini_model.generate_content(prompt, **kwargs)
        return response.text.strip()
    except Exception as e:
        log_event("gemini_generate_error", {"error": str(e)})
        return f"Error generating text with Gemini: {e}"

# --- Local Transformers Pipeline ---
try:
    MODEL_NAME = "google/flan-t5-base"
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    text_generator = pipeline("text2text-generation", model=model, tokenizer=tokenizer, device=-1)
except Exception as e:
    log_event("pipeline_creation_error", {"error": str(e)})
    text_generator = None

def hf_generate(prompt, **kwargs):
    if text_generator is None:
        return "Error: text-generation pipeline not available."
    try:
        out = text_generator(prompt, **kwargs)
        return out[0].get("generated_text", "").strip()
    except Exception as e:
        log_event("hf_generate_error", {"error": str(e)})
        return f"Error generating text: {e}"

# --- Text cleaning and validation ---
SENT_END_RE = re.compile(r'[.?!]\s*$')

def first_paragraph(text):
    parts = re.split(r'\n{1,2}', text.strip())
    return parts[0].strip()

def jaccard_similarity(a, b):
    sa = set(a.lower().split())
    sb = set(b.lower().split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)

def clean_and_validate(text, prev_texts, max_words=60):
    if not text:
        return None
    text = first_paragraph(text)
    text = text.strip().strip('\"\'` ')
    if len(text.split()) > max_words:
        return None
    if not SENT_END_RE.search(text):
        return None
    if len(text.split()) < 4:
        return None
    for p in prev_texts:
        if text == p:
            return None
        if jaccard_similarity(text, p) > 0.75:
            return None
    return text

class ValidationError(Exception):
    pass
