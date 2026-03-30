from flask import Flask, request, render_template, send_file, jsonify, session, redirect, url_for
from flask_cors import CORS
import pandas as pd
import io
import os
from werkzeug.utils import secure_filename
import tempfile
import plotly.graph_objs as go
import plotly.utils
import json
from functools import wraps

# Importar el módulo de limpieza unificado
from utils.cleaner import clean_excel_data, detect_file_type

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
app.config['SECRET_KEY'] = 'tu-clave-secreta-aqui-cambiala-en-produccion'

# Credenciales (en producción, usa base de datos)
USUARIO_VALIDO = "finanza_tisur"
CONTRASENA_VALIDA = "123456"

# Decorador para requerir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de inicio de sesión"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == USUARIO_VALIDO and password == CONTRASENA_VALIDA:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Usuario o contraseña incorrectos")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Cerrar sesión"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/clean', methods=['POST'])
@login_required
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
        
        # Obtener tipo de archivo del formulario (enviado desde el frontend)
        file_type = request.form.get('file_type', None)
        
        # Si no se especifica, auto-detectar
        if file_type is None or file_type == '':
            file_type = detect_file_type(file_bytes)
        
        # Limpiar según tipo
        df_clean, stats = clean_excel_data(file_bytes, file_type)
        
        # Exportar a Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_clean.to_excel(writer, index=False, sheet_name=f'{file_type.upper()}_Limpio')
        
        output.seek(0)
        
        # Nombre de archivo según tipo
        filename = f"{file_type.upper()}_2026_limpio.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/preview', methods=['POST'])
@login_required
def preview_data():
    """Endpoint para obtener vista previa de los datos limpios"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No se subió ningún archivo'}), 400
        
        file = request.files['file']
        file_bytes = file.read()
        
        # Obtener tipo de archivo del formulario (enviado desde el frontend)
        file_type = request.form.get('file_type', None)
        
        # Si no se especifica, auto-detectar
        if file_type is None or file_type == '':
            file_type = detect_file_type(file_bytes)
        
        # Limpiar según tipo
        df_clean, stats = clean_excel_data(file_bytes, file_type)
        
        # Obtener primeras 10 filas para vista previa
        preview_data = df_clean.head(10).fillna('').to_dict('records')
        
        # Obtener estadísticas
        stats_dict = {
            'total_registros': len(df_clean),
            'total_columnas': len(df_clean.columns),
            'columnas': list(df_clean.columns),
            'tipo_archivo': file_type.upper(),
            'modificaciones': stats.get('modificaciones', []),
            'registros_iniciales': stats.get('registros_iniciales', len(df_clean)),
            'registros_finales': len(df_clean),
            'columnas_iniciales': stats.get('columnas_iniciales', len(df_clean.columns)),
            'columnas_finales': len(df_clean.columns)
        }
        
        return jsonify({
            'success': True,
            'preview': preview_data,
            'stats': stats_dict
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export_pdf', methods=['POST'])
@login_required
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
        
        # Obtener tipo de archivo del formulario (enviado desde el frontend)
        file_type = request.form.get('file_type', None)
        
        # Si no se especifica, auto-detectar
        if file_type is None or file_type == '':
            file_type = detect_file_type(file_bytes)
        
        # Limpiar según tipo
        df_clean, stats = clean_excel_data(file_bytes, file_type)
        
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
            textColor=colors.HexColor('#1E4A47'),
            spaceAfter=30
        )
        title = Paragraph(f"Reporte de Datos Limpios - {file_type.upper()} 2026", title_style)
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Estadísticas
        stats_style = ParagraphStyle(
            'StatsStyle',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=10
        )
        story.append(Paragraph(f"Tipo de archivo: {file_type.upper()}", stats_style))
        story.append(Paragraph(f"Total de registros: {len(df_clean)}", stats_style))
        story.append(Paragraph(f"Total de columnas: {len(df_clean.columns)}", stats_style))
        story.append(Spacer(1, 20))
        
        # Tabla de datos (primeras 20 filas)
        data = [df_clean.columns.tolist()] + df_clean.head(20).fillna('').values.tolist()
        
        # Calcular anchos de columna
        col_widths = [min(1.5 * inch, max(0.5 * inch, len(str(col)) * 0.1 * inch)) for col in df_clean.columns]
        
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E4A47')),
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
            download_name=f'{file_type.upper()}_2026_limpio.pdf'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/export_csv', methods=['POST'])
@login_required
def export_csv():
    """Endpoint para exportar datos limpios a CSV"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No se subió ningún archivo'}), 400
        
        file = request.files['file']
        file_bytes = file.read()
        
        # Obtener tipo de archivo del formulario (enviado desde el frontend)
        file_type = request.form.get('file_type', None)
        
        # Si no se especifica, auto-detectar
        if file_type is None or file_type == '':
            file_type = detect_file_type(file_bytes)
        
        # Limpiar según tipo
        df_clean, stats = clean_excel_data(file_bytes, file_type)
        
        # Exportar a CSV
        output = io.StringIO()
        df_clean.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'{file_type.upper()}_2026_limpio.csv'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    
    