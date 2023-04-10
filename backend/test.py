import random
from reportlab.graphics.barcode import code128
from reportlab.graphics.shapes import Drawing
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.graphics import renderPDF
from reportlab.graphics import shapes


if __name__ == "__main__":
    numbers = [random.randint(100000, 999999) for x in range(5)]
    c = canvas.Canvas("barcodes.pdf", pagesize=A4)

    for i, num in enumerate(numbers):
        barcode128 = code128.Code128(num, barWidth=0.4 * mm)
        x = 10 * mm
        y = (30 + (i * 50)) * mm
        barcode128.drawOn(c, x=x, y=y)
        c.drawString(18 * mm, y + (40 * mm), "NKK dayticket")
        c.drawString(10 * mm, y + (30 * mm), "climbing at your own risk")
        c.drawString(15 * mm, y + (20 * mm), "valid for one entry")
    c.save()
