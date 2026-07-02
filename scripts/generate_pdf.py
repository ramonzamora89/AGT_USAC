from weasyprint import HTML
import sys

try:
    print("Iniciando conversión a PDF...")
    HTML('reports/reporte_final_estatico.html').write_pdf('reports/reporte_final_estatico.pdf')
    print("Reporte PDF generado exitosamente: reports/reporte_final_estatico.pdf")
except Exception as e:
    print(f"Error al generar PDF: {e}")
    sys.exit(1)
