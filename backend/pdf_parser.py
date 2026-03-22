import pdfplumber
import re
from typing import List, Dict, Optional
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

class PDFTransactionParser:
    """Parse PDF files containing transaction details"""
    
    def __init__(self):
        self.transaction_patterns = [
            # Pattern for: Date | Merchant | Amount | Category | Location | Time | Device
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\s+(.+?)\s+([\d,]+\.\d{2})\s+(\w+)\s+(.+?)\s+([\d:]+\s*[AP]?M?)\s+(.+?)(?=\d{1,2}[-/]|$)',
            # Pattern for: Transaction ID | Amount | Merchant
            r'(TXN-?\d+)\s+\$?([\d,]+\.\d{2})\s+(.+?)(?=TXN-?|$)',
        ]
    
    def extract_transactions_from_pdf(self, pdf_file) -> List[Dict]:
        """
        Extract transaction details from PDF
        
        Expected PDF format (flexible):
        - Simple table format with columns: Date, Merchant, Amount, Category, Location, Time, Device
        - Or detailed transaction records with relevant fields
        """
        transactions = []
        
        try:
            # Handle both file path and BytesIO objects
            if isinstance(pdf_file, str):
                pdf = pdfplumber.open(pdf_file)
            else:
                pdf = pdfplumber.open(BytesIO(pdf_file.read()))
            
            for page_num, page in enumerate(pdf.pages):
                # Try to extract tables first (preferred method)
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        table_txns = self._parse_table(table)
                        transactions.extend(table_txns)
                        logger.info(f"Page {page_num + 1}: Extracted {len(table_txns)} transactions from table")
                # Only parse text if no tables were found (to avoid duplicates)
                elif not tables:
                    text = page.extract_text()
                    if text:
                        text_txns = self._parse_text(text)
                        transactions.extend(text_txns)
                        logger.info(f"Page {page_num + 1}: Extracted {len(text_txns)} transactions from unstructured text")
            
            pdf.close()
            
            logger.info(f"Total before deduplication: {len(transactions)} transactions")
            
            # Remove duplicates and validate
            transactions = self._deduplicate_transactions(transactions)
            logger.info(f"Total after deduplication: {len(transactions)} transactions")
            
            transactions = [tx for tx in transactions if self._validate_transaction(tx)]
            
            logger.info(f"Extracted {len(transactions)} valid transactions from PDF")
            return transactions
            
        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            raise ValueError(f"Failed to parse PDF: {str(e)}")
    
    def _parse_table(self, table: List[List[str]]) -> List[Dict]:
        """Parse structured table from PDF"""
        transactions = []
        
        if len(table) < 2:
            return transactions
        
        # Assume first row is headers
        headers = [h.lower().strip() if h else "" for h in table[0]]
        
        # Find column indices
        col_map = {
            'date': self._find_column(headers, ['date', 'transaction date', 'posted']),
            'merchant': self._find_column(headers, ['merchant', 'description', 'vendor']),
            'amount': self._find_column(headers, ['amount', 'value', 'transaction amount']),
            'category': self._find_column(headers, ['category', 'type', 'merchant category']),
            'location': self._find_column(headers, ['location', 'city', 'country', 'address']),
            'time': self._find_column(headers, ['time', 'timestamp', 'time']),
            'device': self._find_column(headers, ['device', 'device id', 'terminal']),
            'ip': self._find_column(headers, ['ip', 'ip address', 'source']),
        }
        
        for row_idx, row in enumerate(table[1:], 1):
            try:
                transaction = self._build_transaction_from_row(row, col_map, row_idx)
                if transaction:
                    transactions.append(transaction)
            except Exception as e:
                logger.warning(f"Failed to parse row {row_idx}: {str(e)}")
                continue
        
        return transactions
    
    def _find_column(self, headers: List[str], keywords: List[str]) -> Optional[int]:
        """Find column index by keyword matching"""
        for idx, header in enumerate(headers):
            for keyword in keywords:
                if keyword in header:
                    return idx
        return None
    
    def _build_transaction_from_row(self, row: List[str], col_map: Dict, row_idx: int) -> Optional[Dict]:
        """Build transaction dict from table row"""
        try:
            def get_value(key):
                idx = col_map.get(key)
                if idx is not None and idx < len(row):
                    val = row[idx]
                    return str(val).strip() if val else ""
                return ""
            
            amount_str = get_value('amount').replace('$', '').replace(',', '').strip()
            amount = float(amount_str) if amount_str else 0.0
            
            if amount <= 0:
                return None
            
            transaction = {
                "transaction_id": f"PDF-TXN-{row_idx:04d}",
                "date": get_value('date'),
                "merchant": get_value('merchant') or "Unknown Merchant",
                "amount": amount,
                "merchant_category": get_value('category') or "General",
                "location": get_value('location') or "Unknown",
                "time": get_value('time') or "Unknown",
                "device": get_value('device') or "Unknown Device",
                "ip_address": get_value('ip') or "Unknown",
                "card_holder": "PDF Upload",
                "usual_location": "N/A",
                "last_transaction": "N/A",
                "description": f"Merchant: {get_value('merchant')}, Amount: ${amount:.2f}",
            }
            return transaction
        except Exception as e:
            logger.warning(f"Error building transaction from row: {str(e)}")
            return None
    
    def _parse_text(self, text: str) -> List[Dict]:
        """Parse unstructured text for transaction patterns"""
        transactions = []
        
        # Try to find transaction patterns
        transaction_id = 1
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue
            
            # Look for lines that might contain transaction data
            if any(keyword in line.lower() for keyword in 
                   ['merchant', 'amount', 'transaction', '$', 'card', 'charge']):
                
                # Try to extract amount
                amount_match = re.search(r'\$?([\d,]+\.?\d{0,2})', line)
                if amount_match:
                    amount = float(amount_match.group(1).replace(',', ''))
                    if amount > 0:
                        # Extract merchant name (assume it's before the amount)
                        merchant = line[:amount_match.start()].split()[-1] if amount_match.start() > 0 else "Unknown"
                        
                        transaction = {
                            "transaction_id": f"PDF-TXN-{transaction_id:04d}",
                            "date": "N/A",
                            "merchant": merchant,
                            "amount": amount,
                            "merchant_category": "General",
                            "location": "Unknown",
                            "time": "Unknown",
                            "device": "Unknown Device",
                            "ip_address": "Unknown",
                            "card_holder": "PDF Upload",
                            "usual_location": "N/A",
                            "last_transaction": "N/A",
                            "description": line,
                        }
                        transactions.append(transaction)
                        transaction_id += 1
        
        return transactions
    
    def _deduplicate_transactions(self, transactions: List[Dict]) -> List[Dict]:
        """Remove duplicate transactions using multiple strategies"""
        seen = {}
        unique = []
        
        for tx in transactions:
            # Create a comprehensive signature for deduplication
            merchant = str(tx.get('merchant', '')).strip().lower()
            amount = round(float(tx.get('amount', 0)), 2)
            date = str(tx.get('date', '')).strip().lower()
            location = str(tx.get('location', '')).strip().lower()
            time = str(tx.get('time', '')).strip().lower()
            
            # Primary signature: merchant, amount, date, location, time
            primary_sig = (merchant, amount, date, location, time)
            
            # Secondary signature: merchant, amount, date (more lenient)
            secondary_sig = (merchant, amount, date)
            
            # Check primary signature first (strict match)
            if primary_sig in seen:
                logger.warning(f"Duplicate detected (strict): {merchant} ${amount} on {date}")
                continue
            
            # Check secondary signature (loose match)
            if secondary_sig in seen and secondary_sig != ('', 0, ''):
                # Allow if time is different (same transaction at different time is suspicious but not duplicate)
                if time and time != seen[secondary_sig].get('time', '').strip().lower():
                    pass  # Different time, keep it
                else:
                    logger.warning(f"Duplicate detected (loose): {merchant} ${amount} on {date}")
                    continue
            
            seen[primary_sig] = tx
            unique.append(tx)
        
        logger.info(f"Deduplication: {len(transactions)} → {len(unique)} transactions")
        return unique
    
    def _validate_transaction(self, transaction: Dict) -> bool:
        """Validate transaction has required fields"""
        required = ['merchant', 'amount']
        return all(transaction.get(field) for field in required) and transaction.get('amount', 0) > 0


def extract_pdf_transactions(pdf_file) -> List[Dict]:
    """Convenience function to extract transactions from PDF"""
    parser = PDFTransactionParser()
    return parser.extract_transactions_from_pdf(pdf_file)
