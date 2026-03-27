import pandas as pd
import io
from abc import ABC, abstractmethod

class BaseCleaner(ABC):
    """Clase base para todos los limpiadores"""
    
    def __init__(self, file_bytes):
        self.file_bytes = file_bytes
        self.xls = pd.ExcelFile(io.BytesIO(file_bytes))
        self.stats = {
            'registros_iniciales': 0,
            'columnas_iniciales': 0,
            'modificaciones': []
        }
    
    @abstractmethod
    def clean(self):
        """Método que debe implementar cada limpiador"""
        pass
    
    def get_stats(self):
        return self.stats
    
    def _validate_required_sheets(self, required_sheets):
        """Valida que el Excel tenga las hojas requeridas"""
        available_sheets = self.xls.sheet_names
        missing = [s for s in required_sheets if s not in available_sheets]
        if missing:
            raise ValueError(f"Hojas faltantes: {missing}")
        return True