from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field, ValidationError, validator
from typing import List
import os, tempfile
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

app = FastAPI()

# ---------- Models & Helpers ----------
class Quadrant(BaseModel):
    title: str
    color: str = Field(..., description="Hex color like #d73027")
    items: List[str]

    @validator("color")
    def color_to_hex(cls, v):
        # Normalize to #RRGGBB
        c = v.strip()
        if not c.startswith("#"):
            c = "#" + c
        if len(c) == 4:  # e.g. #abc -> #aabbcc
            c = "#" + "".join([ch * 2 for ch in c[1:]])
        # Fallback to a default if parse fails
        try:
            _ = colors.HexColor(c)
            return c
        except Exception:
            return "#333333"

class Payload(BaseModel):
    quadrants: List[Quadrant]

    @validator("quadrants")
    def must_have_four(cls, v):
        if not v or len(v) != 4:
            raise ValueError("Expected exactly 4 quadrants.")
        return v

def generate_quadrant_pdf(data: Payload, filepath: str):
    doc = SimpleDocTemplate(filepath, pagesize=landscape(A4),
                            rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)

    styles = getSampleStyleSheet()
    if "Header" not in styles:
        pass
    styles.add(ParagraphStyle(name="Header", fontSize=22, textColor=colors.HexColor("#b30000"), alignment=1, spaceAfter=20))
    styles.add(ParagraphStyle(name="BucketText", fontSize=11, leading=14, spaceAfter=6))

    header = Paragraph("Sense Labs Bullshit Detector™<br/><i>Parody Edition</i>", styles["Header"])

    quad_cells = []
    for q in data.quadrants:
        bucket_title = Paragraph(
            q.title,
            ParagraphStyle(
                name="BT",
                fontSize=16,
                textColor=colors.white,
                backColor=colors.HexColor(q.color),
                spaceAfter=8,
                leading=18,
                alignment=1,
            ),
        )
        bullets = [Paragraph("• " + item, styles["BucketText"]) for item in (q.items or [])]
        quad_cells.append([bucket_title] + bullets)

    table_data = [[quad_cells[0], quad_cells[1]],
                  [quad_cells[2], quad_cells[3]]]

    quad_table = Table(table_data, colWidths=[360, 360], rowHeights=[220, 220])
    quad_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 2, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 1, colors.black),
    ]))

    footer = Paragraph(
        "<b>BS Thermometer: 18 / 100</b><br/><i>When thought leadership meets thought laundering.</i>",
        ParagraphStyle(name="Footer", fontSize=12, alignment=1, textColor=colors.HexColor("#b30000"), spaceBefore=20),
    )

    doc.build([header, quad_table, Spacer(1, 20), footer])
    return filepath

# ---------- Routes ----------
@app.get("/", response_class=PlainTextResponse)
def health():
    return "OK"

@app.post("/render")
async def render(request: Request):
    try:
        payload_json = await request.json()
        data = Payload(**payload_json)
    except ValidationError as ve:
        return JSONResponse(status_code=400, content={"error": "Bad Request", "details": ve.errors()})
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": "Bad Request", "details": str(e)})

    try:
        tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf_path = generate_quadrant_pdf(data, tmpfile.name)
        return FileResponse(pdf_path, media_type="application/pdf", filename="BS_Detector.pdf")
    except Exception as e:
        # Return stack-friendly message to client to avoid opaque 500s
        return JSONResponse(status_code=500, content={"error": "Internal Server Error", "details": str(e)})
