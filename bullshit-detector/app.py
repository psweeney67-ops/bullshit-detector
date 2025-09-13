from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
import tempfile
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

app = FastAPI()

def generate_quadrant_pdf(data, filepath):
    doc = SimpleDocTemplate(filepath, pagesize=landscape(A4))
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Header", fontSize=22, textColor=colors.HexColor("#b30000"), alignment=1, spaceAfter=20))
    styles.add(ParagraphStyle(name="BucketText", fontSize=11, leading=14, spaceAfter=6))

    header = Paragraph("Sense Labs Bullshit Detector™<br/><i>Parody Edition</i>", styles["Header"])

    quadrants = data["quadrants"]

    quad_cells = []
    for q in quadrants:
        bucket_title = Paragraph(q["title"], ParagraphStyle(
            name="BT", fontSize=16, textColor=colors.white, alignment=1, backColor=q["color"], spaceAfter=8, leading=18, alignment=1
        ))
        bullets = [Paragraph("• " + item, styles["BucketText"]) for item in q["items"]]
        quad_cells.append([bucket_title] + bullets)

    table_data = [[quad_cells[0], quad_cells[1]], [quad_cells[2], quad_cells[3]]]
    quad_table = Table(table_data, colWidths=[360, 360], rowHeights=[220, 220])
    quad_table.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('BOX',(0,0),(-1,-1),2,colors.black),
        ('INNERGRID',(0,0),(-1,-1),1,colors.black)
    ]))

    footer = Paragraph("<b>BS Thermometer: 18 / 100</b><br/><i>When thought leadership meets thought laundering.</i>",
                       ParagraphStyle(name="Footer", fontSize=12, alignment=1, textColor=colors.HexColor("#b30000"), spaceBefore=20))

    doc.build([header, quad_table, Spacer(1, 20), footer])
    return filepath

@app.post("/render")
async def render(request: Request):
    data = await request.json()
    tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf_path = generate_quadrant_pdf(data, tmpfile.name)
    return FileResponse(pdf_path, media_type="application/pdf", filename="BS_Detector.pdf")
