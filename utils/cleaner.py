import pandas as pd
import io
from .cleaner_usd import USD2026Cleaner
from .cleaner_tm import TMCleaner

def clean_excel_data(file_bytes, file_type=None):
    """
    Función principal de limpieza que selecciona el limpiador adecuado
    
    Args:
        file_bytes: bytes del archivo Excel
        file_type: "usd", "tm" o None (auto-detecta)
    
    Returns:
        tuple: (df_limpio, estadisticas)
    """
    # Auto-detectar si no se especifica
    if file_type is None:
        file_type = detect_file_type(file_bytes)
    
    if file_type == "usd":
        cleaner = USD2026Cleaner(file_bytes)
    elif file_type == "tm":
        cleaner = TMCleaner(file_bytes)
    else:
        raise ValueError(f"Tipo de archivo no soportado: {file_type}")
    
    return cleaner.clean()

def detect_file_type(file_bytes):
    """
    Detecta automáticamente el tipo de archivo por las hojas que contiene
    """
    xls = pd.ExcelFile(io.BytesIO(file_bytes))
    sheets = xls.sheet_names
    
    # Detectar por hojas
    if "USD" in sheets and "Maestro recaladas" in sheets:
        return "usd"
    elif "TM" in sheets and "Cargas TM" in sheets:
        return "tm"
    else:
        # Si no se puede detectar, asumir usd (fallback)
        return "usd"