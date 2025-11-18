#############################################################################
# Pdf Generation Libraries
#############################################################################
import reportlab
from django.contrib.staticfiles import finders
import io
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import arabic_reshaper
from bidi.algorithm import get_display
from decimal import Decimal

#############################################################################
# PDF Generation Fonts
#############################################################################
font_path = finders.find('fonts/Amiri-Regular.ttf')
pdfmetrics.registerFont(TTFont('Amiri', font_path))
font_path = finders.find('fonts/Amiri-Bold.ttf')
pdfmetrics.registerFont(TTFont('Amiri-bold', font_path))
font_path = finders.find('fonts/Amiri-Italic.ttf')
pdfmetrics.registerFont(TTFont('Amiri-italic', font_path))

#############################################################################

def process_arabic_text(text):
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text

def import_record_pdf(trans_id, record_info):
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    width, height = A4

    # Paper header
    c.setFont("Amiri-italic", 12)
    c.setFillColor(colors.darkslategray)
    c.drawString(30, height - 50, process_arabic_text("نموذج رقم م خ / 4"))

    # Date and trans_id
    c.setFont("Amiri", 14)
    c.drawRightString(570, height - 50, process_arabic_text(f"اذن استلام رقم: {record_info['trans_id']}"))
    c.drawRightString(570, height - 80, process_arabic_text(f"التاريخ: {record_info['date']}"))

    # Centered Header
    c.setFont("Amiri", 16)
    c.setFillColor(colors.black)
    c.drawCentredString(width / 2, height - 120, process_arabic_text("دولـة لـيـبـيـا"))
    c.drawCentredString(width / 2, height - 150, process_arabic_text("وزارة الاقتصاد والتجارة"))
    c.drawCentredString(width / 2, height - 180, process_arabic_text("مركز المعلومات والتوثيق الاقتصادي"))

    # Title
    c.setFont("Amiri-bold", 16)
    c.drawCentredString(width / 2, height - 220, process_arabic_text("اذن استلام اصناف بالمخزن"))

    # Company and assignment info
    c.setFont("Amiri", 14)
    c.drawRightString(550, height - 280, process_arabic_text(f"جهة التوريد: "))
    c.setFont("Amiri-bold", 14)
    c.drawRightString(488, height - 280, process_arabic_text(record_info['company']))
    c.setFont("Amiri", 14)    
    c.drawRightString(550, height - 305, process_arabic_text(f"بيان الاصناف الواردة بموجب امر تكليف رقم: {record_info['assign_id']} بتاريخ: {record_info['assign_date']}"))

    # Initialize total_price accumulator
    grand_total = Decimal('0.00')

    # Prepare table data
    table_data = [[
        process_arabic_text('ملاحظات'),
        process_arabic_text('السعر الإجمالي'),
        process_arabic_text('الوحدة'), 
        process_arabic_text('الكمية'), 
        process_arabic_text('اسم الصنف')
    ]]
    for item in record_info['items']:
        total_price = item['total_price']
        grand_total += Decimal(str(total_price))

        table_data.append([
            '',
            f"{item['total_price']:.2f}",
            process_arabic_text(item['unit']),
            str(item['quantity']),
            process_arabic_text(item['name'])
        ])
    
    cur = process_arabic_text('دينار')
    table_data.append([
        f"{cur} {grand_total:.2f}",
        '',
        process_arabic_text('الإجمالي'),
        '',
        ''
    ])

    col_widths = [80, 80, 45, 45, 250]  # Width of each column (in points)

    # Create and style the table
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Amiri'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Amiri-bold'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('SPAN', (0, len(table_data) - 1), (1, len(table_data) - 1)),
        ('SPAN', (2, len(table_data) - 1), (4, len(table_data) - 1)),
        ('ALIGN', (2, -1), (-1, -1), 'LEFT')
    ]))

    # Draw the table on the canvas
    table_width, table_height = table.wrapOn(c, width, height)
    y_position = height - 320 - table_height
    table.drawOn(c, (width - table_width) / 2, y_position)

    # Signature line
    c.setFont("Amiri", 12)
    c.drawCentredString(width / 2 - 150, y_position - 50, process_arabic_text("توقيع كاتب استاذ المخزن"))
    c.drawCentredString(width / 2 - 150, y_position - 75, process_arabic_text("......................"))
    c.drawCentredString(width / 2 + 160, y_position - 50, process_arabic_text("توقيع امين المخزن"))
    c.drawCentredString(width / 2 + 160, y_position - 75, process_arabic_text("................."))

    # Footer
    c.setFillColor(colors.darkslategray)
    c.drawRightString(width - 50, 50, process_arabic_text("(يعد وفقا للمادة 243 من اللائحة)"))

    # Save PDF to the BytesIO buffer
    c.save()
    pdf_data = pdf_buffer.getvalue()  # Get PDF data from the buffer
    pdf_buffer.close()  # Close the buffer

    return pdf_data  # Return the PDF data

