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
        # Fallback to local model if available
        if text_generator:
            try:
                return hf_generate(prompt, **kwargs)
            except:
                pass
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

def clean_and_validate(text, prev_texts, max_words=80):
    if not text:
        return None
    text = first_paragraph(text)
    text = text.strip().strip('\"\'` ')
    
    # Very lenient word count - allow up to max_words
    words = text.split()
    if len(words) > max_words:
        # Truncate if too long but keep it
        text = " ".join(words[:max_words]).rstrip(".,!?;:") + "."
    if len(words) < 2:
        return None
    
    # More lenient: add period if missing and has reasonable length
    if not SENT_END_RE.search(text):
        if len(words) >= 3:  # If it's a reasonable sentence, add period
            text = text + "."
        else:
            return None
    
    # Very lenient similarity check - only reject exact or near-exact duplicates
    text_lower = text.lower().strip()
    for p in prev_texts:
        p_lower = p.lower().strip()
        # First check exact match (after normalization)
        if text_lower == p_lower:
            return None
        # Then check very high similarity (>0.98) - near duplicates
        similarity = jaccard_similarity(text_lower, p_lower)
        if similarity > 0.98:
            return None
    
    return text

class ValidationError(Exception):
    pass


def validate_turn(text, seen_texts, max_words=80):
    """Validate a turn in the debate"""
    return clean_and_validate(text, seen_texts, max_words)


