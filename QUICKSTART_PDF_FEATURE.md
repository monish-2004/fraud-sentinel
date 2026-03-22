# Quick Start Guide - PDF Upload Feature

## Installation

### 1. Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

This installs:
- `pdfplumber` - PDF parsing and extraction
- `python-multipart` - File upload handling
- `openpyxl` - Future Excel support

### 2. Restart Backend Server
```bash
python main.py
```

The API is now ready to handle PDF uploads at `POST /api/analyze-pdf`

## Testing with Sample PDF

### Option 1: Create a Test PDF
Create a simple CSV and convert to PDF, or use a banking app export. The PDF should have columns like:

```
Date          | Merchant              | Amount  | Category  | Location    | Time
2026-03-14   | Amazon                | 49.99   | Retail    | Seattle, WA | 14:30 PM
2026-03-14   | Circle K              | 35.67   | Gas       | Portland, OR| 15:10 PM
2026-03-14   | Target                | 123.45  | Retail    | Seattle, WA | 16:45 PM
```

### Option 2: Use Your Bank Statement PDF
Most banks provide transaction exports in PDF format - just upload those directly!

## Using the Feature

### 1. Navigate to Analyze Page
- Click the **Analyze** tab in the navigation

### 2. Switch to PDF Mode
- Click the **📄 PDF Upload** button (third tab in mode switcher)

### 3. Upload Your PDF
- Click the upload area or drag-and-drop a PDF file
- Wait for analysis (1-2 minutes for typical PDFs)

### 4. Review the Report

#### **Overview Tab** 📊
See high-level statistics:
- Total transactions analyzed
- Fraud detection rate
- Risk distribution across severity levels

#### **Patterns Tab** 🔍
Understand what types of fraud were detected:
- Account Takeover, Card-Not-Present, Geo Anomaly, etc.
- Count and explanation for each pattern

#### **Risks Tab** ⚠️
Identify problem merchants and locations:
- Merchants with fraud activity
- Geographic anomalies
- Risk scores for each

#### **Actions Tab** ✅
Get step-by-step recommended responses:
1. Freeze account
2. Reset password
3. Enable 2FA
... (12 priority-ordered steps based on fraud types detected)

#### **Findings Tab** 🔎
Deep dive into individual high-risk transactions:
- Transaction ID and amount
- Detected fraud pattern
- Why it's suspicious
- Confidence level
- What merchant was involved

## Understanding the Report

### Risk Scores
- 🔴 **80-100**: CRITICAL - Immediate action required
- 🟠 **60-79**: HIGH - Urgent attention needed
- 🟡 **40-59**: MEDIUM - Monitor and investigate
- 🟢 **0-39**: LOW - Generally safe

### Fraud Patterns & Required Actions

| Pattern | What to Do |
|---------|-----------|
| **Account Takeover** | Lock account, force password reset, ask security questions |
| **Card-Not-Present Fraud** | Issue new card, reverse charge, contact merchant |
| **Geo Anomaly** | Call customer to verify, block if confirmed fraud |
| **Velocity Attack** | Limit transaction frequency, lock account temporarily |
| **Synthetic Identity** | File SAR report, escalate to investigation |
| **TOR/Proxy Network** | Block immediately, file SAR if amount >$5k |
| **Phishing** | Try to reverse transaction, file police report |
| **Cryptocurrency** | Block transaction, extremely difficult to recover |

## Sample Test Data

If you want to test without real banking data, create a simple transaction table:

**Legitimate Transactions:**
- Grocery store, $45, home city, 10 AM
- Gas station, $50, home city, regularly
- Coffee shop, $5, home city, morning

**Suspicious Transactions:**
- Same card used in 3 different countries within 1 hour
- Cryptocurrency exchange, $3000, via Tor network
- Unusual merchant category at 3 AM
- Multiple transactions in rapid succession

These will trigger different fraud patterns!

## Troubleshooting

### PDF Not Processing
- ✅ Ensure PDF has readable text/tables (not image-based scans)
- ✅ Check file size is reasonable (<10MB typical)
- ✅ Verify file is actually a PDF (not mislabeled)

### No Transactions Extracted
- ✅ PDF structure may not match expected format
- ✅ Column names should be identifiable (Date, Amount, Merchant, etc.)
- ✅ Check backend logs for detailed error messages

### Analysis Takes a Long Time
- ⏱️ Normal: ~1-2 seconds per transaction
- ⏱️ 50 transactions = 1-2 minutes total
- ⏱️ This includes Groq LLM API calls

### Results Not Saved
- ✅ Only saved with authenticated login
- ✅ Sign in before uploading for database persistence
- ✅ Without auth, results shown but not stored

## Next Steps

1. **Test with current month's transactions**
2. **Review fraud patterns** detected in your data
3. **Implement recommended actions** for any flagged transactions
4. **Monitor high-risk merchants** for future activity
5. **Set up regular PDF analysis** as part of compliance workflow

## Advanced Usage

### Batch Processing
- Generate multiple PDFs from different date ranges
- Upload each separately to build historical baseline
- Compare patterns month-to-month

### Integration with Systems
- Export from accounting software → Convert to PDF → Upload
- Bank API → Download statement PDF → Upload to Fraud Sentinel
- Transaction logs → Format as PDF table → Upload

### Customization
- Next steps can be customized per organization
- Fraud thresholds can be adjusted (currently: 50+ = flagged)
- Risk scoring can be tuned for your specific risk profile

---

**Questions?** Check the detailed documentation in `PDF_FEATURE_DOCUMENTATION.md`
