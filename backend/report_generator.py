import os
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.units import cm
from database import init_db, get_session, Alert

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

DARK   = HexColor("#0d1420")
BLUE   = HexColor("#0ea5e9")
RED    = HexColor("#ef4444")
PURPLE = HexColor("#a855f7")
YELLOW = HexColor("#f59e0b")
GRAY   = HexColor("#64748b")
LIGHT  = HexColor("#e2e8f0")

SEV_COLOURS = {
    "Critical": PURPLE,
    "High":     RED,
    "Medium":   YELLOW,
    "Low":      BLUE,
}

def generate_report(hours: int = 24) -> str:
    """Generate a PDF incident report for the last N hours."""
    init_db()
    session  = get_session()
    since    = datetime.utcnow() - timedelta(hours=hours)
    alerts   = (session.query(Alert)
                       .filter(Alert.timestamp >= since)
                       .order_by(Alert.timestamp.desc())
                       .all())
    session.close()

    now      = datetime.now()
    filename = f"XEDR_Report_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(REPORTS_DIR, filename)

    doc    = SimpleDocTemplate(filepath, pagesize=A4,
                               leftMargin=2*cm, rightMargin=2*cm,
                               topMargin=2*cm,  bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story  = []

    # ── Title ──
    title_style = ParagraphStyle("title",
        fontSize=22, fontName="Helvetica-Bold",
        textColor=BLUE, spaceAfter=4)
    sub_style = ParagraphStyle("sub",
        fontSize=10, fontName="Helvetica",
        textColor=GRAY, spaceAfter=16)

    story.append(Paragraph("XEDR — Incident Report", title_style))
    story.append(Paragraph(
        f"Generated: {now.strftime('%B %d, %Y at %H:%M:%S')} · "
        f"Period: Last {hours} hours", sub_style))
    story.append(HRFlowable(width="100%", thickness=1,
                             color=BLUE, spaceAfter=16))

    # ── Summary stats ──
    total    = len(alerts)
    critical = sum(1 for a in alerts if a.severity == "Critical")
    high     = sum(1 for a in alerts if a.severity == "High")
    medium   = sum(1 for a in alerts if a.severity == "Medium")
    low      = sum(1 for a in alerts if a.severity == "Low")

    section_style = ParagraphStyle("section",
        fontSize=13, fontName="Helvetica-Bold",
        textColor=LIGHT, spaceBefore=12, spaceAfter=8)
    body_style = ParagraphStyle("body",
        fontSize=10, fontName="Helvetica",
        textColor=GRAY, spaceAfter=6, leading=16)

    story.append(Paragraph("Executive Summary", section_style))

    summary_data = [
        ["Metric",          "Count"],
        ["Total Alerts",    str(total)],
        ["Critical",        str(critical)],
        ["High",            str(high)],
        ["Medium",          str(medium)],
        ["Low",             str(low)],
    ]
    summary_table = Table(summary_data, colWidths=[10*cm, 6*cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0),  DARK),
        ("TEXTCOLOR",   (0,0), (-1,0),  BLUE),
        ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 10),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [HexColor("#0a1018"), HexColor("#0d1420")]),
        ("TEXTCOLOR",   (0,1), (-1,-1), LIGHT),
        ("GRID",        (0,0), (-1,-1), 0.5, HexColor("#1e293b")),
        ("TOPPADDING",  (0,0), (-1,-1), 7),
        ("BOTTOMPADDING",(0,0),(-1,-1), 7),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 16))

    if not alerts:
        story.append(Paragraph(
            "No alerts were recorded during this period. System appears normal.",
            body_style))
    else:
        story.append(Paragraph("Alert Details", section_style))

        for i, alert in enumerate(alerts[:30]):   # cap at 30 for readability
            sev_colour = SEV_COLOURS.get(alert.severity, BLUE)

            alert_data = [
                [f"#{alert.id}  {alert.alert_type}", f"{alert.severity}  ·  Risk {alert.risk_score}/100"],
            ]
            alert_table = Table(alert_data, colWidths=[11*cm, 5*cm])
            alert_table.setStyle(TableStyle([
                ("BACKGROUND",  (0,0), (-1,-1), HexColor("#0d1420")),
                ("TEXTCOLOR",   (0,0), (0,0),   LIGHT),
                ("TEXTCOLOR",   (1,0), (1,0),   sev_colour),
                ("FONTNAME",    (0,0), (-1,-1), "Helvetica-Bold"),
                ("FONTSIZE",    (0,0), (-1,-1), 10),
                ("TOPPADDING",  (0,0), (-1,-1), 8),
                ("BOTTOMPADDING",(0,0),(-1,-1), 8),
                ("LEFTPADDING", (0,0), (-1,-1), 10),
                ("LINEBELOW",   (0,0), (-1,-1), 0.5, sev_colour),
            ]))
            story.append(alert_table)

            detail_style = ParagraphStyle(f"detail_{i}",
                fontSize=9, fontName="Helvetica",
                textColor=GRAY, spaceAfter=2, leading=14,
                leftIndent=10)
            story.append(Paragraph(f"Process: {alert.process}", detail_style))
            story.append(Paragraph(
                f"Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                detail_style))
            story.append(Paragraph(f"Description: {alert.description}", detail_style))

            if alert.explained:
                ai_style = ParagraphStyle(f"ai_{i}",
                    fontSize=9, fontName="Helvetica",
                    textColor=HexColor("#94a3b8"),
                    spaceAfter=12, leading=14, leftIndent=10)
                story.append(Paragraph(f"AI Analysis: {alert.explained}", ai_style))
            else:
                story.append(Spacer(1, 10))

    # ── Footer ──
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY))
    footer_style = ParagraphStyle("footer",
        fontSize=8, fontName="Helvetica",
        textColor=GRAY, spaceAfter=0, alignment=1)
    story.append(Paragraph(
        "XEDR — AI-Powered Endpoint Security Assistant · "
        "Confidential Security Report", footer_style))

    doc.build(story)
    print(f"[REPORT] Generated: {filepath}")
    return filepath


if __name__ == "__main__":
    path = generate_report(hours=24)
    print(f"Report saved to: {path}")