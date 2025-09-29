from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def exportar_asistencia_excel(datos, filename="reporte_asistencia.xlsx"):
    """
    datos: lista de diccionarios con llaves:
    ['fecha', 'ingreso', 'salida', 'estado', 'motivo']
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Asistencia"

    # Encabezados
    headers = ["Empleado", "Ingreso", "Salida", "Estado", "Motivo"]
    ws.append(headers)

    # Estilo de encabezados
    header_fill = PatternFill(start_color="000000", end_color="000000", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Bordes
    thin_border = Border(left=Side(style='thin'),
                         right=Side(style='thin'),
                         top=Side(style='thin'),
                         bottom=Side(style='thin'))

    # Colores por estado
    colores_estado = {
        "Ausente": PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid"),  # rojo claro
        "Presente": PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid"), # verde claro
        "Salida": PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid"),   # amarillo claro
    }

    # Insertar datos con estilo
    for fila, item in enumerate(datos, start=2):
        ws.cell(row=fila, column=1, value=item['fecha']).border = thin_border
        ws.cell(row=fila, column=2, value=item['ingreso']).border = thin_border
        ws.cell(row=fila, column=3, value=item['salida']).border = thin_border
        estado_cell = ws.cell(row=fila, column=4, value=item['estado'])
        estado_cell.border = thin_border
        motivo_cell = ws.cell(row=fila, column=5, value=item['motivo'])
        motivo_cell.border = thin_border

        # Pintar color según estado
        if item['estado'] in colores_estado:
            estado_cell.fill = colores_estado[item['estado']]

    # Ajustar anchos de columna
    for col in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col)].width = 18

    # Activar filtros
    ws.auto_filter.ref = ws.dimensions

    # Guardar archivo
    wb.save(filename)
    return filename
