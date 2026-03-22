import os
import json
import random
import logging
from groq import Groq

logger = logging.getLogger(__name__)

FRAUD_TYPES = [
    "Account Takeover", "Card-Not-Present", "Geo Anomaly",
    "Velocity Attack", "TOR Network", "Phishing",
    "Crypto Fraud", "Card Skimming", "Synthetic Identity",
]

class TransactionGenerator:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            logger.warning("GROQ_API_KEY not set, will use mock data generation")
            self.client = None
        else:
            self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        self._tx_counter = 1000

    def _generate_mock_transactions(self, count: int = 5, include_legitimate: bool = True) -> list:
        """Generate mock transactions when API is unavailable"""
        logger.info("Using mock transaction generation")
        fraud_count = count if not include_legitimate else max(1, int(count * 0.75))
        legit_count = count - fraud_count
        
        merchants = ["Amazon", "Netflix", "Starbucks", "Shell Gas", "Walmart", "Target", "Best Buy", "Crypto Exchange", "Wire Transfer", "ATM Withdrawal"]
        locations = ["New York, USA", "Los Angeles, USA", "London, UK", "Lagos, Nigeria", "Mumbai, India", "Singapore", "Hong Kong", "Moscow, Russia"]
        devices = ["iPhone 13", "Android Phone", "Desktop", "Laptop", "Tablet", "Unknown"]
        
        transactions = []
        
        # Generate fraudulent transactions
        for i in range(fraud_count):
            self._tx_counter += 1
            tx = {
                "transaction_id": f"TXN-{self._tx_counter}-{chr(65 + i % 26)}{chr(75 + i % 10)}",
                "amount": round(random.uniform(100, 5000), 2),
                "merchant": random.choice(merchants[:7]),
                "merchant_category": "Suspicious",
                "location": random.choice(locations[2:]),
                "time": f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}",
                "device": random.choice(devices),
                "ip_address": f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
                "card_holder": ["John Doe", "Jane Smith", "Ahmed Hassan", "Liu Chen"][i % 4],
                "usual_location": random.choice(locations[:2]),
                "last_transaction": "2 days ago",
                "flags": random.sample(["Geo Anomaly", "Velocity Attack", "TOR Network"], 2),
                "is_suspicious": True,
                "fraud_type": random.choice(FRAUD_TYPES)
            }
            transactions.append(tx)
        
        # Generate legitimate transactions
        for i in range(legit_count):
            self._tx_counter += 1
            tx = {
                "transaction_id": f"TXN-{self._tx_counter}-{chr(65 + (i + fraud_count) % 26)}{chr(75 + (i + fraud_count) % 10)}",
                "amount": round(random.uniform(10, 500), 2),
                "merchant": random.choice(merchants),
                "merchant_category": "Retail",
                "location": random.choice(locations[:2]),
                "time": f"{random.randint(8, 18):02d}:{random.randint(0, 59):02d}",
                "device": random.choice(devices[:3]),
                "ip_address": f"{random.randint(100, 200)}.{random.randint(100, 200)}.{random.randint(1, 100)}.{random.randint(1, 255)}",
                "card_holder": ["John Doe", "Jane Smith", "Ahmed Hassan", "Liu Chen"][i % 4],
                "usual_location": random.choice(locations[:2]),
                "last_transaction": "1 day ago",
                "flags": [],
                "is_suspicious": False,
                "fraud_type": None
            }
            transactions.append(tx)
        
        return transactions

    def generate(self, count: int = 5, include_legitimate: bool = True) -> list:
        """Generate synthetic transactions using LLM or fallback to mock"""
        try:
            # If no API key, use mock generation
            if self.client is None:
                return self._generate_mock_transactions(count, include_legitimate)
                
            fraud_count = count if not include_legitimate else max(1, int(count * 0.75))
            legit_count = count - fraud_count

            selected_patterns = random.sample(FRAUD_TYPES, min(fraud_count, len(FRAUD_TYPES)))

            prompt = f"""Generate {fraud_count} suspicious and {legit_count} legitimate bank transactions for fraud detection testing.

Patterns to include for suspicious: {', '.join(selected_patterns[:fraud_count])}

Respond ONLY with a valid JSON array (no markdown):
[
  {{
    "transaction_id": "TXN-XXXX-XX",
    "amount": <float>,
    "merchant": "<merchant name>",
    "merchant_category": "<category>",
    "location": "<City, Country>",
    "time": "<HH:MM AM/PM TZ>",
    "device": "<device description>",
    "ip_address": "<realistic IP>",
    "card_holder": "<full name>",
    "usual_location": "<city, state>",
    "last_transaction": "<timeframe ago + location>",
    "flags": ["<flag1>", "<flag2>"],
    "is_suspicious": <true|false>,
    "fraud_type": "<fraud type or null>"
  }}
]

Make transactions realistic and varied. Use diverse names, locations, amounts."""

            logger.info(f"Calling Groq API to generate {count} transactions")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=2000,
            )
            
            logger.info("Groq API response received")
            raw = response.choices[0].message.content.strip()
            logger.info(f"Raw response: {raw[:200]}...")
            
            # Clean up response
            raw = raw.replace("```json", "").replace("```", "").strip()
            
            # Parse JSON
            transactions = json.loads(raw)
            logger.info(f"Parsed {len(transactions)} transactions")
            
            # Ensure unique IDs
            for i, tx in enumerate(transactions):
                self._tx_counter += 1
                tx["transaction_id"] = f"TXN-{self._tx_counter}-{chr(65 + i % 26)}{chr(75 + i % 10)}"
            
            logger.info("Transaction generation completed successfully")
            return transactions
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            logger.error(f"Response was: {raw if 'raw' in locals() else 'N/A'}")
            logger.info("Falling back to mock transaction generation")
            return self._generate_mock_transactions(count, include_legitimate)
        except Exception as e:
            logger.error(f"Transaction generation error: {str(e)}", exc_info=True)
            logger.info("Falling back to mock transaction generation due to error")
            return self._generate_mock_transactions(count, include_legitimate)
