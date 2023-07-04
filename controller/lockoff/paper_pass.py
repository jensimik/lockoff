import base64
import io

import qrcode
from weasyprint import HTML

template = """<html>
  <head>
    <meta charset="utf-8">
    <title>NKK membership card</title>
    <style>
@font-face {
    font-family: Roboto;
    src: url(Roboto-Regular.ttf);
  }
  
  html {
    font-family: Roboto, sans-serif;
  }
  
    body {
      background: #fff;
      color: #000;
      text-align: center;
    }
  
    #introduction {
      text-align: left;
    }
  
    #cardwrap {
      display: flex;
      box-sizing: border-box;
      justify-content: space-between;
      justify-content: center;
    }
  
    #card {
      position: relative;
      display: flex;
      justify-content: space-between;
      box-sizing: border-box;
      border-radius: 2mm;
      height: 53.98mm;
      margin: 0;
      width: 85.6mm;
      background: #fff;
      color: #000;
      border: 0.6mm dashed #dcdcdc;
      justify-content: center;
      align-content: center;
      align-items: center;
    }
    p {
      font-size: 5mm;
      margin: 0;
      text-align: left;
    }
  
    #spacer {
      height: 1.5cm;
    }
  
    #details {
      padding-left: 4mm;
      flex: 1 1 60%;
    }
    #logowrap {
      flex: 1 1 40%;
      padding-left: 4mm;
    }
    #nkklogo {
      width: 2.5cm;
    }
    #qrcode {
      width: 50%;
    }
  
    h1 {
      font-size: 6mm;
      margin: 0;
    }
    </style>
  </head>

  <body>
    <section id="introduction">
        <h1>Tillykke med dit NKK medlemsskab</h1>
        <p>Du kan nu printe dit medlemskort til klubben.</p>
        <p>Du skal have kortet med når du klatrer i klubben (random tjeks).</p>    
    </section>

    <div id="spacer"></div>

    <div id="cardwrap">
        <section id="card">
            <div id="logowrap">
                <svg id="nkklogo" xmlns="http://www.w3.org/2000/svg" version="1.1" width="512px" height="511px" style="shape-rendering:geometricPrecision; text-rendering:geometricPrecision; image-rendering:optimizeQuality; fill-rule:evenodd; clip-rule:evenodd" xmlns:xlink="http://www.w3.org/1999/xlink">
                  <g><path style="opacity:1" fill="#fefefe" d="M 231.5,1.5 C 147.452,12.266 82.6184,53.266 37,124.5C 17.1801,159.453 5.34675,196.786 1.5,236.5C 1.5,158.167 1.5,79.8333 1.5,1.5C 78.1667,1.5 154.833,1.5 231.5,1.5 Z"/></g>
                  <g><path style="opacity:1" fill="#2b2e31" d="M 231.5,1.5 C 247.167,1.5 262.833,1.5 278.5,1.5C 372.67,13.9824 441.504,62.3157 485,146.5C 497.333,173.709 505.167,202.043 508.5,231.5C 508.5,247.167 508.5,262.833 508.5,278.5C 495.413,376.079 444.413,445.912 355.5,488C 329.076,499.005 301.743,505.838 273.5,508.5C 261.167,508.5 248.833,508.5 236.5,508.5C 160.717,500.859 99.2166,467.193 52,407.5C 23.0978,367.366 6.26451,322.699 1.5,273.5C 1.5,261.167 1.5,248.833 1.5,236.5C 5.34675,196.786 17.1801,159.453 37,124.5C 82.6184,53.266 147.452,12.266 231.5,1.5 Z"/></g>
                  <g><path style="opacity:1" fill="#fefefe" d="M 278.5,1.5 C 355.167,1.5 431.833,1.5 508.5,1.5C 508.5,78.1667 508.5,154.833 508.5,231.5C 505.167,202.043 497.333,173.709 485,146.5C 441.504,62.3157 372.67,13.9824 278.5,1.5 Z"/></g>
                  <g><path style="opacity:1" fill="#fefefe" d="M 124.5,96.5 C 132.507,96.3336 140.507,96.5003 148.5,97C 150.081,98.828 151.415,100.828 152.5,103C 156.159,104.28 159.659,105.78 163,107.5C 161.895,131.963 157.395,155.796 149.5,179C 151.429,182.599 153.763,185.933 156.5,189C 167.209,195.927 178.876,198.927 191.5,198C 213.631,190.372 231.298,176.872 244.5,157.5C 242.883,155.368 242.383,153.035 243,150.5C 253.451,140.839 263.451,141.506 273,152.5C 274.171,154.842 275.338,157.176 276.5,159.5C 280.223,157.405 284.056,156.739 288,157.5C 295.028,167.028 301.861,176.695 308.5,186.5C 297.8,194.7 288.633,204.367 281,215.5C 273.846,230.63 268.513,246.296 265,262.5C 271.718,247.391 279.718,233.058 289,219.5C 295.133,212.034 302.466,206.034 311,201.5C 318.804,210.969 327.638,219.469 337.5,227C 340.738,231.908 344.905,235.741 350,238.5C 350.49,239.793 350.657,241.127 350.5,242.5C 351.552,242.351 352.552,242.517 353.5,243C 374.891,263.39 396.058,284.223 417,305.5C 423.203,314.246 427.536,323.913 430,334.5C 435.958,352.276 434.291,369.276 425,385.5C 422.293,389.035 418.793,390.202 414.5,389C 360.572,357.536 304.905,329.536 247.5,305C 245.5,302.92 243.5,300.92 241.5,299C 234.246,297.449 226.913,296.616 219.5,296.5C 203.371,298.327 187.204,299.661 171,300.5C 150.493,299.84 129.993,299.007 109.5,298C 100.904,296.785 93.4042,293.285 87,287.5C 84.4728,283.779 82.4728,279.779 81,275.5C 78.0658,261.967 76.7324,248.301 77,234.5C 77.5817,228.505 79.2484,222.838 82,217.5C 87.1,212.403 91.4333,206.736 95,200.5C 95.3333,198.167 95.6667,195.833 96,193.5C 99.1843,188.47 102.851,183.804 107,179.5C 109.725,172.384 112.725,165.384 116,158.5C 117.356,157.62 118.856,157.286 120.5,157.5C 118.501,144.504 116.501,131.504 114.5,118.5C 114.202,109.349 117.535,102.016 124.5,96.5 Z"/></g>
                  <g><path style="opacity:1" fill="#3b3d40" d="M 250.5,149.5 C 258.219,149.694 264.219,153.027 268.5,159.5C 267.635,160.583 266.635,160.749 265.5,160C 261.613,156.889 257.28,154.556 252.5,153C 251.177,152.184 250.511,151.017 250.5,149.5 Z"/></g>
                  <g><path style="opacity:1" fill="#fefefe" d="M 1.5,273.5 C 6.26451,322.699 23.0978,367.366 52,407.5C 99.2166,467.193 160.717,500.859 236.5,508.5C 158.167,508.5 79.8333,508.5 1.5,508.5C 1.5,430.167 1.5,351.833 1.5,273.5 Z"/></g>
                  <g><path style="opacity:1" fill="#fefefe" d="M 508.5,278.5 C 508.5,355.167 508.5,431.833 508.5,508.5C 430.167,508.5 351.833,508.5 273.5,508.5C 301.743,505.838 329.076,499.005 355.5,488C 444.413,445.912 495.413,376.079 508.5,278.5 Z"/></g>
                </svg>
            </div>
            <div id="details">
                <p id="navn">NAME</p>
                <p id="level">LEVEL</p>
            </div>
        </section>    
    </div>
    <div id="cardwrap">
        <section id="card">
            <div id="details">
                <img src="data:image/png;base64, IMGSTR" id="qrcode">
            </div>
        </section>
    </div>
  </body>
</html>
"""


def generate_pdf(pdf_file: io.BufferedIOBase, name: str, level: str, qr_code_data: str):
    # generate qr code
    qr = qrcode.QRCode(
        version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, border=0
    )
    qr.add_data(qr_code_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color=(0, 0, 0), back_color=(255, 255, 255))
    with io.BytesIO() as f:
        img.save(f, format="png")
        img_str = base64.b64encode(f.getvalue())
    # make simple template
    html = (
        template.replace("IMGSTR", img_str.decode("utf-8"))
        .replace("NAME", name)
        .replace("LEVEL", level)
    )
    # make the pdf from html
    HTML(string=html, base_url="").write_pdf(pdf_file)


if __name__ == "__main__":
    with open("test.pdf", "wb") as f:
        generate_pdf(
            pdf_file=f, name="Jens Hansen", level="Normal 2023", qr_code_data="ASDF1234"
        )
