import faiss
import numpy as np
import json
from typing import List, Dict
import hashlib

# Fraud knowledge base - expert rules and patterns
FRAUD_KNOWLEDGE = [
    {
        "source": "ATO_Pattern_001",
        "category": "Account Takeover",
        "content": "Account Takeover (ATO) indicators: new device login, password reset within 24h, rapid profile changes, high-value purchase immediately after account changes, geo-anomaly (different country/state from usual), unusual access time (2-5 AM local time). ATO often involves credential stuffing from data breaches. Risk mitigation: freeze account, require re-authentication, verify via secondary channel.",
    },
    {
        "source": "CNP_Pattern_002",
        "category": "Card-Not-Present Fraud",
        "content": "Card-Not-Present (CNP) fraud occurs in online/phone transactions without physical card. Indicators: billing/shipping address mismatch, multiple failed CVV attempts, high-value electronics/gift cards, international shipping to freight forwarder, rapid checkout without browsing history, proxy or VPN IP, device fingerprint mismatch. Next steps: manual review, request additional verification, flag for chargeback monitoring.",
    },
    {
        "source": "GEO_Pattern_003",
        "category": "Geo Anomaly",
        "content": "Geographic anomaly fraud: transaction location impossible given prior transaction timing (e.g., Chicago transaction followed 30 min later by Lagos transaction). Indicators: overseas IP during domestic card use, transaction in sanctioned country, IP geolocation mismatch with billing address, use of Tor/VPN to mask location. Action: block transaction, alert customer immediately, require OTP verification.",
    },
    {
        "source": "VEL_Pattern_004",
        "category": "Velocity Attack",
        "content": "Velocity attacks involve rapid succession of transactions to test card validity or drain accounts. Indicators: 3+ transactions within 10 minutes, multiple small amounts followed by large amount, many failed attempts before success, same merchant repeated, sequential account numbers being tested. Response: temporary transaction limit, challenge additional transactions, alert fraud team.",
    },
    {
        "source": "SYN_Pattern_005",
        "category": "Synthetic Identity Fraud",
        "content": "Synthetic identity fraud combines real and fake PII (e.g., real SSN with fake name). Indicators: credit history is thin but recently opened many accounts, no social media presence matching identity, address is a mail drop or freight forwarder, identity documents show inconsistencies, multiple identities at same address. Long-term buildup before bust-out event. Requires SAR filing.",
    },
    {
        "source": "TOR_Pattern_006",
        "category": "TOR/Proxy Network",
        "content": "Transactions originating from Tor exit nodes or anonymous proxies indicate deliberate identity concealment. Tor exit node IPs are publicly listed (e.g., 185.220.x.x range). High correlation with fraud when combined with crypto purchases, wire transfers, or gift cards. Automatic high-risk flag. Suggest blocking transaction and filing SAR if amount exceeds $5,000.",
    },
    {
        "source": "PHISH_Pattern_007",
        "category": "Phishing / Social Engineering",
        "content": "Post-phishing fraud indicators: customer reports suspicious email/call, then large wire transfer or account change. Pattern: customer receives fake bank call, shares OTP, fraudster initiates transfer. Indicators: unusual recipient account, customer initiates contact about 'reversing' transaction, transaction to peer-to-peer payment platform. Immediately freeze outgoing transfers, file police report guidance.",
    },
    {
        "source": "CRYPTO_Pattern_008",
        "category": "Cryptocurrency Fraud",
        "content": "Cryptocurrency exchange transactions carry high fraud risk due to irreversibility. Indicators: first-time crypto purchase, unusual amount, foreign exchange, customer age <25 or >70, transaction immediately after account access from new device. Crypto-related fraud is difficult to recover. Block and verify before processing. May require SAR under BSA if >$10,000 or structured.",
    },
    {
        "source": "SAR_Rules_009",
        "category": "SAR Filing Requirements",
        "content": "Suspicious Activity Report (SAR) required under Bank Secrecy Act for: transactions >$5,000 with known/suspected illegal activity, >$25,000 regardless of actor identity, structuring to avoid $10,000 CTR threshold, transactions involving sanctioned countries, known terrorist financing indicators. SAR must be filed within 30 days of detection. Do not alert customer (tipping off prohibited).",
    },
    {
        "source": "SKIM_Pattern_010",
        "category": "Card Skimming",
        "content": "Card skimming involves capturing card data from physical terminals (ATMs, gas pumps). Indicators: card used at known skimmer-prone location (rural ATM, unbranded gas station), then card-present transaction in different city, multiple victims from same merchant terminal. Clone cards used in-person with chip bypass (magnetic stripe only). Reissue card, check other customers at same terminal.",
    },
    {
        "source": "FRIENDLY_Pattern_011",
        "category": "Friendly Fraud",
        "content": "Friendly fraud (chargeback abuse): legitimate cardholder disputes transaction falsely. Indicators: history of chargebacks, dispute filed immediately after delivery confirmation, high-value item, digital goods dispute, social media evidence of product use post-dispute. Build evidence package: delivery confirmation, IP logs, device fingerprint matching customer. Contest chargeback with documentation.",
    },
    {
        "source": "ELDER_Pattern_012",
        "category": "Elder Financial Abuse",
        "content": "Elder financial abuse indicators: customer age >65, sudden large withdrawals, wire to unknown recipient, multiple cash withdrawals in short period, new authorized user added to account, reluctance to discuss transaction details, mention of lottery winnings or grandchild emergency. Requires mandatory reporting in many states. Contact Adult Protective Services. Do not process suspicious outgoing wires.",
    },
]

