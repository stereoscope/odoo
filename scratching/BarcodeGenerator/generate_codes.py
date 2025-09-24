import barcode
from barcode.writer import ImageWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import ImageReader
import os

class BarcodeGenerator:


    def genreate(self, productTemplates):
        products = []

        for product in productTemplates:
            ean = product.barcode
            sku = product.default_code

            if not self.is_valid_ean13(ean):
                print(f"SKU {sku} Invalid barcode: {ean}")
            else:
                products.append(product)

        self.create_pdf(products)

    # Function to generate barcode image
    def generate_barcode(self, ean_code):
        ean = barcode.get('ean13', ean_code, writer=ImageWriter())
        filename = f'barcodes/{ean_code}'
        file = ean.save(filename)
        return file


    # Function to create PDF with 5x10 matrix of barcodes
    def create_pdf(self, products, filename='barcodes.pdf'):
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        rows = 8
        cols = 5
        bwidth = 4
        bhight = 2
        max_label_length = 20
        barcode_width = width / cols
        barcode_height = height / rows

        for i, product in enumerate(products):
            barcode = product.barcode
            sku = product.default_code
            name = product.name

            if i > 0 and i % (rows * cols) == 0:
                c.showPage()  # Create a new page
            row = (i % (rows * cols)) // cols
            col = (i % (rows * cols)) % cols

            x = col * barcode_width + (barcode_width - bwidth * cm) / 2
            y = height - (row + 1) * barcode_height + (barcode_height - bhight * cm) / 2

            barcode_file = self.generate_barcode(barcode)
            c.drawImage(ImageReader(barcode_file), x, y, bwidth * cm, bhight * cm)
            #os.remove(barcode_file)
            c.setFont("Helvetica", 9)
            c.drawCentredString(x + 2 * cm, y - .2 * cm, f"{sku}")
            c.drawCentredString(x + 2 * cm, y - .8 * cm, f"{name}"[:max_label_length])

        c.save()
        print("Created pdf")

    def is_valid_ean13(self, code):
        if not code or not code.isdigit() or len(code) != 13:
            return False

        def calculate_check_digit(ean):
            sum_even = sum(int(ean[i]) for i in range(0, 12, 2))
            sum_odd = sum(int(ean[i]) for i in range(1, 12, 2))
            total_sum = sum_even + sum_odd * 3
            return (10 - (total_sum % 10)) % 10

        check_digit = calculate_check_digit(code)
        return check_digit == int(code[-1])
