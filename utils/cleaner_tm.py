import pandas as pd
from .base_cleaner import BaseCleaner

class TMCleaner(BaseCleaner):
    """Limpiador específico para TM 2026"""
    
    def clean(self):
        # Validar hojas requeridas
        required_sheets = ["TM", "Cargas TM", "Clientes TM"]
        self._validate_required_sheets(required_sheets)
        
        # Leer las hojas
        df_tm = pd.read_excel(self.xls, "TM")
        df_cargas = pd.read_excel(self.xls, "Cargas TM")
        df_clientes = pd.read_excel(self.xls, "Clientes TM")
        
        self.stats['registros_iniciales'] = len(df_tm)
        self.stats['columnas_iniciales'] = len(df_tm.columns)
        
        # ========== 1. ASIGNAR CLIENTE2 ==========
        def asignar_cliente(row, clientes_df):
            # Reglas especiales
            if row["Carga original"] in ["SOYA", "TORTA DE SOYA"] and row["Cliente1"] == "CARGILL AMERICAS PERU S.R.L":
                return "Otros"
            elif row["Carga original"] == "BOLAS DE ACERO":
                return "Otros"
            elif row["Cliente1"] == "IMPORTADORA Y EXPORTADORA MONTERREY S.R.L" and row["Regimen"] == "IMPORTACION":
                return "Otros"
            elif row["Carga original"] == "FERTILIZANTES" and row["Tipo_Carga"] == "CARGA FRACCIONADA":
                return "Otros"
            elif row["Carga original"] == "ACIDO SULFURICO" and row["Cliente1"] == "COMPAÑIA MINERA ANTAPACCAY S.A." and row["Regimen"] == "IMPORTACION":
                return "Xstrata"
            elif row["Carga original"] == "ACIDO SULFURICO" and row["Cliente1"] == "COMPAÑIA MINERA ANTAPACCAY S.A." and row["Regimen"] == "CABOTAJE DESCARGA":
                return "Glencore"
            elif row["Cliente1"] == "SOCIEDAD MINERA CERRO VERDE S.A.A.":
                return "Cerro Verde"
            else:
                # Buscar en la hoja clientes TM
                cliente = clientes_df.loc[clientes_df["Cliente1"] == row["Cliente1"], "Cliente2"]
                if not cliente.empty:
                    return cliente.values[0]
                else:
                    return "Otros"
        
        df_tm["Cliente2"] = df_tm.apply(lambda row: asignar_cliente(row, df_clientes), axis=1)
        self.stats['modificaciones'].append('Cliente2 asignado')
        
        # ========== 2. ASIGNAR CARGA ==========
        def asignar_carga(row, cargas_df):
            # Regla 1: Ácido sulfúrico con ciertos clientes
            if row["Carga original"] == "ACIDO SULFURICO" and row["Cliente1"] in ["COMPAÑIA MINERA ANTAPACCAY S.A.", "SOCIEDAD MINERA CERRO VERDE S.A.A."]:
                return "ACIDO SULFURICO"
            # Regla 2: Cátodos de cobre fraccionados
            elif row["Carga original"] in ["CATODOS COBRE", "CATODOS DE COBRE"] and row["Tipo_Carga"] == "CARGA FRACCIONADA":
                return "Cátodos Cu"
            # Regla 3: Contenedores
            elif row["Tipo_Carga"] == "CONTENEDORES":
                return row.get("Tipo_Contenedor", "")
            # Regla 4: Concentrado de cobre según Cliente2
            elif row["Cliente2"] in ["Cerro Verde", "Las Bambas", "Antapaccay"]:
                return "CONCENTRADO DE COBRE / CU AMA F"
            elif row["Cliente2"] in ["Hudbay", "Marcobre"]:
                return "CONCENTRADO DE COBRE / CU"
            # Regla 5: Buscar en hoja Cargas TM
            else:
                carga = cargas_df.loc[cargas_df["Carga original"] == row["Carga original"], "Carga"]
                if not carga.empty:
                    return carga.values[0]
                else:
                    return ""
        
        df_tm["Carga"] = df_tm.apply(lambda row: asignar_carga(row, df_cargas), axis=1)
        self.stats['modificaciones'].append('Carga asignada')
        
        # ========== 3. CALCULAR TM ==========
        df_tm["TM"] = df_tm["Peso Kg"] / 1000
        self.stats['modificaciones'].append('TM calculada (Peso Kg / 1000)')
        
        # ========== 4. PROCESAR FECHAS ==========
        df_tm["DesAtraque_F_Ultima_Linea"] = pd.to_datetime(df_tm["DesAtraque_F_Ultima_Linea"], errors="coerce")
        df_tm["Mes_num"] = df_tm["DesAtraque_F_Ultima_Linea"].dt.month
        
        meses_es = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }
        df_tm["Mes"] = df_tm["Mes_num"].map(meses_es)
        self.stats['modificaciones'].append('Mes extraído de fecha')
        
        # ========== 5. REORDENAR COLUMNAS ==========
        cols = list(df_tm.columns)
        
        # Quitamos las columnas que vamos a mover
        for c in ["Mes", "Cliente2", "TM", "Carga", "Carga original"]:
            if c in cols:
                cols.remove(c)
        
        # Nuevo orden
        new_order = ["Mes", "Cliente2"]
        
        # Insertar "TM" después de "Peso Kg"
        if "Peso Kg" in cols:
            idx_peso = cols.index("Peso Kg")
            cols.insert(idx_peso + 1, "TM")
        
        # Insertar "Carga" después de "Tipo_Contenedor"
        if "Tipo_Contenedor" in cols:
            idx_tipo = cols.index("Tipo_Contenedor")
            cols.insert(idx_tipo + 1, "Carga")
        
        new_order.extend(cols)
        new_order.insert(-1, "Carga original")
        
        df_tm = df_tm[new_order]
        self.stats['modificaciones'].append('Columnas reordenadas')
        
        # Estadísticas finales
        self.stats['registros_finales'] = len(df_tm)
        self.stats['columnas_finales'] = len(df_tm.columns)
        
        return df_tm, self.stats