class Agent:
    """Debate agent that generates arguments"""
    
    def __init__(self, persona: str):
        self.persona = persona
    
    def speak(self, topic: str, context: str = "", seen_texts: list = [], round_num: int = 1) -> str:
        """Generate an argument for the given topic"""
        # Build persona-specific prompts
        persona_prompts = {
            "Scientist": "Focus on evidence-based reasoning, technical aspects, safety, data, and empirical research.",
            "Philosopher": "Focus on ethical implications, moral reasoning, human values, autonomy, and societal impact.",
            "Engineer": "Focus on practical implementation, feasibility, efficiency, and technical solutions.",
            "Economist": "Focus on market dynamics, costs, benefits, incentives, and economic impact.",
            "Lawyer": "Focus on legal frameworks, rights, regulations, precedents, and justice.",
            "Doctor": "Focus on medical analogies, patient safety, clinical trials, and health outcomes."
        }
        
        prompt_guidance = persona_prompts.get(self.persona, "Focus on providing a clear, reasoned argument.")
        
        # Build a more detailed prompt for better arguments
        round_context = ""
        if round_num == 1:
            round_context = "This is your opening argument. Make it strong and establish your core position."
        elif round_num <= 4:
            round_context = "This is a middle round. Build on your previous arguments and respond to counterarguments."
        else:
            round_context = "This is a later round. Strengthen your position with compelling evidence and reasoning."
        
        # Build prompt
        recent_exchange = ""
        if context:
            recent_exchange = "RECENT EXCHANGE:\n" + context + "\n"
        
        prompt = f"""
You are {self.persona} engaged in a structured debate. {prompt_guidance}

TOPIC: {topic}
CURRENT ROUND: {round_num} of 8
{round_context}

TASK: Write a compelling argument (3-6 sentences, 40-80 words) that:
- Presents a clear, reasoned position from a {self.persona} perspective
- Uses specific examples, evidence, or philosophical reasoning
- Addresses the topic directly and thoughtfully
- Builds on previous rounds or responds to counterarguments
- Avoids repeating previous arguments

{("PREVIOUS ARGUMENTS (avoid repeating): " + "; ".join(seen_texts[-3:]) if seen_texts else "This is the first argument.")}

{recent_exchange}

Write your argument now. Be substantive, thoughtful, and specific. Output ONLY the argument text, no labels or metadata:

"""
        
        # Use Gemini by default
        generator = gemini_generate
        gen_params = {}
        
        raw = ""
        cleaned = None
        for attempt in range(3):  # Try 3 times
            try:
                raw = generator(prompt, **gen_params)
                log_event("agent_speak_raw", {"persona": self.persona, "round": round_num, "raw_text": raw, "attempt": attempt + 1})
                
                if not raw or len(raw.strip()) < 10:
                    time.sleep(0.3)
                    continue
                
                # Clean the raw text
                cleaned = raw.strip().strip('\"\'` ')
                
                # Remove common prefixes
                prefixes = ["Argument:", "Response:", "As " + self.persona + ":", "Round " + str(round_num) + ":", 
                           "Round:", f"[{self.persona}]:", f"{self.persona}:"]
                for prefix in prefixes:
                    if cleaned.startswith(prefix):
                        cleaned = cleaned[len(prefix):].strip()
                
                # Take first paragraph (everything before double newline)
                if '\n\n' in cleaned:
                    cleaned = cleaned.split('\n\n')[0].strip()
                elif '\n' in cleaned:
                    # Take first substantial line (at least 20 chars)
                    lines = [l.strip() for l in cleaned.split('\n') if len(l.strip()) > 20]
                    if lines:
                        cleaned = lines[0]
                
                # Ensure minimum length (at least 20 words for a good argument)
                words = cleaned.split()
                if len(words) < 20:
                    # Try to get more sentences if too short
                    if '.' in raw:
                        sentences = [s.strip() for s in raw.split('.') if len(s.strip().split()) >= 5]
                        if sentences:
                            cleaned = '. '.join(sentences[:3]).strip()
                            if not cleaned.endswith('.'):
                                cleaned += '.'
                
                # Final length check
                words = cleaned.split()
                if len(words) < 10:
                    time.sleep(0.3)
                    continue
                
                # Validate with lenient settings
                validated = clean_and_validate(cleaned, seen_texts, max_words=100)
                if validated:
                    cleaned = validated
                    log_event("agent_speak_success", {"persona": self.persona, "round": round_num, "text": cleaned})
                    break
                else:
                    # Even if validation fails, use it if it's reasonable and unique enough
                    if len(words) >= 15 and len(words) <= 100:
                        # Check if it's not too similar to previous
                        text_lower = cleaned.lower().strip()
                        is_duplicate = False
                        for prev in seen_texts:
                            if jaccard_similarity(text_lower, prev.lower().strip()) > 0.90:
                                is_duplicate = True
                                break
                        if not is_duplicate:
                            # Add punctuation if missing
                            if not cleaned[-1] in '.!?':
                                cleaned += '.'
                            log_event("agent_speak_lenient_accepted", {"persona": self.persona, "round": round_num, "text": cleaned})
                            break
                
                time.sleep(0.3)
            except Exception as e:
                log_event("agent_speak_generation_error", {"persona": self.persona, "round": round_num, "error": str(e)})
                time.sleep(0.5)
        
        if cleaned and len(cleaned.split()) >= 10:
            return cleaned
        else:
            log_event("agent_speak_failed", {"persona": self.persona, "round": round_num, "final_text": cleaned})
            # Return a better fallback with more substance
            round_themes = {
                1: f"As {self.persona}, I argue that {topic} requires careful analysis of {('empirical evidence and safety protocols' if self.persona == 'Scientist' else 'ethical implications and human values')}.",
                2: f"As {self.persona}, I counter that {topic} involves complex considerations about {('systematic validation and risk assessment' if self.persona == 'Scientist' else 'autonomy and moral frameworks')}.",
                3: f"As {self.persona}, I emphasize that {topic} demands {('rigorous scientific methodology and data-driven decision making' if self.persona == 'Scientist' else 'philosophical reflection on fundamental rights')}.",
                4: f"As {self.persona}, I contend that {topic} raises {('critical questions about algorithmic bias and equitable outcomes' if self.persona == 'Scientist' else 'profound issues regarding human dignity and societal impact')}.",
                5: f"As {self.persona}, I demonstrate that {topic} necessitates {('comprehensive testing protocols and evidence-based regulation' if self.persona == 'Scientist' else 'deep ethical reasoning and consideration of moral principles')}.",
                6: f"As {self.persona}, I highlight that {topic} touches upon {('fundamental safety concerns and technical verification' if self.persona == 'Scientist' else 'core questions about freedom and human agency')}.",
                7: f"As {self.persona}, I stress that {topic} requires {('systematic evaluation of empirical data and long-term consequences' if self.persona == 'Scientist' else 'careful examination of values and ethical frameworks')}.",
                8: f"As {self.persona}, I conclude that {topic} ultimately depends on {('scientific rigor and evidence-based policy decisions' if self.persona == 'Scientist' else 'philosophical wisdom and respect for human autonomy')}."
            }
            fallback = round_themes.get(round_num, f"As {self.persona}, I believe {topic} demands thoughtful consideration of complex factors.")
            return fallback