class SimpleEmbedder:
    """Simple TF-IDF-like embedding using word frequency vectors"""
    
    def __init__(self, dim=256):
        self.dim = dim
        self.vocab = {}
        self._build_vocab()
    
    def _build_vocab(self):
        """Build vocabulary from knowledge base"""
        words = set()
        for entry in FRAUD_KNOWLEDGE:
            for word in entry["content"].lower().split():
                word = ''.join(c for c in word if c.isalnum())
                if len(word) > 2:
                    words.add(word)
        self.vocab = {w: i % self.dim for i, w in enumerate(sorted(words))}
    
    def embed(self, text: str) -> np.ndarray:
        """Create a simple bag-of-words embedding"""
        vec = np.zeros(self.dim, dtype=np.float32)
        words = text.lower().split()
        for word in words:
            word = ''.join(c for c in word if c.isalnum())
            if word in self.vocab:
                vec[self.vocab[word]] += 1.0
        # Normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec


class FraudRAGEngine:
    def __init__(self, dim=256):
        self.dim = dim
        self.embedder = SimpleEmbedder(dim=dim)
        self.index = faiss.IndexFlatIP(dim)  # Inner product (cosine similarity)
        self.entries: List[Dict] = []
    
    def seed_knowledge_base(self):
        """Index all fraud knowledge documents"""
        self.entries = []
        vectors = []
        for entry in FRAUD_KNOWLEDGE:
            text = f"{entry['category']} {entry['content']}"
            vec = self.embedder.embed(text)
            vectors.append(vec)
            self.entries.append(entry)
        
        matrix = np.array(vectors, dtype=np.float32)
        self.index.reset()
        self.index.add(matrix)
        print(f"✅ Indexed {len(self.entries)} fraud knowledge documents")
    
    def retrieve_context(self, query: str, k: int = 4) -> List[Dict]:
        """Retrieve top-k relevant fraud patterns for query"""
        if self.index.ntotal == 0:
            return []
        
        q_vec = self.embedder.embed(query).reshape(1, -1)
        k = min(k, self.index.ntotal)
        scores, indices = self.index.search(q_vec, k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0:
                entry = self.entries[idx].copy()
                entry["similarity_score"] = float(score)
                results.append(entry)
        return results
    
    def list_entries(self) -> List[Dict]:
        return [{"source": e["source"], "category": e["category"]} for e in self.entries]
