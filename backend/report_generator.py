import json
from typing import List, Dict, Optional
from datetime import datetime
from collections import defaultdict, Counter
import logging
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)

class FraudReportGenerator:
    """Generate comprehensive fraud analysis reports from transaction analysis"""
    
    FRAUD_SEVERITY_LEVELS = {
        "critical": {"range": (85, 100), "label": "🔴 CRITICAL", "color": "#ff4757"},
        "high": {"range": (70, 84), "label": "🟠 HIGH", "color": "#ff6b35"},
        "medium": {"range": (50, 69), "label": "🟡 MEDIUM", "color": "#ffa502"},
        "low": {"range": (30, 49), "label": "🟢 LOW", "color": "#2ed573"},
        "minimal": {"range": (0, 29), "label": "🟢 MINIMAL", "color": "#1dd1a1"},
    }
    
    FRAUD_REMEDIATION_STEPS = {
        "Account Takeover": [
            "Immediately freeze or lock the account to prevent further unauthorized access",
            "Reset password and force re-authentication on all devices",
            "Review account activity logs for other unauthorized transactions",
            "Contact customer via secondary channel (phone) to confirm incidents",
            "Enable multi-factor authentication (MFA) for additional security",
            "File incident report with fraud team for investigation",
        ],
        "Card-Not-Present Fraud": [
            "Initiate chargeback process with payment processor",
            "Issue replacement card with new card number immediately",
            "Contact merchant to reverse the fraudulent transaction",
            "Place temporary restrictions on online transactions",
            "Request police report documentation if amount exceeds $1,000",
            "Monitor account for residual fraud attempts",
        ],
        "Geo Anomaly": [
            "Contact customer immediately via phone to verify transaction",
            "Block the transaction if customer confirms it's not authorized",
            "Request OTP (One-Time Password) verification for high-risk locations",
            "Implement IP geolocation verification for future transactions",
            "Flag merchant for suspicious transaction patterns",
            "Consider restricting transactions from high-risk countries",
        ],
        "Velocity Attack": [
            "Immediately flag all transactions from same source/device",
            "Implement temporary transaction velocity limits (e.g., 1 per 10 minutes)",
            "Lock account and require password reset",
            "Investigate all transactions in the sequence for fraud",
            "File report with payment card industry (PCI) compliance team",
            "Block automated transaction attempts from same IP/device",
        ],
        "Synthetic Identity Fraud": [
            "Escalate to fraud investigation unit for manual review",
            "Verify identity documents with government databases",
            "File Suspicious Activity Report (SAR) with regulatory authorities",
            "Place account on fraud watchlist (6-month+ monitoring)",
            "Contact all creditors about potential fraud",
            "Coordinate with law enforcement for follow-up investigation",
        ],
        "TOR/Proxy Network": [
            "Block transaction immediately - high fraud risk confirmed",
            "Block all future transactions originating from Tor/proxy networks",
            "Terminate account access and require in-person re-verification",
            "File Suspicious Activity Report (SAR) if transaction >$5,000",
            "Add IP address(es) to global fraud blacklist",
            "Coordinate with cyber security team for further investigation",
        ],
        "Phishing / Social Engineering": [
            "Immediately stop/reverse the fraudulent transaction if possible",
            "Contact customer to confirm if they initiated the transaction",
            "File police report and provide evidence of phishing attempt",
            "Monitor account closely for 30 days for follow-up fraud",
            "Educate customer about phishing and social engineering tactics",
            "Review security logs for unauthorized account access attempts",
        ],
        "Cryptocurrency Fraud": [
            "Attempt to reverse or block cryptocurrency transaction",
            "File report with cryptocurrency exchange for account monitoring",
            "Coordinate with financial crimes unit - crypto fraud is hard to recover",
            "File Suspicious Activity Report (SAR) if transaction >$10,000",
            "Block account pending manual fraud review",
            "Provide fraud prevention education to customer",
        ],
    }
    
    def generate_report(self, transactions: List[Dict], analyses: List[Dict]) -> Dict:
        """
        Generate comprehensive fraud report from analyzed transactions
        
        Args:
            transactions: List of original transaction dicts
            analyses: List of analysis dicts from Groq
        
        Returns:
            Comprehensive report dict
        """
        if not transactions or not analyses:
            return self._empty_report()
        
        # Aggregate statistics
        total_amount = sum(tx.get('amount', 0) for tx in transactions)
        fraud_count = sum(1 for analysis in analyses if analysis.get('risk_score', 0) >= 50)
        high_risk_count = sum(1 for analysis in analyses if analysis.get('risk_score', 0) >= 70)
        critical_count = sum(1 for analysis in analyses if analysis.get('risk_score', 0) >= 85)
        
        # Identify patterns
        fraud_patterns = Counter()
        fraud_reasons = defaultdict(list)
        risk_by_merchant = defaultdict(lambda: {"count": 0, "amount": 0, "max_risk": 0})
        risk_by_location = defaultdict(lambda: {"count": 0, "amount": 0, "max_risk": 0})
        
        for tx, analysis in zip(transactions, analyses):
            if analysis.get('risk_score', 0) >= 50:
                pattern = analysis.get('fraud_pattern', 'Unknown')
                fraud_patterns[pattern] += 1
                
                merchant = tx.get('merchant', 'Unknown')
                risk_by_merchant[merchant]["count"] += 1
                risk_by_merchant[merchant]["amount"] += tx.get('amount', 0)
                risk_by_merchant[merchant]["max_risk"] = max(
                    risk_by_merchant[merchant]["max_risk"],
                    analysis.get('risk_score', 0)
                )
                
                location = tx.get('location', 'Unknown')
                risk_by_location[location]["count"] += 1
                risk_by_location[location]["amount"] += tx.get('amount', 0)
                risk_by_location[location]["max_risk"] = max(
                    risk_by_location[location]["max_risk"],
                    analysis.get('risk_score', 0)
                )
        
        # Generate summary
        summary = self._generate_summary(
            total_amount, len(transactions), fraud_count, 
            high_risk_count, critical_count, fraud_patterns
        )
        
        # Gather next steps from all fraud patterns
        next_steps = self._generate_next_steps(fraud_patterns)
        
        # Identify top risks
        top_risky_merchants = sorted(
            risk_by_merchant.items(),
            key=lambda x: x[1]["max_risk"],
            reverse=True
        )[:5]
        
        top_risky_locations = sorted(
            risk_by_location.items(),
            key=lambda x: x[1]["max_risk"],
            reverse=True
        )[:5]
        
        return {
            "report_id": f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "generated_at": datetime.now().isoformat(),
            "summary": summary,
            "statistics": {
                "total_transactions": len(transactions),
                "total_amount": round(total_amount, 2),
                "fraud_detected_count": fraud_count,
                "high_risk_count": high_risk_count,
                "critical_count": critical_count,
                "fraud_detection_rate": f"{(fraud_count / len(transactions) * 100):.1f}%" if transactions else "0%",
            },
            "fraud_patterns": dict(fraud_patterns),
            "risky_merchants": [
                {
                    "merchant": name,
                    "fraud_count": data["count"],
                    "total_amount": round(data["amount"], 2),
                    "max_risk_score": data["max_risk"],
                }
                for name, data in top_risky_merchants
            ],
            "risky_locations": [
                {
                    "location": name,
                    "fraud_count": data["count"],
                    "total_amount": round(data["amount"], 2),
                    "max_risk_score": data["max_risk"],
                }
                for name, data in top_risky_locations
            ],
            "fraud_reasons": dict(fraud_patterns),
            "recommended_next_steps": next_steps,
            "detailed_findings": self._generate_detailed_findings(
                transactions, analyses, fraud_patterns
            ),
        }
    
    def _empty_report(self) -> Dict:
        """Generate empty report"""
        return {
            "report_id": f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "generated_at": datetime.now().isoformat(),
            "summary": "No transactions to analyze",
            "statistics": {
                "total_transactions": 0,
                "total_amount": 0,
                "fraud_detected_count": 0,
                "high_risk_count": 0,
                "critical_count": 0,
                "fraud_detection_rate": "0%",
            },
            "fraud_patterns": {},
            "fraud_reasons": {},
            "recommended_next_steps": [],
            "detailed_findings": [],
        }
    
    def _generate_summary(self, total_amount: float, tx_count: int, 
                         fraud_count: int, high_risk: int, critical: int,
                         patterns: Counter) -> str:
        """Generate executive summary"""
        fraud_rate = (fraud_count / tx_count * 100) if tx_count > 0 else 0
        
        lines = [
            f"Analyzed {tx_count} transactions totaling ${total_amount:,.2f}.",
            f"Found {fraud_count} potentially fraudulent transactions ({fraud_rate:.1f}% fraud rate).",
            f"{critical} CRITICAL risk transactions, {high_risk} HIGH risk transactions.",
        ]
        
        if patterns:
            top_pattern = patterns.most_common(1)[0][0]
            lines.append(f"Most common fraud pattern: {top_pattern}.")
        
        lines.append("Immediate action required on high and critical risk transactions.")
        
        return " ".join(lines)
    
    def _generate_next_steps(self, fraud_patterns: Counter) -> List[str]:
        """Generate prioritized next steps based on fraud patterns detected"""
        next_steps = []
        step_set = set()
        
        # Sort patterns by frequency
        for pattern, count in fraud_patterns.most_common():
            steps = self.FRAUD_REMEDIATION_STEPS.get(pattern, [])
            
            # Add top 2 steps per pattern to avoid duplication
            for step in steps[:2]:
                if step not in step_set:
                    next_steps.append(step)
                    step_set.add(step)
            
            # Stop if we have enough steps
            if len(next_steps) >= 10:
                break
        
        # Add generic fraud response steps if needed
        if len(next_steps) < 5:
            generic_steps = [
                "Monitor account closely for recurring fraud patterns over next 30 days",
                "Review customer's transaction history for additional unauthorized activity",
                "Implement enhanced authentication for high-value transactions",
                "Update fraud detection rules based on detected patterns",
                "Provide fraud awareness communication to affected customers",
            ]
            for step in generic_steps:
                if step not in step_set:
                    next_steps.append(step)
                    step_set.add(step)
        
        return next_steps[:12]  # Return top 12 recommendations
    
    def _generate_detailed_findings(self, transactions: List[Dict], 
                                   analyses: List[Dict],
                                   fraud_patterns: Counter) -> List[Dict]:
        """Generate detailed findings for each high-risk transaction"""
        findings = []
        
        for tx, analysis in zip(transactions, analyses):
            risk_score = analysis.get('risk_score', 0)
            
            # Only include medium risk and above
            if risk_score >= 50:
                finding = {
                    "transaction_id": tx.get('transaction_id'),
                    "merchant": tx.get('merchant'),
                    "amount": tx.get('amount'),
                    "location": tx.get('location'),
                    "risk_score": risk_score,
                    "confidence": analysis.get('confidence'),
                    "fraud_pattern": analysis.get('fraud_pattern'),
                    "explanation": analysis.get('explanation'),
                    "recommended_action": analysis.get('recommended_action'),
                    "severity_level": self._get_severity_label(risk_score),
                }
                findings.append(finding)
        
        # Sort by risk score descending
        findings.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return findings
    
    def _get_severity_label(self, risk_score: int) -> str:
        """Get severity label for risk score"""
        for level, config in self.FRAUD_SEVERITY_LEVELS.items():
            min_score, max_score = config['range']
            if min_score <= risk_score <= max_score:
                return config['label']
        return "Unknown"
    
    def format_report_for_display(self, report: Dict) -> Dict:
        """Format report for frontend display"""
        return {
            "reportId": report["report_id"],
            "generatedAt": report["generated_at"],
            "summary": report["summary"],
            "statistics": report["statistics"],
            "fraudPatterns": report["fraud_patterns"],
            "fraudReasons": self._format_fraud_reasons(report["fraud_patterns"]),
            "recommendedActions": report["recommended_next_steps"],
            "riskySummary": {
                "merchants": report["risky_merchants"],
                "locations": report["risky_locations"],
            },
            "detailedFindings": report["detailed_findings"],
        }
    
    def _format_fraud_reasons(self, patterns: Dict) -> List[str]:
        """Format fraud patterns as human-readable reasons"""
        reasons = []
        
        fraud_reason_templates = {
            "Account Takeover": "Unauthorized account access detected - possible credential compromise",
            "Card-Not-Present Fraud": "Online/phone transaction fraud detected - card not physically present",
            "Geo Anomaly": "Impossible geographic transaction pattern - location anomaly detected",
            "Velocity Attack": "Rapid succession of transactions - potential account testing/draining",
            "Synthetic Identity Fraud": "Transaction using fabricated identity - synthetic fraud indicators",
            "TOR/Proxy Network": "Transaction originating from anonymized network - identity concealment",
            "Phishing / Social Engineering": "Post-phishing fraud indicators - social engineering compromise",
            "Cryptocurrency Fraud": "Irreversible cryptocurrency transaction - high-risk fraud channel",
        }
        
        for pattern, count in patterns.items():
            reason = fraud_reason_templates.get(pattern, f"{pattern} detected")
            if count > 1:
                reasons.append(f"{reason} ({count} occurrences)")
            else:
                reasons.append(reason)
        
        return reasons
    
    def generate_pdf_report(self, report: Dict) -> BytesIO:
        """
        Generate a PDF version of the fraud report
        
        Args:
            report: The report dictionary from generate_report()
        
        Returns:
            BytesIO object containing the PDF data
        """
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#ff4757'),
            spaceAfter=30,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#7c3aed'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=10,
            leading=14
        )
        
        # Title
        elements.append(Paragraph("FRAUD SENTINEL REPORT", title_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Report Info
        report_id = report.get('report_id', 'N/A')
        generated_at = report.get('generated_at', 'N/A')
        elements.append(Paragraph(f"<b>Report ID:</b> {report_id}", normal_style))
        elements.append(Paragraph(f"<b>Generated:</b> {generated_at}", normal_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Executive Summary
        elements.append(Paragraph("EXECUTIVE SUMMARY", heading_style))
        summary = report.get('summary', 'No summary available')
        elements.append(Paragraph(summary, normal_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Statistics
        elements.append(Paragraph("KEY STATISTICS", heading_style))
        stats = report.get('statistics', {})
        
        stats_data = [
            ["Metric", "Value"],
            ["Total Transactions", str(stats.get('total_transactions', 0))],
            ["Total Amount", f"${stats.get('total_amount', 0):,.2f}"],
            ["Fraud Detected", str(stats.get('fraud_detected_count', 0))],
            ["Detection Rate", str(stats.get('fraud_detection_rate', '0%'))],
            ["High Risk", str(stats.get('high_risk_count', 0))],
            ["Critical", str(stats.get('critical_count', 0))],
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 2.5*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        elements.append(stats_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Fraud Patterns
        fraud_patterns = report.get('fraud_patterns', {})
        if fraud_patterns:
            elements.append(Paragraph("FRAUD PATTERNS DETECTED", heading_style))
            pattern_text = ", ".join([f"{p} ({c})" for p, c in fraud_patterns.items()])
            elements.append(Paragraph(pattern_text, normal_style))
            elements.append(Spacer(1, 0.2*inch))
        
        # Risky Merchants
        elements.append(Paragraph("RISKY MERCHANTS", heading_style))
        merchants = report.get('risky_merchants', [])
        if merchants:
            merchant_data = [["Merchant", "Fraud Count", "Max Risk", "Total Amount"]]
            for m in merchants[:5]:
                merchant_data.append([
                    m.get('merchant', 'N/A'),
                    str(m.get('fraud_count', 0)),
                    f"{m.get('max_risk_score', 0)}%",
                    f"${m.get('total_amount', 0):,.2f}"
                ])
            
            merchant_table = Table(merchant_data, colWidths=[2*inch, 1.2*inch, 1.2*inch, 1.3*inch])
            merchant_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff6b35')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ]))
            elements.append(merchant_table)
        else:
            elements.append(Paragraph("No risky merchants detected", normal_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Recommended Actions
        elements.append(PageBreak())
        elements.append(Paragraph("RECOMMENDED ACTIONS", heading_style))
        actions = report.get('recommended_next_steps', [])
        for i, action in enumerate(actions[:10], 1):
            elements.append(Paragraph(f"<b>{i}.</b> {action}", normal_style))
        
        elements.append(Spacer(1, 0.3*inch))
        
        # Detailed Findings
        elements.append(Paragraph("DETAILED FINDINGS", heading_style))
        findings = report.get('detailed_findings', [])
        
        if findings:
            for finding in findings[:10]:
                elements.append(Paragraph(
                    f"<b>Transaction:</b> {finding.get('transaction_id', 'N/A')} | "
                    f"<b>Amount:</b> ${finding.get('amount', 0):,.2f} | "
                    f"<b>Risk:</b> {finding.get('risk_score', 0)}%",
                    normal_style
                ))
                elements.append(Paragraph(
                    f"<b>Merchant:</b> {finding.get('merchant', 'N/A')} | "
                    f"<b>Location:</b> {finding.get('location', 'N/A')}",
                    normal_style
                ))
                elements.append(Paragraph(
                    f"<b>Pattern:</b> {finding.get('fraud_pattern', 'N/A')}",
                    normal_style
                ))
                elements.append(Paragraph(
                    f"<i>{finding.get('explanation', 'No explanation available')}</i>",
                    normal_style
                ))
                elements.append(Spacer(1, 0.15*inch))
        else:
            elements.append(Paragraph("No detailed findings available", normal_style))
        
        # Build PDF
        doc.build(elements)
        pdf_buffer.seek(0)
        
        return pdf_buffer
