"""
Generación del PDF del reporte.

Estrategia: se renderiza una plantilla HTML y se convierte a PDF con WeasyPrint.
Si WeasyPrint no está disponible (por ejemplo, faltan librerías del sistema en
Windows), se usa un respaldo con ReportLab que produce un PDF de texto.
"""
from django.template.loader import render_to_string


def render_pdf_bytes(template_name, context):
    """Devuelve los bytes del PDF generado a partir de una plantilla HTML."""
    html_string = render_to_string(template_name, context)
    try:
        from weasyprint import HTML

        return HTML(string=html_string).write_pdf()
    except Exception:
        # Respaldo con ReportLab: vuelca el texto del contexto resumido.
        return _render_pdf_reportlab(context)


def _render_pdf_reportlab(context):
    import io

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.lib import colors

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    estilos = getSampleStyleSheet()
    elementos = []

    rep = context.get("reporte")
    elementos.append(Paragraph(context.get("titulo", "Reporte de Mantenimiento"),
                               estilos["Title"]))
    elementos.append(Paragraph(context.get("planta", "Choco Pasión - Tingo María"),
                               estilos["Normal"]))
    if rep:
        elementos.append(Paragraph(
            f"Periodo: {rep.fecha_inicio} a {rep.fecha_fin} | Código: {rep.codigo_reporte}",
            estilos["Normal"],
        ))
    elementos.append(Spacer(1, 0.5 * cm))

    secciones = [
        ("Checklists realizados", context.get("checklists")),
        ("Checklists observados / no aptos", context.get("checklists_no_aptos")),
        ("Observaciones diarias", context.get("observaciones")),
        ("Reportes de falla", context.get("fallas")),
        ("Órdenes de trabajo abiertas", context.get("ot_abiertas")),
        ("Órdenes de trabajo cerradas", context.get("ot_cerradas")),
        ("Repuestos bajo stock", context.get("repuestos_bajo_stock")),
    ]
    for titulo, datos in secciones:
        elementos.append(Paragraph(titulo, estilos["Heading3"]))
        filas = [[str(x)] for x in (datos or [])][:50]
        if not filas:
            filas = [["Sin registros en el periodo."]]
        tabla = Table(filas, colWidths=[16 * cm])
        tabla.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elementos.append(tabla)
        elementos.append(Spacer(1, 0.4 * cm))

    doc.build(elementos)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
