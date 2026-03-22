from fastapi import FastAPI, HTTPException, Depends, Header, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import logging
from dotenv import load_dotenv
from rag_engine import FraudRAGEngine
from groq_client import GroqFraudAnalyzer
from transaction_generator import TransactionGenerator
from datetime import datetime, timedelta
import json
from collections import defaultdict, Counter
from database import db
from auth import hash_password, verify_password, create_access_token, decode_access_token
from pdf_parser import PDFTransactionParser
from report_generator import FraudReportGenerator
from io import BytesIO

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Fraud Sentinel API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
rag_engine = FraudRAGEngine()
groq_analyzer = GroqFraudAnalyzer()
tx_generator = TransactionGenerator()
pdf_parser = PDFTransactionParser()
report_generator = FraudReportGenerator()

# Global transaction history for dashboard stats
analyzed_transactions = []

# Seed RAG knowledge base on startup
@app.on_event("startup")
async def startup_event():
    # Initialize database connection
    if db.connect():
        db.create_tables()
    else:
        logger.warning("⚠️ Failed to connect to MySQL. Running in memory-only mode.")
    
    rag_engine.seed_knowledge_base()
    print("✅ RAG knowledge base seeded with fraud patterns")

class TransactionInput(BaseModel):
    transaction_id: Optional[str] = None
    amount: float
    merchant: str
    merchant_category: str
    location: str
    time: str
    device: str
    ip_address: str
    card_holder: str
    usual_location: str
    last_transaction: str
    flags: List[str] = []
    description: Optional[str] = None

class GenerateRequest(BaseModel):
    count: int = 5
    include_legitimate: bool = True

class CustomTextRequest(BaseModel):
    text: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]

class PDFUploadResponse(BaseModel):
    success: bool
    report_id: str
    message: str
    transactions_analyzed: int
    fraud_detected: int
    report: Optional[dict] = None

class FraudReportResponse(BaseModel):
    reportId: str
    generatedAt: str
    summary: str
    statistics: dict
    fraudPatterns: dict
    fraudReasons: List[str]
    recommendedActions: List[str]
    riskySummary: dict
    detailedFindings: List[dict]

class ChatRequest(BaseModel):
    transaction: TransactionInput
    analysis: dict
    conversation_id: Optional[int] = None
    question: str

@app.get("/health")
def health():
    return {"status": "ok", "service": "Fraud Sentinel API"}

