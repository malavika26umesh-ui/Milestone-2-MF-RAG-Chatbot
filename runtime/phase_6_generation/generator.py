import os
import re
from typing import List, Dict, Optional
from groq import Groq
from dotenv import load_dotenv

from runtime.phase_6_generation.prompts import SYSTEM_PROMPT

class GroqGenerator:
    def __init__(self, model_id: str = "llama-3.1-8b-instant"):
        load_dotenv()
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment.")
        
        self.client = Groq(api_key=self.api_key)
        self.model_id = model_id

    def generate_answer(self, query: str, retrieved_chunks: List[Dict]) -> str:
        """
        Generates an answer using Groq based on retrieved context.
        Includes a single retry attempt and a final fallback.
        """
        # 1. Pack context and find latest date
        context_text = self._pack_context(retrieved_chunks)
        latest_date = self._get_latest_date(retrieved_chunks)
        
        # 2. Initial generation attempt
        response = self._call_groq(query, context_text)
        
        # 3. Post-validation (§7.2)
        if self._validate_response(response, retrieved_chunks):
            return response
        
        # 4. Retry if validation failed
        print("Initial response failed validation. Retrying with stricter constraints...")
        retry_query = f"{query}\n\nSTRICT REQUIREMENT: Use NO MORE than 3 sentences and include exactly one URL from the context."
        response = self._call_groq(retry_query, context_text)
        
        if self._validate_response(response, retrieved_chunks):
            return response
            
        # 5. Final Fallback (§191)
        print("Validation failed after retry. Using templated fallback.")
        return (
            "I could not generate a validated answer for your request. "
            "Please refer to the official fund documents for more information.\n\n"
            f"Last updated from sources: {latest_date}"
        )

    def _pack_context(self, chunks: List[Dict]) -> str:
        packed = []
        for i, chunk in enumerate(chunks):
            meta = chunk["metadata"]
            # Use 'content' from our merged Phase 5 output
            packed.append(f"Source [{i+1}]: {meta['source_url']}\nDate: {meta['fetched_at']}\nContent: {chunk['content']}")
        return "\n\n".join(packed)

    def _get_latest_date(self, chunks: List[Dict]) -> str:
        dates = []
        for c in chunks:
            dt = c["metadata"].get("fetched_at")
            if dt:
                # Basic string comparison works for ISO dates
                dates.append(dt)
        return max(dates) if dates else "Unknown"

    def _call_groq(self, query: str, context_block: str) -> str:
        system_msg = SYSTEM_PROMPT.format(context_block=context_block)
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": query},
                ],
                model=self.model_id,
                temperature=0.1,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"Groq API error: {e}")
            return "Error calling generation service."

    def _validate_response(self, text: str, chunks: List[Dict]) -> bool:
        """
        Programmatic guards for §7.2
        Returns True if response passes all checks.
        """
        if not text or "Error calling" in text:
            return False

        # A. Sentence count (Heuristic: split on . ! ?)
        sentences = re.split(r'[.!?]+\s+', text.strip())
        sentences = [s for s in sentences if len(s.strip()) > 5]
        # Allowing a buffer for URL and Footer which might be seen as sentences
        if len(sentences) > 4: 
            return False
        
        # B. URL Presence and Allowlist
        found_urls = re.findall(r'https?://[^\s)\]]+', text)
        if not found_urls or len(found_urls) > 1:
            return False
            
        allowed_urls = {chunk["metadata"]["source_url"] for chunk in chunks}
        if not any(url in allowed_urls for url in found_urls):
            return False
            
        # C. Forbidden Advisory Phrases
        forbidden = ["invest in", "you should", "better than", "outperform", "guarantee", "recommend"]
        lowered = text.lower()
        if any(word in lowered for word in forbidden):
            return False
            
        # D. Footer presence
        if "Last updated from sources:" not in text:
            return False
            
        return True