def export_record_pdf(trans_id, record_info):
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    width, height = A4

    # Paper header
    c.setFont("Amiri-italic", 12)
    c.setFillColor(colors.darkslategray)
    c.drawString(30, height - 50, process_arabic_text("نموذج رقم م خ / 7"))

    # Date and trans_id
    c.setFont("Amiri", 14)
    c.drawRightString(570, height - 50, process_arabic_text(f"اذن صرف رقم: {record_info['trans_id']}"))
    c.drawRightString(570, height - 80, process_arabic_text(f"التاريخ: {record_info['date']}"))

    # Centered Header
    c.setFont("Amiri", 16)
    c.setFillColor(colors.black)
    c.drawCentredString(width / 2, height - 120, process_arabic_text("دولـة لـيـبـيـا"))
    c.drawCentredString(width / 2, height - 150, process_arabic_text("وزارة الاقتصاد والتجارة"))
    c.drawCentredString(width / 2, height - 180, process_arabic_text("مركز المعلومات والتوثيق الاقتصادي"))

    # Title
    c.setFont("Amiri-bold", 16)
    c.drawCentredString(width / 2, height - 220, process_arabic_text("اذن صرف اصناف من المخزن للاغراض المصلحية"))

    # Company and assignment info

    c.setFont("Amiri", 14)
    c.drawRightString(550, height - 305, process_arabic_text(f"بيان الاصناف المصروفة لحساب: "))
    c.setFont("Amiri-bold", 14)    
    c.drawRightString(392, height - 305, process_arabic_text(record_info['entity']))
    c.setFont("Amiri", 14)
    c.drawString(40, height - 305, process_arabic_text(f"الغرض: {record_info['export_type']}"))

    # Initialize total_price accumulator
    grand_total = Decimal('0.00')

    # Prepare table data
    table_data = [[
        process_arabic_text('ملاحظات'),
        process_arabic_text('متوسط السعر'),
        process_arabic_text('الوحدة'), 
        process_arabic_text('الكمية'), 
        process_arabic_text('اسم الصنف'),
        process_arabic_text('ر.ت'),
    ]]
    row_number = 1

    for item in record_info['items']:
        price = item['price']
        grand_total += Decimal(str(price))

        table_data.append([
            '',
            f"{item['price']:.2f}",
            process_arabic_text(item['unit']),
            str(item['quantity']),
            process_arabic_text(item['name']),
            str(row_number),  # Auto-numbering column
        ])
    row_number += 1  # Increment the row number
    cur = process_arabic_text('دينار')
    table_data.append([
        f"{cur} {grand_total:.2f}",
        '',
        process_arabic_text('الإجمالي'),
        '',
        ''
    ])

    col_widths = [70, 70, 45, 45, 250, 35]  # Width of each column (in points)

    # Create and style the table
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Amiri'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Amiri-bold'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('SPAN', (0, len(table_data) - 1), (1, len(table_data) - 1)),
        ('SPAN', (2, len(table_data) - 1), (4, len(table_data) - 1)),
        ('ALIGN', (2, -1), (-1, -1), 'LEFT')
    ]))

    # Draw the table on the canvas
    table_width, table_height = table.wrapOn(c, width, height)
    y_position = height - 320 - table_height
    table.drawOn(c, (width - table_width) / 2, y_position)

    # Signature line
    c.setFont("Amiri", 12)
    c.drawCentredString(width / 2 - 150, y_position - 50, process_arabic_text("توقيع المستلم"))
    c.drawCentredString(width / 2 - 150, y_position - 75, process_arabic_text("................."))
    c.drawCentredString(width / 2 , y_position - 100, process_arabic_text("توقيع كاتب استاذ المخزن"))
    c.drawCentredString(width / 2 , y_position - 125, process_arabic_text("......................"))
    c.drawCentredString(width / 2 + 160, y_position - 50, process_arabic_text("توقيع امين المخزن"))
    c.drawCentredString(width / 2 + 160, y_position - 75, process_arabic_text("................."))
    # Footer
    c.setFillColor(colors.darkslategray)
    c.drawRightString(width - 50, 50, process_arabic_text("(يعد وفقا للمادة 263 من اللائحة)"))

    # Save PDF to the BytesIO buffer
    c.save()
    pdf_data = pdf_buffer.getvalue()  # Get PDF data from the buffer
    pdf_buffer.close()  # Close the buffer

    return pdf_data  # Return the PDF data


