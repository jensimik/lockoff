# import base64
# import io

import qrcode
from PIL import Image

# from weasyprint import HTML

# from .paper_template import template


def generate_png(qr_code_data: str) -> Image:
    # generate qr code
    qr = qrcode.QRCode(
        version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, border=0
    )
    qr.add_data(qr_code_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color=(0, 0, 0), back_color=(255, 255, 255))
    return img


# def generate_pdf(name: str, level: str, qr_code_data: str):
#     pdf_file = io.BytesIO()
#     # generate qr code
#     img = generate_png(qr_code_data=qr_code_data)
#     with io.BytesIO() as f:
#         img.save(f, format="png")
#         img_str = base64.b64encode(f.getvalue())
#     # make simple template
#     html = (
#         template.replace("IMGSTR", img_str.decode("utf-8"))
#         .replace("NAME", name)
#         .replace("LEVEL", level)
#     )
#     # make the pdf from html
#     HTML(string=html, base_url="").write_pdf(pdf_file)
#     return pdf_file


# if __name__ == "__main__":
#     token = generate_dayticket_access_token()
#     pdf_file = generate_pdf(name="Jens Hansen", level="Normal 2023", qr_code_data=token)
