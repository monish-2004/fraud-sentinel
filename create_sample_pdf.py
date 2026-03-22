from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime

# Create PDF
pdf_path = r"C:\Users\monish\Downloads\fraud-sentinel\fraud-sentinel\sample_transactions.pdf"
doc = SimpleDocTemplate(pdf_path, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)

# Build story
story = []
styles = getSampleStyleSheet()

# Title
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=16,
    textColor=colors.HexColor('#1a1a1a'),
    spaceAfter=12,
    alignment=1
)
title = Paragraph("Transaction Report - Q1 2026", title_style)
story.append(title)

subtitle_style = ParagraphStyle(
    'SubtitleCustom',
    parent=styles['Normal'],
    fontSize=10,
    textColor=colors.HexColor('#666666'),
    alignment=1,
    spaceAfter=20
)
subtitle = Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", subtitle_style)
story.append(subtitle)

# Transaction data
transactions = [
    ["Date", "Time", "Merchant", "Category", "Amount", "Location", "Device", "IP Address"],
    ["2026-03-10", "14:32", "Amazon Inc", "Shopping", "$1,245.99", "San Francisco, CA", "Desktop", "192.168.1.105"],
    ["2026-03-10", "16:45", "Starbucks Coffee", "Food & Beverage", "$8.50", "New York, NY", "Mobile", "10.0.0.42"],
    ["2026-03-11", "09:15", "Chase Bank", "Bank Transfer", "$5,000.00", "Los Angeles, CA", "Web Browser", "203.0.113.89"],
    ["2026-03-11", "22:33", "Shell Gas Station", "Gas", "$62.45", "Las Vegas, NV", "Mobile", "198.51.100.23"],
    ["2026-03-12", "03:22", "Late Night Store", "Shopping", "$234.56", "Tokyo, Japan", "Mobile", "203.0.113.198"],
    ["2026-03-12", "10:05", "United Airlines", "Travel", "$1,899.00", "Miami, FL", "Desktop", "192.0.2.156"],
    ["2026-03-12", "19:45", "Unknown Merchant XYZ", "Unknown", "$199.99", "Moscow, Russia", "Mobile", "198.51.100.89"],
    ["2026-03-13", "06:12", "Walmart Store", "Shopping", "$87.34", "Chicago, IL", "Mobile", "192.168.1.50"],
    ["2026-03-13", "13:20", "PayPal Transfer", "Finance", "$500.00", "Seattle, WA", "Web Browser", "198.51.100.45"],
    ["2026-03-14", "02:15", "Crypto Exchange Platform", "Cryptocurrency", "$3,500.00", "Singapore", "Mobile", "203.0.113.67"],
    ["2026-03-14", "11:40", "Target Retail", "Shopping", "$156.78", "Boston, MA", "Mobile", "192.168.1.99"],
    ["2026-03-14", "18:50", "Netflix Subscription", "Entertainment", "$15.99", "Denver, CO", "Web Browser", "198.51.100.12"],
    ["2026-03-15", "05:30", "International Wire", "Bank Transfer", "$10,000.00", "Dubai, UAE", "Desktop", "203.0.113.44"],
    ["2026-03-15", "14:22", "Best Buy Electronics", "Shopping", "$2,499.99", "Portland, OR", "Mobile", "192.0.2.89"],
]

# Create table
table_data = transactions
table = Table(table_data, colWidths=[1.0*inch, 0.8*inch, 1.5*inch, 1.2*inch, 0.9*inch, 1.2*inch, 1.0*inch, 1.2*inch])

# Style table
table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 9),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
    ('TOPPADDING', (0, 0), (-1, 0), 6),
    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
    ('FONTSIZE', (0, 1), (-1, -1), 8),
    ('LEFTPADDING', (0, 0), (-1, -1), 4),
    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ('TOPPADDING', (0, 1), (-1, -1), 4),
    ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
]))

story.append(table)

# Build PDF
doc.build(story)
print(f"✅ PDF created successfully!")
print(f"📄 Location: {pdf_path}")
print(f"\n📊 Contains 14 sample transactions with fraud indicators:")
print("   • Unusual locations (Tokyo, Moscow, Dubai, Singapore)")
print("   • Early morning transactions (3:22 AM, 2:15 AM, 5:30 AM)")
print("   • High-value bank transfers ($5,000, $10,000)")
print("   • Cryptocurrency transaction ($3,500)")
print("   • Online shopping and travel")
print("   • Multiple geographic anomalies for fraud detection testing")
