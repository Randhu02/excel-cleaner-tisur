// Elementos del DOM
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const fileSize = document.getElementById('fileSize');
const clearFile = document.getElementById('clearFile');
const previewBtn = document.getElementById('previewBtn');
const cleanBtn = document.getElementById('cleanBtn');
const exportPdfBtn = document.getElementById('exportPdfBtn');
const exportCsvBtn = document.getElementById('exportCsvBtn');
const loading = document.getElementById('loading');
const statsCard = document.getElementById('statsCard');
const previewCard = document.getElementById('previewCard');
const result = document.getElementById('result');
const progressBar = document.getElementById('progressBar');

let selectedFile = null;

// Mostrar fecha y hora actual
function updateDateTime() {
    const now = new Date();
    const fecha = now.toLocaleDateString('es-ES', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    });
    const hora = now.toLocaleTimeString('es-ES');
    
    const fechaElem = document.getElementById('fechaActual');
    const horaElem = document.getElementById('horaActual');
    if (fechaElem) fechaElem.textContent = fecha;
    if (horaElem) horaElem.textContent = hora;
}

setInterval(updateDateTime, 1000);
updateDateTime();

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
    
    // Calcular tamaño del archivo
    const sizeInMB = (file.size / (1024 * 1024)).toFixed(2);
    fileSize.textContent = `${sizeInMB} MB`;
    
    fileInfo.style.display = 'block';
    uploadArea.style.display = 'none';
    
    // Habilitar botones
    const buttons = [previewBtn, cleanBtn, exportPdfBtn, exportCsvBtn];
    buttons.forEach(btn => {
        if (btn) btn.disabled = false;
    });
    
    result.innerHTML = '';
    statsCard.style.display = 'none';
    previewCard.style.display = 'none';
}

clearFile.addEventListener('click', () => {
    selectedFile = null;
    fileInfo.style.display = 'none';
    uploadArea.style.display = 'block';
    
    const buttons = [previewBtn, cleanBtn, exportPdfBtn, exportCsvBtn];
    buttons.forEach(btn => {
        if (btn) btn.disabled = true;
    });
    
    fileInput.value = '';
    result.innerHTML = '';
    statsCard.style.display = 'none';
    previewCard.style.display = 'none';
});

// Simular progreso
function simulateProgress() {
    let width = 0;
    const interval = setInterval(() => {
        if (width >= 90) {
            clearInterval(interval);
        } else {
            width += 10;
            if (progressBar) progressBar.style.width = width + '%';
        }
    }, 200);
    return interval;
}

// Vista previa
previewBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    
    previewBtn.disabled = true;
    loading.style.display = 'block';
    const progressInterval = simulateProgress();
    
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
        
        if (progressBar) progressBar.style.width = '100%';
        setTimeout(() => {
            if (progressBar) progressBar.style.width = '0%';
        }, 500);
        
        displayStats(data.stats);
        displayPreview(data.preview);
        showMessage('✅ Vista previa generada correctamente', 'success');
        
    } catch (error) {
        showMessage(`❌ Error: ${error.message}`, 'error');
    } finally {
        clearInterval(progressInterval);
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
    exportCsvBtn.disabled = true;
    loading.style.display = 'block';
    const progressInterval = simulateProgress();
    
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
        a.download = `USD_2026_limpio_${new Date().toISOString().slice(0,19).replace(/:/g, '-')}.xlsx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        if (progressBar) progressBar.style.width = '100%';
        setTimeout(() => {
            if (progressBar) progressBar.style.width = '0%';
        }, 500);
        
        showMessage('✅ Archivo procesado correctamente. ¡Descarga iniciada!', 'success');
        
    } catch (error) {
        showMessage(`❌ Error: ${error.message}`, 'error');
    } finally {
        clearInterval(progressInterval);
        cleanBtn.disabled = false;
        previewBtn.disabled = false;
        exportPdfBtn.disabled = false;
        exportCsvBtn.disabled = false;
        loading.style.display = 'none';
    }
});

// Exportar PDF
exportPdfBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    
    exportPdfBtn.disabled = true;
    loading.style.display = 'block';
    const progressInterval = simulateProgress();
    
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
        a.download = `USD_2026_reporte_${new Date().toISOString().slice(0,19).replace(/:/g, '-')}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        if (progressBar) progressBar.style.width = '100%';
        setTimeout(() => {
            if (progressBar) progressBar.style.width = '0%';
        }, 500);
        
        showMessage('✅ PDF generado correctamente. ¡Descarga iniciada!', 'success');
        
    } catch (error) {
        showMessage(`❌ Error: ${error.message}`, 'error');
    } finally {
        clearInterval(progressInterval);
        exportPdfBtn.disabled = false;
        loading.style.display = 'none';
    }
});

