import io
from reportlab.pdfgen import canvas

def generate_pdf_certificate(r):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(420, 560))
    c.setFillColorRGB(0, 0.41, 0.22)
    c.rect(20, 520, 380, 25, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.drawString(35, 528, "COUNTY GOVERNMENT OF NYERI - WEIGHTS & MEASURES")
    
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(30, 490, "OFFICIAL VERIFICATION CERTIFICATE")
    c.setFont("Helvetica", 10)
    
    c.drawString(30, 460, f"Certificate S/NO: {r['s_no']}")
    c.drawString(30, 440, f"Date Issued: {r['date']}")
    c.drawString(30, 420, f"Business / Trader: {r['trader']}")
    c.drawString(30, 400, f"Phone Contact: {r['phone']}")
    c.drawString(30, 380, f"Station / Location: {r['station']}")
    c.drawString(30, 360, f"Stamped Pumps: {r['pumps']}")
    c.drawString(30, 340, f"Stamped Scales: {r['scales']}")
    c.drawString(30, 320, f"Stamped Weights: {r['weights']}")
    
    c.setFont("Helvetica-Bold", 10)
    c.drawString(30, 290, f"Total Amount Paid: KES {r['fee']:,.2f}")
    c.drawString(30, 270, f"M-Pesa Reference Code: {r['code']}")
    
    c.setFillColorRGB(0.7, 0, 0)
    c.drawString(30, 240, f"Next Verification Due: {r['due']}")
    
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(30, 190, "Authorized digital stamp & record synced to county server.")
    c.drawString(30, 175, f"Logged by: {r['inspector']}")
    
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
