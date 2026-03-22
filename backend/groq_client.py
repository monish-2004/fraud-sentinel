import os
import json
from groq import Groq
from typing import Dict, List

class GroqFraudAnalyzer:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY", "")
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"

    def _build_rag_context_str(self, rag_context: List[Dict]) -> str:
        if not rag_context:
            return "No specific pattern context available."
        lines = []
        for r in rag_context:
            lines.append(f"[{r['category']}] {r['content']}")
        return "\n\n".join(lines)

    def analyze(self, transaction: Dict, rag_context: List[Dict]) -> Dict:
        """Analyze structured transaction with RAG context"""
        rag_str = self._build_rag_context_str(rag_context)
        
        prompt = f"""You are an expert fraud analyst AI. Use the retrieved fraud knowledge below to analyze this transaction.

=== RETRIEVED FRAUD KNOWLEDGE (RAG Context) ===
{rag_str}

=== TRANSACTION TO ANALYZE ===
Transaction ID: {transaction.get('transaction_id', 'N/A')}
Amount: ${transaction.get('amount', 0):.2f}
Merchant: {transaction.get('merchant')} ({transaction.get('merchant_category')})
Location: {transaction.get('location')}
Time: {transaction.get('time')}
Device: {transaction.get('device')}
IP Address: {transaction.get('ip_address')}
Card Holder: {transaction.get('card_holder')}
Usual Location: {transaction.get('usual_location')}
Last Transaction: {transaction.get('last_transaction')}
Risk Flags: {', '.join(transaction.get('flags', []))}

Based on the retrieved knowledge and transaction details, provide a comprehensive fraud analysis.

Respond ONLY with a valid JSON object (no markdown, no backticks, no extra text):
{{
  "risk_score": <integer 1-100>,
  "confidence": "<Low|Medium|High|Critical>",
  "fraud_pattern": "<primary fraud pattern name>",
  "fraud_probability": "<percentage string like '87%'>",
  "explanation": "<2-3 sentence plain English explanation for customer>",
  "technical_details": "<detailed technical analysis for fraud analysts, 2-3 sentences>",
  "rag_reasoning": "<how the retrieved knowledge influenced this analysis, 1-2 sentences>",
  "immediate_actions": ["<action 1>", "<action 2>", "<action 3>", "<action 4>"],
  "customer_message": "<friendly, reassuring 1-sentence message to send to customer>",
  "sar_required": <true|false>,
  "sar_reason": "<reason if SAR required, else null>",
  "recovery_steps": ["<recovery step 1>", "<recovery step 2>", "<recovery step 3>"],
  "similar_patterns": ["<related fraud type 1>", "<related fraud type 2>"]
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1200,
        )
        
        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)

    def analyze_text(self, text: str, rag_context: List[Dict]) -> Dict:
        """Analyze free-text transaction description"""
        rag_str = self._build_rag_context_str(rag_context)
        
        prompt = f"""You are an expert fraud analyst AI. Use the retrieved fraud knowledge to analyze this transaction description.

=== RETRIEVED FRAUD KNOWLEDGE (RAG Context) ===
{rag_str}

=== TRANSACTION DESCRIPTION ===
{text}

Respond ONLY with a valid JSON object (no markdown, no backticks):
{{
  "risk_score": <integer 1-100>,
  "confidence": "<Low|Medium|High|Critical>",
  "fraud_pattern": "<primary fraud pattern>",
  "fraud_probability": "<percentage>",
  "explanation": "<2-3 sentence plain English explanation>",
  "technical_details": "<2-3 sentences technical analysis>",
  "rag_reasoning": "<how retrieved knowledge helped>",
  "immediate_actions": ["<action 1>", "<action 2>", "<action 3>"],
  "customer_message": "<1-sentence friendly alert>",
  "sar_required": <true|false>,
  "sar_reason": "<reason or null>",
  "recovery_steps": ["<step 1>", "<step 2>", "<step 3>"],
  "similar_patterns": ["<type 1>", "<type 2>"]
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1200,
        )
        
        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)

    def chat_about_transaction(self, transaction: Dict, analysis: Dict, conversation_history: List[Dict], user_question: str) -> str:
        """
        Chat with user about a specific transaction analysis.
        
        Args:
            transaction: Transaction details
            analysis: Fraud analysis results
            conversation_history: List of previous messages [{"role": "user/assistant", "content": "..."}]
            user_question: Current user question
        
        Returns:
            Assistant response as string
        """
        # Build context about the transaction
        context = f"""You are a fraud detection expert assistant helping analyze a transaction.

=== TRANSACTION DETAILS ===
Transaction ID: {transaction.get('transaction_id', 'N/A')}
Amount: ${transaction.get('amount', 0):.2f}
Merchant: {transaction.get('merchant')} ({transaction.get('merchant_category')})
Location: {transaction.get('location')}
Time: {transaction.get('time')}
Device: {transaction.get('device')}
IP Address: {transaction.get('ip_address')}
Card Holder: {transaction.get('card_holder')}
Usual Location: {transaction.get('usual_location')}
Last Transaction: {transaction.get('last_transaction')}

=== FRAUD ANALYSIS RESULTS ===
Risk Score: {analysis.get('risk_score', 0)}/100
Confidence: {analysis.get('confidence', 'Unknown')}
Fraud Pattern: {analysis.get('fraud_pattern', 'Unknown')}
Fraud Probability: {analysis.get('fraud_probability', 'Unknown')}
Explanation: {analysis.get('explanation', '')}
Technical Details: {analysis.get('technical_details', '')}
SAR Required: {analysis.get('sar_required', False)}
Immediate Actions: {', '.join(analysis.get('immediate_actions', []))}
Recovery Steps: {', '.join(analysis.get('recovery_steps', []))}

Answer the user's questions about this transaction analysis. Be helpful, clear, and concise.
Provide context from the analysis results when relevant."""

        # Build message history - combine system context with conversation
        messages = [
            {"role": "user", "content": context}
        ]
        
        # Add previous conversation turns
        if conversation_history:
            for msg in conversation_history:
                messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        
        # Add current question
        messages.append({"role": "user", "content": user_question})
        
        # Call Groq LLM
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=800,
        )
        
        return response.choices[0].message.content.strip()