// Exportar CSV (nueva funcionalidad)
if (exportCsvBtn) {
    exportCsvBtn.addEventListener('click', async () => {
        if (!selectedFile) return;
        
        exportCsvBtn.disabled = true;
        loading.style.display = 'block';
        
        const formData = new FormData();
        formData.append('file', selectedFile);
        
        try {
            const response = await fetch('/export_csv', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Error al generar CSV');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `USD_2026_limpio_${new Date().toISOString().slice(0,19).replace(/:/g, '-')}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showMessage('✅ CSV generado correctamente. ¡Descarga iniciada!', 'success');
            
        } catch (error) {
            showMessage(`❌ Error: ${error.message}`, 'error');
        } finally {
            exportCsvBtn.disabled = false;
            loading.style.display = 'none';
        }
    });
}

function displayStats(stats) {
    const statsContent = document.getElementById('statsContent');
    
    let html = `
        <div class="stats-grid">
            <div class="stat-card">
                <i class="fas fa-database"></i>
                <h3>${stats.total_registros || stats.registros_finales || 0}</h3>
                <p>Total Registros Procesados</p>
            </div>
            <div class="stat-card">
                <i class="fas fa-columns"></i>
                <h3>${stats.total_columnas || stats.columnas_finales || 0}</h3>
                <p>Total Columnas</p>
            </div>
            <div class="stat-card">
                <i class="fas fa-chart-line"></i>
                <h3>${stats.registros_iniciales || stats.total_registros || 0}</h3>
                <p>Registros Originales</p>
            </div>
        </div>
        <h6><i class="fas fa-list-check"></i> Modificaciones Aplicadas:</h6>
        <ul class="modifications-list">
    `;
    
    const modificaciones = stats.modificaciones || (stats.resumen && stats.resumen.modificaciones) || [];
    modificaciones.forEach(mod => {
        html += `<li>${mod}</li>`;
    });
    
    if (modificaciones.length === 0) {
        html += `<li class="text-muted">No se registraron modificaciones específicas</li>`;
    }
    
    html += `</ul>`;
    html += `<hr class="my-3">`;
    html += `<small class="text-muted">
        <i class="fas fa-clock"></i> Procesado el: ${new Date().toLocaleString('es-ES')}
        <br><i class="fas fa-tag"></i> Columnas: ${(stats.columnas || []).slice(0, 10).join(', ')}${(stats.columnas || []).length > 10 ? '...' : ''}
    </small>`;
    
    statsContent.innerHTML = html;
    statsCard.style.display = 'block';
}

function displayPreview(data) {
    const previewContent = document.getElementById('previewContent');
    
    if (!data || data.length === 0) {
        previewContent.innerHTML = '<p class="text-muted text-center">No hay datos para mostrar</p>';
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
            let value = row[col] || '';
            if (value.toString().length > 50) {
                value = value.toString().substring(0, 50) + '...';
            }
            html += `<td title="${row[col] || ''}">${value}</td>`;
        });
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    html += `<p class="text-muted mt-2"><small><i class="fas fa-info-circle"></i> Mostrando primeras ${data.length} filas. El archivo completo tiene más registros.</small></p>`;
    
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