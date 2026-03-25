// Elementos del DOM
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const clearFile = document.getElementById('clearFile');
const previewBtn = document.getElementById('previewBtn');
const cleanBtn = document.getElementById('cleanBtn');
const exportPdfBtn = document.getElementById('exportPdfBtn');
const loading = document.getElementById('loading');
const statsCard = document.getElementById('statsCard');
const previewCard = document.getElementById('previewCard');
const result = document.getElementById('result');

let selectedFile = null;

// Eventos de drag and drop
uploadArea.addEventListener('click', () => fileInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file && (file.name.endsWith('.xlsx') || file.name.endsWith('.xls'))) {
        handleFile(file);
    } else {
        showMessage('Por favor sube un archivo Excel válido (.xlsx o .xls)', 'error');
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files[0]) {
        handleFile(e.target.files[0]);
    }
});

function handleFile(file) {
    selectedFile = file;
    fileName.textContent = file.name;
    fileInfo.style.display = 'block';
    uploadArea.style.display = 'none';
    previewBtn.disabled = false;
    cleanBtn.disabled = false;
    exportPdfBtn.disabled = false;
    result.innerHTML = '';
    statsCard.style.display = 'none';
    previewCard.style.display = 'none';
}

clearFile.addEventListener('click', () => {
    selectedFile = null;
    fileInfo.style.display = 'none';
    uploadArea.style.display = 'block';
    previewBtn.disabled = true;
    cleanBtn.disabled = true;
    exportPdfBtn.disabled = true;
    fileInput.value = '';
    result.innerHTML = '';
    statsCard.style.display = 'none';
    previewCard.style.display = 'none';
});

// Vista previa
previewBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    
    previewBtn.disabled = true;
    loading.style.display = 'block';
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    try {
        const response = await fetch('/preview', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Error al obtener vista previa');
        }
        
        // Mostrar estadísticas
        displayStats(data.stats);
        
        // Mostrar vista previa
        displayPreview(data.preview);
        
        showMessage('✅ Vista previa generada correctamente', 'success');
        
    } catch (error) {
        showMessage(`❌ Error: ${error.message}`, 'error');
    } finally {
        previewBtn.disabled = false;
        loading.style.display = 'none';
    }
});

// Limpiar y descargar Excel
cleanBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    
    cleanBtn.disabled = true;
    previewBtn.disabled = true;
    exportPdfBtn.disabled = true;
    loading.style.display = 'block';
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    try {
        const response = await fetch('/clean', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Error al procesar');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'USD_2026_limpio.xlsx';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showMessage('✅ Archivo procesado correctamente. ¡Descarga iniciada!', 'success');
        
    } catch (error) {
        showMessage(`❌ Error: ${error.message}`, 'error');
    } finally {
        cleanBtn.disabled = false;
        previewBtn.disabled = false;
        exportPdfBtn.disabled = false;
        loading.style.display = 'none';
    }
});

// Exportar PDF
exportPdfBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    
    exportPdfBtn.disabled = true;
    loading.style.display = 'block';
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    try {
        const response = await fetch('/export_pdf', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Error al generar PDF');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'USD_2026_limpio.pdf';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showMessage('✅ PDF generado correctamente. ¡Descarga iniciada!', 'success');
        
    } catch (error) {
        showMessage(`❌ Error: ${error.message}`, 'error');
    } finally {
        exportPdfBtn.disabled = false;
        loading.style.display = 'none';
    }
});

function displayStats(stats) {
    const statsContent = document.getElementById('statsContent');
    
    let html = `
        <div class="stats-grid">
            <div class="stat-card">
                <h3>${stats.total_registros}</h3>
                <p>Total Registros</p>
            </div>
            <div class="stat-card">
                <h3>${stats.total_columnas}</h3>
                <p>Total Columnas</p>
            </div>
            <div class="stat-card">
                <h3>${stats.registros_iniciales || stats.total_registros}</h3>
                <p>Registros Iniciales</p>
            </div>
        </div>
        <h6><i class="fas fa-list"></i> Modificaciones Aplicadas:</h6>
        <ul class="modifications-list">
    `;
    
    if (stats.modificaciones) {
        stats.modificaciones.forEach(mod => {
            html += `<li>${mod}</li>`;
        });
    } else if (stats.resumen && stats.resumen.modificaciones) {
        stats.resumen.modificaciones.forEach(mod => {
            html += `<li>${mod}</li>`;
        });
    }
    
    html += `</ul>`;
    html += `<hr><small class="text-muted">Columnas procesadas: ${stats.columnas ? stats.columnas.slice(0, 15).join(', ') : '...'}</small>`;
    
    statsContent.innerHTML = html;
    statsCard.style.display = 'block';
}

function displayPreview(data) {
    const previewContent = document.getElementById('previewContent');
    
    if (!data || data.length === 0) {
        previewContent.innerHTML = '<p class="text-muted">No hay datos para mostrar</p>';
        previewCard.style.display = 'block';
        return;
    }
    
    const columns = Object.keys(data[0]);
    
    let html = '<table class="preview-table">';
    html += '<thead><tr>';
    columns.forEach(col => {
        html += `<th>${col}</th>`;
    });
    html += '</tr></thead><tbody>';
    
    data.forEach(row => {
        html += '<tr>';
        columns.forEach(col => {
            html += `<td>${row[col] || ''}</td>`;
        });
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    html += `<p class="text-muted mt-2"><small>Mostrando primeras ${data.length} filas de ${data.length}+ registros</small></p>`;
    
    previewContent.innerHTML = html;
    previewCard.style.display = 'block';
}

function showMessage(msg, type) {
    const resultDiv = document.getElementById('result');
    const alertClass = type === 'error' ? 'alert-danger' : 'alert-success';
    const icon = type === 'error' ? 'fa-exclamation-circle' : 'fa-check-circle';
    
    resultDiv.innerHTML = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            <i class="fas ${icon}"></i> ${msg}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    setTimeout(() => {
        const alert = resultDiv.querySelector('.alert');
        if (alert) {
            alert.classList.remove('show');
            setTimeout(() => {
                resultDiv.innerHTML = '';
            }, 150);
        }
    }, 5000);
}