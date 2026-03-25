from flask import Flask, request, render_template, send_file, jsonify
from flask_cors import CORS
import pandas as pd
import io
import os
from werkzeug.utils import secure_filename
import tempfile
import plotly.graph_objs as go
import plotly.utils
import json

# Importar el módulo de limpieza
from utils.cleaner import clean_excel_data

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
app.config['SECRET_KEY'] = 'tu-clave-secreta-aqui'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/clean', methods=['POST'])
def clean_excel():
    """Endpoint para limpiar el Excel y devolver el archivo procesado"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No se subió ningún archivo'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Nombre de archivo vacío'}), 400
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Formato no soportado. Use .xlsx o .xls'}), 400
        
        # Procesar el archivo
        file_bytes = file.read()
        df_clean, stats = clean_excel_data(file_bytes)
        
        # Exportar a Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_clean.to_excel(writer, index=False, sheet_name='USD_Limpio')
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='USD_2026_limpio.xlsx'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/preview', methods=['POST'])
def preview_data():
    """Endpoint para obtener vista previa de los datos limpios"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No se subió ningún archivo'}), 400
        
        file = request.files['file']
        file_bytes = file.read()
        df_clean, stats = clean_excel_data(file_bytes)
        
        # Obtener primeras 10 filas para vista previa
        preview_data = df_clean.head(10).fillna('').to_dict('records')
        
        # Obtener estadísticas
        stats = {
            'total_registros': len(df_clean),
            'total_columnas': len(df_clean.columns),
            'columnas': list(df_clean.columns),
            'resumen': stats
        }
        
        return jsonify({
            'success': True,
            'preview': preview_data,
            'stats': stats
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export_pdf', methods=['POST'])
def export_pdf():
    """Endpoint para exportar datos limpios a PDF"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        import tempfile
        
        if 'file' not in request.files:
            return jsonify({'error': 'No se subió ningún archivo'}), 400
        
        file = request.files['file']
        file_bytes = file.read()
        df_clean, stats = clean_excel_data(file_bytes)
        
        # Crear archivo PDF temporal
        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_pdf.close()
        
        # Configurar documento
        doc = SimpleDocTemplate(temp_pdf.name, pagesize=landscape(letter))
        styles = getSampleStyleSheet()
        story = []
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=30
        )
        title = Paragraph("Reporte de Datos Limpios - USD 2026", title_style)
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Estadísticas
        stats_style = ParagraphStyle(
            'StatsStyle',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=10
        )
        story.append(Paragraph(f"Total de registros: {len(df_clean)}", stats_style))
        story.append(Paragraph(f"Total de columnas: {len(df_clean.columns)}", stats_style))
        story.append(Paragraph(f"Columnas procesadas: {', '.join(df_clean.columns[:10])}{'...' if len(df_clean.columns) > 10 else ''}", stats_style))
        story.append(Spacer(1, 20))
        
        # Tabla de datos (primeras 20 filas)
        data = [df_clean.columns.tolist()] + df_clean.head(20).fillna('').values.tolist()
        
        # Calcular anchos de columna
        col_widths = [min(1.5 * inch, max(0.5 * inch, len(str(col)) * 0.1 * inch)) for col in df_clean.columns]
        
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        
        story.append(table)
        
        # Pie de página
        story.append(Spacer(1, 20))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey
        )
        story.append(Paragraph("Reporte generado automáticamente por el sistema de limpieza de datos", footer_style))
        
        # Construir PDF
        doc.build(story)
        
        # Enviar archivo
        return send_file(
            temp_pdf.name,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='USD_2026_limpio.pdf'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    
    