class MemoryNode:
    """Memory management for debate context"""
    
    def __init__(self):
        self.memory = []
        self.summaries = []
    
    def update(self, transcript: list):
        """Update memory with new transcript entries"""
        self.memory.extend(transcript)
        
        # Generate periodic summaries
        if len(transcript) >= 2:
            summary = self._generate_summary(transcript[-2:])
            if summary:
                self.summaries.append(summary)
    
    def get_summary(self) -> str:
        """Get current memory summary"""
        if not self.summaries:
            return ""
        return self.summaries[-1]
    
    def _generate_summary(self, entries: list) -> str:
        """Generate summary for recent entries"""
        texts = [f"[{e['persona']}]: {e['text']}" for e in entries]
        context = "\n".join(texts)
        
        prompt = f"""
Summarize these debate arguments in one sentence (max 20 words):
{context}
"""
        
        try:
            summary = gemini_generate(prompt)
            if summary and len(summary.strip()) > 5:
                return summary.strip()
        except Exception as e:
            log_event("memory_summary_error", {"error": str(e)})
        
        return ""


class JudgeNode:
    """Judge that evaluates debate and determines winner"""
    
    def __init__(self):
        self.weighted_keywords = {
            "AgentA": {"risk": 1.5, "safety": 1.5, "protocol": 1.5, "technical": 1, "verification": 1, "data": 1, "evidence": 1, "scientific": 1, "bias": 1, "testing": 1, "impact": 1, "policy": 1, "regulation": 1.5, "medicine": 1.5},
            "AgentB": {"autonomy": 1.5, "freedom": 1.5, "ethics": 1.5, "moral": 1.5, "dignity": 1, "philosophy": 1, "consciousness": 1, "agency": 1, "human": 1, "societal": 1, "rights": 1, "knowledge": 1, "wisdom": 1, "innovation": 1.5, "progress": 1.5}
        }
    
    def review(self, transcript: list, persona_a: str, persona_b: str, topic: str = "") -> dict:
        """Review the debate and determine winner"""
        if not transcript:
            return None
        
        # Calculate scores
        scores = self._calculate_scores(transcript)
        
        # Determine winner
        winner = "AgentA" if scores["AgentA"] > scores["AgentB"] else "AgentB"
        winner_persona = persona_a if winner == "AgentA" else persona_b
        
        # Generate rationale
        rationale = self._generate_rationale(transcript, scores, winner, winner_persona, topic)
        
        return {
            "winner": f"{winner_persona} ({winner})",
            "rationale": rationale,
            "scores": scores
        }
    
    def _calculate_scores(self, transcript: list) -> dict:
        """Calculate keyword-based scores for each agent"""
        scores = {"AgentA": 0, "AgentB": 0}
        
        for entry in transcript:
            agent = entry["agent"]
            text = entry["text"].lower()
            
            if agent in self.weighted_keywords:
                keywords = self.weighted_keywords[agent]
                for keyword, weight in keywords.items():
                    count = text.count(keyword)
                    scores[agent] += count * weight
        
        return scores
    
    def _generate_rationale(self, transcript: list, scores: dict, winner: str, winner_persona: str, topic: str = "") -> str:
        """Generate rationale for the decision"""
        # Build summary of key arguments
        agent_a_args = [t['text'] for t in transcript if t['agent'] == 'AgentA']
        agent_b_args = [t['text'] for t in transcript if t['agent'] == 'AgentB']
        
        transcript_text = "\n".join([f"[{t['persona']} Round {t['round']}]: {t['text']}" for t in transcript])
        
        # Use provided topic or extract from transcript
        debate_topic = topic if topic else ("the debate topic")
        if not debate_topic and transcript and len(transcript) > 0:
            # Try to infer from first argument
            debate_topic = "the debate topic"
        
        prompt = f"""
You are an impartial judge evaluating a debate on: "{debate_topic}"

DEBATE TRANSCRIPT:
{transcript_text}

SCORES: AgentA scored {scores['AgentA']:.2f} points, AgentB scored {scores['AgentB']:.2f} points.
WINNER: {winner_persona} ({winner})

TASK: Write a clear, concise rationale (2-3 sentences) explaining the winner. 
- Briefly summarize the key arguments from each side
- Explain why {winner_persona} won based on argument quality, relevance, and persuasiveness
- DO NOT repeat the scores or mention them directly
- Focus on the quality of arguments, not numerical scores

Output ONLY the rationale text, no labels or prefixes:
"""
        
        try:
            raw_rationale = gemini_generate(prompt)
            
            # Clean and validate rationale
            if raw_rationale and len(raw_rationale.strip()) > 20:
                rationale = raw_rationale.strip().strip('\"\'` ')
                
                # Remove score mentions if present
                rationale = rationale.replace(f"The final score is 0 for AgentA and 0 for AgentB", "")
                rationale = rationale.replace(f"Scores: AgentA={scores['AgentA']:.2f}, AgentB={scores['AgentB']:.2f}", "")
                
                # Take first 3 sentences maximum
                sentences = [s.strip() for s in rationale.split('. ') if s.strip()]
                unique_sentences = []
                for sentence in sentences:
                    # Skip sentences that just repeat scores
                    if 'score' in sentence.lower() and ('0' in sentence or 'AgentA' in sentence and 'AgentB' in sentence):
                        continue
                    if sentence and not any(sentence.lower() in s.lower() for s in unique_sentences):
                        unique_sentences.append(sentence)
                    if len(unique_sentences) >= 3:
                        break
                
                rationale = '. '.join(unique_sentences)
                if rationale and not rationale.endswith('.'):
                    rationale += '.'
                
                # Ensure minimum quality
                if len(rationale.split()) < 8:
                    # Generate better fallback
                    key_points_a = " ".join([t['text'][:50] for t in agent_a_args[:2]])
                    key_points_b = " ".join([t['text'][:50] for t in agent_b_args[:2]])
                    rationale = f"{winner_persona} presented stronger arguments: {key_points_a[:100]}... demonstrating more compelling reasoning than {agent_b_args[0]['persona'] if agent_b_args else 'the opponent'}."
                
                return rationale
            else:
                # Better fallback
                if agent_a_args and agent_b_args:
                    return f"{winner_persona} presented more convincing arguments with stronger evidence and clearer reasoning throughout the debate, outweighing the valid points raised by the opponent."
                else:
                    return f"{winner_persona} wins based on stronger argumentation and more relevant points during the debate."
        except Exception as e:
            log_event("judge_rationale_error", {"error": str(e)})
            if agent_a_args and agent_b_args:
                return f"{winner_persona} presented more convincing arguments with stronger evidence and clearer reasoning throughout the debate."
            else:
                return f"{winner_persona} wins based on stronger argumentation and more relevant points during the debate."
