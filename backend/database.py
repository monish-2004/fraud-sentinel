import mysql.connector
from mysql.connector import Error
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseConnection:
    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.user = os.getenv("DB_USER", "root")
        self.password = os.getenv("DB_PASSWORD", "")
        self.database = os.getenv("DB_NAME", "fraud_sentinel")
        self.port = int(os.getenv("DB_PORT", 3306))
        self.connection = None

    def connect(self):
        """Create connection to MySQL database"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port
            )
            if self.connection.is_connected():
                logger.info("✅ Connected to MySQL database")
                return True
        except Error as e:
            logger.error(f"❌ Error connecting to MySQL: {e}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Disconnected from MySQL database")

    def create_tables(self):
        """Create required tables if they don't exist"""
        if not self.connection:
            logger.error("Database not connected")
            return False

        cursor = self.connection.cursor()
        try:
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)

            # Create transactions table - OPTIMIZED: store only essential transaction data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    transaction_id VARCHAR(255) NOT NULL UNIQUE,
                    amount DECIMAL(15, 2) NOT NULL,
                    merchant VARCHAR(255),
                    merchant_category VARCHAR(100),
                    location VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    INDEX idx_user_created (user_id, created_at),
                    INDEX idx_transaction_id (transaction_id)
                )
            """)

            # Create fraud analysis table - OPTIMIZED: store analysis details separately
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fraud_analysis (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    transaction_id INT NOT NULL UNIQUE,
                    risk_score INT NOT NULL,
                    risk_level VARCHAR(50) NOT NULL,
                    confidence VARCHAR(50),
                    fraud_pattern VARCHAR(100),
                    explanation TEXT,
                    sar_required BOOLEAN DEFAULT FALSE,
                    fraud_probability VARCHAR(10),
                    customer_message TEXT,
                    technical_details TEXT,
                    rag_reasoning TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
                    INDEX idx_risk_score (risk_score),
                    INDEX idx_fraud_pattern (fraud_pattern),
                    INDEX idx_created_at (created_at)
                )
            """)

            # Create recovery steps table - OPTIMIZED: normalized list of actions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recovery_steps (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    analysis_id INT NOT NULL,
                    step_text VARCHAR(255) NOT NULL,
                    step_order INT,
                    FOREIGN KEY (analysis_id) REFERENCES fraud_analysis(id) ON DELETE CASCADE,
                    INDEX idx_analysis_id (analysis_id)
                )
            """)

            # Create immediate actions table - OPTIMIZED: normalized list of actions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS immediate_actions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    analysis_id INT NOT NULL,
                    action_text VARCHAR(255) NOT NULL,
                    action_order INT,
                    FOREIGN KEY (analysis_id) REFERENCES fraud_analysis(id) ON DELETE CASCADE,
                    INDEX idx_analysis_id (analysis_id)
                )
            """)

            # Create similar patterns table - OPTIMIZED: normalized related patterns
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS similar_patterns (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    analysis_id INT NOT NULL,
                    pattern_name VARCHAR(100) NOT NULL,
                    FOREIGN KEY (analysis_id) REFERENCES fraud_analysis(id) ON DELETE CASCADE,
                    INDEX idx_analysis_id (analysis_id)
                )
            """)

            # Create chat conversations table - store conversation metadata
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_conversations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    transaction_id INT,
                    analysis_id INT,
                    title VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
                    FOREIGN KEY (analysis_id) REFERENCES fraud_analysis(id) ON DELETE CASCADE,
                    INDEX idx_user_id (user_id),
                    INDEX idx_transaction_id (transaction_id),
                    INDEX idx_created_at (created_at)
                )
            """)

            # Create chat messages table - store individual messages
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    conversation_id INT NOT NULL,
                    role VARCHAR(10) NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES chat_conversations(id) ON DELETE CASCADE,
                    INDEX idx_conversation_id (conversation_id),
                    INDEX idx_created_at (created_at)
                )
            """)

            self.connection.commit()
            logger.info("✅ Database tables created successfully")
            return True
        except Error as e:
            logger.error(f"❌ Error creating tables: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()

    def execute_query(self, query, params=None):
        """Execute a SELECT query"""
        if not self.connection:
            logger.error("Database not connected")
            return None

        cursor = self.connection.cursor(dictionary=True)
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        except Error as e:
            logger.error(f"❌ Error executing query: {e}")
            return None
        finally:
            cursor.close()

    def execute_query_one(self, query, params=None):
        """Execute a SELECT query and return one result"""
        if not self.connection:
            logger.error("Database not connected")
            return None

        cursor = self.connection.cursor(dictionary=True)
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchone()
        except Error as e:
            logger.error(f"❌ Error executing query: {e}")
            return None
        finally:
            cursor.close()

    def execute_update(self, query, params=None):
        """Execute INSERT, UPDATE, or DELETE query"""
        if not self.connection:
            logger.error("Database not connected")
            return False

        cursor = self.connection.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            logger.error(f"❌ Error executing update: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()

    def store_transaction_with_analysis(self, user_id, transaction_data, analysis_data):
        """Store transaction and analysis data in normalized tables"""
        if not self.connection:
            logger.error("Database not connected")
            return False

        cursor = self.connection.cursor()
        try:
            # Insert transaction
            cursor.execute(
                """INSERT INTO transactions 
                (user_id, transaction_id, amount, merchant, merchant_category, location) 
                VALUES (%s, %s, %s, %s, %s, %s)""",
                (user_id, transaction_data.get("transaction_id"), transaction_data.get("amount"),
                 transaction_data.get("merchant"), transaction_data.get("merchant_category"),
                 transaction_data.get("location"))
            )
            transaction_id = cursor.lastrowid

            # Insert fraud analysis (stores only critical fields, not entire JSON)
            risk_score = analysis_data.get("risk_score", 0)
            risk_level = "high" if risk_score >= 60 else "medium" if risk_score >= 40 else "low"

            cursor.execute(
                """INSERT INTO fraud_analysis 
                (transaction_id, risk_score, risk_level, confidence, fraud_pattern, 
                 explanation, sar_required, fraud_probability, customer_message, 
                 technical_details, rag_reasoning) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (transaction_id, risk_score, risk_level,
                 analysis_data.get("confidence"), analysis_data.get("fraud_pattern"),
                 analysis_data.get("explanation", "")[:5000],  # Limit text size
                 analysis_data.get("sar_required", False),
                 analysis_data.get("fraud_probability"),
                 analysis_data.get("customer_message", "")[:1000],
                 analysis_data.get("technical_details", "")[:2000],
                 analysis_data.get("rag_reasoning", "")[:2000])
            )
            analysis_id = cursor.lastrowid

            # Insert recovery steps
            recovery_steps = analysis_data.get("recovery_steps", [])
            for idx, step in enumerate(recovery_steps):
                cursor.execute(
                    "INSERT INTO recovery_steps (analysis_id, step_text, step_order) VALUES (%s, %s, %s)",
                    (analysis_id, step[:255], idx)
                )

            # Insert immediate actions
            immediate_actions = analysis_data.get("immediate_actions", [])
            for idx, action in enumerate(immediate_actions):
                cursor.execute(
                    "INSERT INTO immediate_actions (analysis_id, action_text, action_order) VALUES (%s, %s, %s)",
                    (analysis_id, action[:255], idx)
                )

            # Insert similar patterns
            similar_patterns = analysis_data.get("similar_patterns", [])
            for pattern in similar_patterns:
                cursor.execute(
                    "INSERT INTO similar_patterns (analysis_id, pattern_name) VALUES (%s, %s)",
                    (analysis_id, pattern[:100])
                )

            self.connection.commit()
            logger.info(f"✅ Transaction {transaction_data.get('transaction_id')} stored in database")
            return transaction_id

        except Error as e:
            logger.error(f"❌ Error storing transaction: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()

    def get_user_transactions_with_analysis(self, user_id, limit=100):
        """
        Fetch user transactions with complete analysis data from normalized tables.
        Returns in format compatible with legacy code.
        """
        if not self.connection:
            logger.error("Database not connected")
            return []

        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute("""
                SELECT 
                    t.id, t.transaction_id, t.amount, t.merchant, 
                    t.merchant_category, t.location, t.created_at,
                    fa.risk_score, fa.risk_level, fa.confidence, 
                    fa.fraud_pattern, fa.explanation, fa.sar_required,
                    fa.fraud_probability, fa.customer_message,
                    fa.technical_details, fa.rag_reasoning
                FROM transactions t
                LEFT JOIN fraud_analysis fa ON t.id = fa.transaction_id
                WHERE t.user_id = %s
                ORDER BY t.created_at DESC
                LIMIT %s
            """, (user_id, limit))
            
            results = []
            for row in cursor.fetchall():
                if row is None:
                    continue
                    
                # Build analysis dict from fraud_analysis columns
                # Handle NULL values from LEFT JOIN explicitly
                analysis = {
                    "risk_score": row.get("risk_score") if row.get("risk_score") is not None else 0,
                    "risk_level": row.get("risk_level") if row.get("risk_level") is not None else "low",
                    "confidence": row.get("confidence") if row.get("confidence") is not None else "Unknown",
                    "fraud_pattern": row.get("fraud_pattern") if row.get("fraud_pattern") is not None else "Unknown",
                    "explanation": row.get("explanation") if row.get("explanation") is not None else "",
                    "sar_required": row.get("sar_required") if row.get("sar_required") is not None else False,
                    "fraud_probability": row.get("fraud_probability") if row.get("fraud_probability") is not None else "0%",
                    "customer_message": row.get("customer_message") if row.get("customer_message") is not None else "",
                    "technical_details": row.get("technical_details") if row.get("technical_details") is not None else "",
                    "rag_reasoning": row.get("rag_reasoning") if row.get("rag_reasoning") is not None else ""
                }
                
                # Fetch related lists if analysis exists (transaction_id is not None)
                if row.get("id") and row.get("risk_score") is not None:
                    # Only fetch extra data if fraud_analysis exists
                    try:
                        # Recovery steps
                        cursor2 = self.connection.cursor(dictionary=True)
                        cursor2.execute(
                            "SELECT step_text FROM recovery_steps WHERE analysis_id = (SELECT id FROM fraud_analysis WHERE transaction_id = %s) ORDER BY step_order",
                            (row.get("id"),)
                        )
                        analysis["recovery_steps"] = [r["step_text"] for r in cursor2.fetchall()]
                        cursor2.close()
                        
                        # Immediate actions
                        cursor2 = self.connection.cursor(dictionary=True)
                        cursor2.execute(
                            "SELECT action_text FROM immediate_actions WHERE analysis_id = (SELECT id FROM fraud_analysis WHERE transaction_id = %s) ORDER BY action_order",
                            (row.get("id"),)
                        )
                        analysis["immediate_actions"] = [r["action_text"] for r in cursor2.fetchall()]
                        cursor2.close()
                        
                        # Similar patterns
                        cursor2 = self.connection.cursor(dictionary=True)
                        cursor2.execute(
                            "SELECT pattern_name FROM similar_patterns WHERE analysis_id = (SELECT id FROM fraud_analysis WHERE transaction_id = %s)",
                            (row.get("id"),)
                        )
                        analysis["similar_patterns"] = [r["pattern_name"] for r in cursor2.fetchall()]
                        cursor2.close()
                    except Exception as e:
                        # If extra data fetch fails, just use what we have
                        logger.warning(f"Failed to fetch related data for transaction: {e}")
                        analysis["recovery_steps"] = []
                        analysis["immediate_actions"] = []
                        analysis["similar_patterns"] = []
                else:
                    # No fraud analysis exists, use empty lists
                    analysis["recovery_steps"] = []
                    analysis["immediate_actions"] = []
                    analysis["similar_patterns"] = []
                
                results.append({
                    "transaction_id": row.get("transaction_id"),
                    "amount": row.get("amount"),
                    "merchant": row.get("merchant"),
                    "merchant_category": row.get("merchant_category"),
                    "location": row.get("location"),
                    "timestamp": row.get("created_at").isoformat() if row.get("created_at") else None,
                    "analysis": analysis
                })
            
            return results
            
        except Error as e:
            logger.error(f"❌ Error fetching transactions with analysis: {e}")
            return []
        finally:
            cursor.close()

    def create_chat_conversation(self, user_id, transaction_id, analysis_id, title="Chat"):
        """Create a new chat conversation"""
        if not self.connection:
            logger.error("Database not connected")
            return None

        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """INSERT INTO chat_conversations 
                (user_id, transaction_id, analysis_id, title) 
                VALUES (%s, %s, %s, %s)""",
                (user_id, transaction_id, analysis_id, title)
            )
            self.connection.commit()
            conversation_id = cursor.lastrowid
            logger.info(f"✅ Chat conversation {conversation_id} created")
            return conversation_id
        except Error as e:
            logger.error(f"❌ Error creating chat conversation: {e}")
            self.connection.rollback()
            return None
        finally:
            cursor.close()

    def save_chat_message(self, conversation_id, role, content):
        """Save a chat message (user or assistant)"""
        if not self.connection:
            logger.error("Database not connected")
            return False

        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """INSERT INTO chat_messages (conversation_id, role, content) 
                VALUES (%s, %s, %s)""",
                (conversation_id, role, content)
            )
            self.connection.commit()
            logger.info(f"✅ Chat message saved to conversation {conversation_id}")
            return cursor.lastrowid
        except Error as e:
            logger.error(f"❌ Error saving chat message: {e}")
            self.connection.rollback()
            return False
        finally:
            cursor.close()

    def get_chat_conversation_history(self, conversation_id):
        """Fetch full chat history for a conversation"""
        if not self.connection:
            logger.error("Database not connected")
            return []

        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT role, content, created_at FROM chat_messages 
                WHERE conversation_id = %s 
                ORDER BY created_at ASC""",
                (conversation_id,)
            )
            return cursor.fetchall()
        except Error as e:
            logger.error(f"❌ Error fetching chat history: {e}")
            return []
        finally:
            cursor.close()

# Global database instance
db = DatabaseConnection()