def inventory_pdf(report_data):
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    width, height = A4

    # Paper header
    c.setFont("Amiri-italic", 12)
    c.setFillColor(colors.darkslategray)
    c.drawString(30, height - 50, process_arabic_text("نموذج رقم م خ / 9"))

    # Centered Header
    c.setFont("Amiri", 16)
    c.setFillColor(colors.black)
    c.drawCentredString(width / 2, height - 120, process_arabic_text("دولـة لـيـبـيـا"))
    c.drawCentredString(width / 2, height - 150, process_arabic_text("وزارة الاقتصاد والتجارة"))
    c.drawCentredString(width / 2, height - 180, process_arabic_text("مركز المعلومات والتوثيق الاقتصادي"))

    # Title
    c.setFont("Amiri-bold", 16)
    c.drawCentredString(width / 2, height - 220, process_arabic_text(f"نموذج الجرد العام لسنة: {report_data['year']}"))


    # Prepare table data
    table_data = [
        [
        process_arabic_text('ملاحظات'),
        process_arabic_text(''),
        process_arabic_text('الفرق'),
        process_arabic_text('المدون بالسجل'),
        process_arabic_text(''),
        process_arabic_text('التوقيعات'),
        process_arabic_text('الوحدة'), 
        process_arabic_text('الكمية بالمخزن'), 
        process_arabic_text('اسم الصنف'),
        process_arabic_text('ر.ت'),
    ],
    [
        process_arabic_text(''),
        process_arabic_text('نقصان'),
        process_arabic_text('زياده'),
        process_arabic_text(''),
        process_arabic_text('المراجع'),
        process_arabic_text('العداد'),
        process_arabic_text(''), 
        process_arabic_text(''), 
        process_arabic_text(''),
        process_arabic_text(''),
    ],
    
    ]

    row_number = 1

    for item in report_data['items']:
        table_data.append([
            '',
            f"{item['stock']:.2f}",
            process_arabic_text(item['unit']),
            str(item['net_quantity']),
            process_arabic_text(item['name']),
            str(row_number),  # Auto-numbering column
        ])
    row_number += 1  # Increment the row number

    col_widths = [70, 70, 45, 45, 250, 35]  # Width of each column (in points)

    # Create and style the table
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Amiri'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Amiri-bold'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('SPAN', (0, len(table_data) - 1), (1, len(table_data) - 1)),
        ('SPAN', (2, len(table_data) - 1), (4, len(table_data) - 1)),
        ('ALIGN', (2, -1), (-1, -1), 'LEFT')
    ]))

    # Draw the table on the canvas
    table_width, table_height = table.wrapOn(c, width, height)
    y_position = height - 320 - table_height
    table.drawOn(c, (width - table_width) / 2, y_position)

    # Signature line
    c.setFont("Amiri", 12)
    c.drawCentredString(width / 2 - 150, y_position - 50, process_arabic_text("توقيع المستلم"))
    c.drawCentredString(width / 2 - 150, y_position - 75, process_arabic_text("................."))
    c.drawCentredString(width / 2 , y_position - 100, process_arabic_text("توقيع كاتب استاذ المخزن"))
    c.drawCentredString(width / 2 , y_position - 125, process_arabic_text("......................"))
    c.drawCentredString(width / 2 + 160, y_position - 50, process_arabic_text("توقيع امين المخزن"))
    c.drawCentredString(width / 2 + 160, y_position - 75, process_arabic_text("................."))
    # Footer
    c.setFillColor(colors.darkslategray)
    c.drawRightString(width - 50, 50, process_arabic_text("(يعد وفقا للمادة 263 من اللائحة)"))

    # Save PDF to the BytesIO buffer
    c.save()
    pdf_data = pdf_buffer.getvalue()  # Get PDF data from the buffer
    pdf_buffer.close()  # Close the buffer

    return pdf_data  # Return the PDF data