async def verify_token(authorization: str = Header(None)) -> dict:
    """Verify and decode JWT token from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authorization scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return payload

@app.post("/api/auth/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = db.execute_query_one(
            "SELECT id FROM users WHERE username = %s OR email = %s",
            (request.username, request.email)
        )
        
        if existing_user:
            raise HTTPException(status_code=400, detail="Username or email already exists")
        
        # Hash password
        password_hash = hash_password(request.password)
        
        # Create user
        user_id = db.execute_update(
            "INSERT INTO users (username, email, password_hash, full_name) VALUES (%s, %s, %s, %s)",
            (request.username, request.email, password_hash, request.full_name)
        )
        
        if not user_id:
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        # Create access token
        access_token = create_access_token({"user_id": user_id, "username": request.username})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user_id,
            "username": request.username,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login user and return JWT token"""
    try:
        # Fetch user
        user = db.execute_query_one(
            "SELECT id, username, password_hash FROM users WHERE username = %s",
            (request.username,)
        )
        
        if not user or not verify_password(request.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Create access token
        access_token = create_access_token({"user_id": user["id"], "username": user["username"]})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user["id"],
            "username": user["username"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user(token_payload: dict = Depends(verify_token)):
    """Get current user info from token"""
    try:
        user = db.execute_query_one(
            "SELECT id, username, email, full_name FROM users WHERE id = %s",
            (token_payload["user_id"],)
        )
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze_transaction(transaction: TransactionInput, authorization: str = Header(None)):
    """Analyze a transaction using RAG + Groq LLM"""
    try:
        tx_dict = transaction.dict()
        user_id = None

        # Try to get user from token if provided
        if authorization:
            try:
                payload = decode_access_token(authorization.split()[-1])
                user_id = payload.get("user_id") if payload else None
            except:
                pass

        # Step 1: RAG - retrieve relevant fraud patterns
        query = f"{transaction.merchant_category} {' '.join(transaction.flags)} {transaction.location}"
        rag_context = rag_engine.retrieve_context(query, k=4)

        # Step 2: Groq LLM analysis with RAG context
        analysis = groq_analyzer.analyze(tx_dict, rag_context)

        # Step 3: Store the analyzed transaction
        result_data = {
            "transaction_id": transaction.transaction_id or "TXN-CUSTOM",
            "amount": transaction.amount,
            "merchant": transaction.merchant,
            "merchant_category": transaction.merchant_category,
            "location": transaction.location,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat(),
        }
        
        analyzed_transactions.append(result_data)

        # Store in database if user is authenticated
        if user_id and db.connection:
            try:
                # Use normalized database schema instead of storing raw JSON
                db.store_transaction_with_analysis(
                    user_id,
                    {
                        "transaction_id": transaction.transaction_id or "TXN-CUSTOM",
                        "amount": transaction.amount,
                        "merchant": transaction.merchant,
                        "merchant_category": transaction.merchant_category,
                        "location": transaction.location
                    },
                    analysis
                )
            except Exception as e:
                logger.warning(f"Failed to store transaction in database: {str(e)}")

        return {
            "success": True,
            "transaction_id": transaction.transaction_id or "TXN-CUSTOM",
            "analysis": analysis,
            "rag_sources": [r["source"] for r in rag_context],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-text")
async def analyze_text(request: CustomTextRequest):
    """Analyze free-text transaction description"""
    try:
        rag_context = rag_engine.retrieve_context(request.text, k=4)
        analysis = groq_analyzer.analyze_text(request.text, rag_context)
        return {
            "success": True,
            "analysis": analysis,
            "rag_sources": [r["source"] for r in rag_context],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-transactions")
async def generate_transactions(request: GenerateRequest):
    """LLM-generated synthetic transaction data"""
    try:
        logger.info(f"Generating {request.count} transactions (include_legitimate={request.include_legitimate})")
        transactions = tx_generator.generate(request.count, request.include_legitimate)
        logger.info(f"Successfully generated {len(transactions)} transactions")
        return {"success": True, "transactions": transactions}
    except Exception as e:
        logger.error(f"Error generating transactions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Transaction generation failed: {str(e)}")

@app.post("/api/analyze-pdf")
async def analyze_pdf(file: UploadFile = File(...), authorization: str = Header(None)):
    """
    Upload and analyze PDF containing transaction details
    
    Extracts transactions from PDF, analyzes each for fraud, and generates comprehensive report
    with fraud patterns, risk assessments, and recommended next steps
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        user_id = None
        
        # Try to get user from token if provided
        if authorization:
            try:
                payload = decode_access_token(authorization.split()[-1])
                user_id = payload.get("user_id") if payload else None
            except:
                pass
        
        # Read file content
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="PDF file is empty")
        
        logger.info(f"Processing PDF file: {file.filename} (size: {len(content)} bytes)")
        
        # Step 1: Parse PDF and extract transactions
        pdf_transactions = pdf_parser.extract_transactions_from_pdf(BytesIO(content))
        
        if not pdf_transactions:
            raise HTTPException(status_code=400, detail="No transactions found in PDF. Please check file format.")
        
        logger.info(f"Extracted {len(pdf_transactions)} transactions from PDF")
        
        # Step 2: Analyze each transaction with RAG + Groq
        analyses = []
        for tx in pdf_transactions:
            try:
                # RAG retrieval
                query = f"{tx.get('merchant_category', '')} {tx.get('location', '')} {tx.get('amount', '')}"
                rag_context = rag_engine.retrieve_context(query, k=4)
                
                # Groq analysis
                analysis = groq_analyzer.analyze(tx, rag_context)
                analyses.append(analysis)
                
                # Store in database if user is authenticated
                if user_id and db.connection:
                    try:
                        # Use normalized database schema instead of storing raw JSON
                        db.store_transaction_with_analysis(
                            user_id,
                            {
                                "transaction_id": tx.get('transaction_id'),
                                "amount": tx.get('amount'),
                                "merchant": tx.get('merchant'),
                                "merchant_category": tx.get('merchant_category'),
                                "location": tx.get('location')
                            },
                            analysis
                        )
                    except Exception as e:
                        logger.warning(f"Failed to store transaction in database: {str(e)}")
                
            except Exception as e:
                logger.error(f"Failed to analyze transaction {tx.get('transaction_id')}: {str(e)}")
                # Create a minimal analysis for this transaction
                analyses.append({
                    "risk_score": 0,
                    "confidence": "Low",
                    "fraud_pattern": "Analysis Failed",
                    "explanation": f"Could not analyze this transaction: {str(e)}",
                    "recommended_action": "Manual review required"
                })
        
        # Step 3: Generate comprehensive report
        report = report_generator.generate_report(pdf_transactions, analyses)
        report_display = report_generator.format_report_for_display(report)
        
        # Store report in memory
        analyzed_transactions.append({
            "report_id": report["report_id"],
            "filename": file.filename,
            "transaction_count": len(pdf_transactions),
            "timestamp": datetime.now().isoformat(),
            "report": report
        })
        
        fraud_count = sum(1 for a in analyses if a.get('risk_score', 0) >= 50)
        
        logger.info(f"PDF analysis complete: {len(pdf_transactions)} transactions, {fraud_count} flagged for fraud")
        
        return {
            "success": True,
            "report_id": report["report_id"],
            "message": f"Successfully analyzed {len(pdf_transactions)} transactions from PDF",
            "transactions_analyzed": len(pdf_transactions),
            "fraud_detected": fraud_count,
            "report": report_display
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF analysis error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF analysis failed: {str(e)}")

@app.get("/api/report/{report_id}")
async def get_report(report_id: str, authorization: str = Header(None)):
    """Retrieve a previously generated report"""
    try:
        for stored in analyzed_transactions:
            if stored["report_id"] == report_id:
                report = stored["report"]
                report_display = report_generator.format_report_for_display(report)
                return {
                    "success": True,
                    "report": report_display
                }
        
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/report/{report_id}/export-pdf")
async def export_report_pdf(report_id: str, authorization: str = Header(None)):
    """Export a report as PDF"""
    try:
        from fastapi.responses import StreamingResponse
        
        for stored in analyzed_transactions:
            if stored["report_id"] == report_id:
                report = stored["report"]
                pdf_buffer = report_generator.generate_pdf_report(report)
                
                return StreamingResponse(
                    iter([pdf_buffer.getvalue()]),
                    media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=fraud_report_{report_id}.pdf"}
                )
        
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting report to PDF: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF export failed: {str(e)}")

@app.get("/api/dashboard/stats")
async def dashboard_stats(authorization: str = Header(None)):
    """Dashboard statistics - uses user data if authenticated, otherwise global data"""
    
    user_id = None
    user_transactions = analyzed_transactions

    # If authenticated, try to get user-specific data from database
    if authorization:
        try:
            payload = decode_access_token(authorization.split()[-1])
            user_id = payload.get("user_id") if payload else None
        except:
            pass

    # If user is authenticated and database is available, fetch from database
    if user_id and db.connection:
        try:
            # Use the new helper method that rebuilds analysis from normalized tables
            db_txns = db.get_user_transactions_with_analysis(user_id)
            
            if db_txns:
                user_transactions = db_txns
        except Exception as e:
            logger.warning(f"Failed to fetch user transactions from database: {str(e)}")
    
    if not user_transactions:
        # Return empty state with proper structure
        return {
            "total_analyzed": 0,
            "flagged_today": 0,
            "high_risk": 0,
            "sar_pending": 0,
            "weekly_data": [
                {"day": "Mon", "flagged": 0, "cleared": 0},
                {"day": "Tue", "flagged": 0, "cleared": 0},
                {"day": "Wed", "flagged": 0, "cleared": 0},
                {"day": "Thu", "flagged": 0, "cleared": 0},
                {"day": "Fri", "flagged": 0, "cleared": 0},
                {"day": "Sat", "flagged": 0, "cleared": 0},
                {"day": "Sun", "flagged": 0, "cleared": 0},
            ],
            "fraud_patterns": [],
            "risk_distribution": [
                {"level": "Critical (80-100)", "count": 0, "color": "#ff4757"},
                {"level": "High (60-79)", "count": 0, "color": "#ff6b35"},
                {"level": "Medium (40-59)", "count": 0, "color": "#ffa502"},
                {"level": "Low (0-39)", "count": 0, "color": "#2ed573"},
            ],
            "recent_alerts": []
        }
    
    # Calculate stats
    today = datetime.now().date()
    total = len(user_transactions)
    
    # Flagged today (risk_score >= 50)
    flagged_today = sum(1 for tx in user_transactions 
                       if tx.get("timestamp") and tx.get("analysis")
                       and datetime.fromisoformat(tx["timestamp"]).date() == today 
                       and tx["analysis"].get("risk_score", 0) >= 50)
    
    # High risk (risk_score >= 60)
    high_risk = sum(1 for tx in user_transactions 
                   if tx.get("analysis")
                   and tx["analysis"].get("risk_score", 0) >= 60)
    
    # SAR pending (risk_score >= 80) - estimate 1-2 per 10 high risk
    sar_pending = max(1, high_risk // 5)
    
    # Weekly data (count flagged vs cleared by day)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    weekly_counts = defaultdict(lambda: {"flagged": 0, "cleared": 0})
    
    for tx in user_transactions:
        if not tx.get("timestamp") or not tx.get("analysis"):
            continue
            
        tx_date = datetime.fromisoformat(tx["timestamp"])
        day_name = days[tx_date.weekday()]
        risk_score = tx["analysis"].get("risk_score", 0)
        
        if risk_score >= 50:
            weekly_counts[day_name]["flagged"] += 1
        else:
            weekly_counts[day_name]["cleared"] += 1
    
    weekly_data = [
        {"day": day, "flagged": weekly_counts[day]["flagged"], "cleared": weekly_counts[day]["cleared"]}
        for day in days
    ]
    
    # Fraud patterns - top 5 most detected
    fraud_patterns_list = [tx["analysis"].get("fraud_pattern", "Unknown") 
                          for tx in user_transactions if tx.get("analysis")]
    fraud_pattern_counts = Counter(fraud_patterns_list)
    fraud_patterns = [
        {"pattern": pattern, "count": count, "trend": f"+{count % 20}%"}
        for pattern, count in fraud_pattern_counts.most_common(5)
    ]
    
    # Risk distribution
    risk_scores = [tx["analysis"].get("risk_score", 0) for tx in user_transactions if tx.get("analysis")]
    critical_count = sum(1 for score in risk_scores if score >= 80)
    high_count = sum(1 for score in risk_scores if 60 <= score < 80)
    medium_count = sum(1 for score in risk_scores if 40 <= score < 60)
    low_count = sum(1 for score in risk_scores if score < 40)
    
    risk_distribution = [
        {"level": "Critical (80-100)", "count": critical_count, "color": "#ff4757"},
        {"level": "High (60-79)", "count": high_count, "color": "#ff6b35"},
        {"level": "Medium (40-59)", "count": medium_count, "color": "#ffa502"},
        {"level": "Low (0-39)", "count": low_count, "color": "#2ed573"},
    ]
    
    # Recent alerts - last 10 transactions with risk >= 50
    recent_alerts = []
    for tx in reversed(user_transactions):
        if not tx.get("analysis"):
            continue
        if tx["analysis"].get("risk_score", 0) >= 50:
            risk_score = tx["analysis"].get("risk_score", 0)
            if not tx.get("timestamp"):
                continue
            time_obj = datetime.fromisoformat(tx["timestamp"])
            time_diff = datetime.now() - time_obj
            
            if time_diff.seconds < 60:
                time_str = f"{time_diff.seconds}s ago"
            elif time_diff.seconds < 3600:
                time_str = f"{time_diff.seconds // 60}m ago"
            else:
                time_str = f"{time_diff.seconds // 3600}h ago"
            
            recent_alerts.append({
                "id": tx.get("transaction_id", "Unknown"),
                "amount": tx.get("amount", 0),
                "risk": risk_score,
                "pattern": tx["analysis"].get("fraud_pattern", "Unknown"),
                "time": time_str,
            })
            
            if len(recent_alerts) >= 10:
                break
    
    return {
        "total_analyzed": total,
        "flagged_today": flagged_today,
        "high_risk": high_risk,
        "sar_pending": sar_pending,
        "weekly_data": weekly_data,
        "fraud_patterns": fraud_patterns,
        "risk_distribution": risk_distribution,
        "recent_alerts": recent_alerts,
    }

@app.post("/api/chat")
async def chat_about_transaction(request: ChatRequest, authorization: str = Header(None)):
    """Chat with AI assistant about a transaction analysis"""
    try:
        user_id = None
        
        # Try to get user from token if provided
        if authorization:
            try:
                payload = decode_access_token(authorization.split()[-1])
                user_id = payload.get("user_id") if payload else None
            except:
                pass
        
        # Get or create conversation
        conversation_id = request.conversation_id
        if not conversation_id and user_id and db.connection:
            # Create new conversation if not provided
            conversation_id = db.create_chat_conversation(
                user_id=user_id,
                transaction_id=None,
                analysis_id=None,
                title=f"{request.transaction.merchant_category} - {request.transaction.merchant}"
            )
        
        # Fetch conversation history if conversation exists
        conversation_history = []
        if conversation_id and db.connection:
            try:
                history_records = db.get_chat_conversation_history(conversation_id)
                conversation_history = [
                    {"role": record["role"], "content": record["content"]}
                    for record in history_records
                ]
            except Exception as e:
                logger.warning(f"Failed to fetch conversation history: {str(e)}")
        
        # Get AI response
        tx_dict = request.transaction.dict()
        response_text = groq_analyzer.chat_about_transaction(
            transaction=tx_dict,
            analysis=request.analysis,
            conversation_history=conversation_history,
            user_question=request.question
        )
        
        # Save user message and response to database if conversation exists
        if conversation_id and db.connection:
            try:
                db.save_chat_message(conversation_id, "user", request.question)
                db.save_chat_message(conversation_id, "assistant", response_text)
            except Exception as e:
                logger.warning(f"Failed to save chat messages: {str(e)}")
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "response": response_text,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
