import pandas as pd
import io

def clean_excel_data(file_bytes):
    """
    Función principal de limpieza - Adaptada de tu notebook
    Retorna: (df_limpio, estadisticas)
    """
    
    # Leer todas las hojas del Excel
    xls = pd.ExcelFile(io.BytesIO(file_bytes))
    
    # Leer las hojas
    df_usd = pd.read_excel(xls, "USD")
    df_maestro = pd.read_excel(xls, "Maestro recaladas")
    df_servicios = pd.read_excel(xls, "Servicios USD")
    df_clase_carga = pd.read_excel(xls, "Clase carga USD")
    df_clientes = pd.read_excel(xls, "Clientes USD")
    df_tipo_ingreso = pd.read_excel(xls, "Tipo Ingreso")
    
    # Estadísticas iniciales
    stats = {
        'registros_iniciales': len(df_usd),
        'columnas_iniciales': len(df_usd.columns),
        'modificaciones': []
    }
    
    # ========== 1. RÉGIMEN ==========
    mapa_regimen = dict(zip(df_maestro["Recalada"], df_maestro["Régimen"]))
    
    def asignar_regimen(row):
        if str(row["Recalada"]) == "17" and str(row["Carga original"]).strip().upper() == "MOLIBDENO":
            return "EXPORTACION"
        elif pd.isna(row["Régimen"]) or str(row["Régimen"]).strip() == "":
            return mapa_regimen.get(row["Recalada"], row["Régimen"])
        else:
            return row["Régimen"]
    
    df_usd["Régimen"] = df_usd.apply(asignar_regimen, axis=1)
    stats['modificaciones'].append('Régimen completado y corregido')
    
    invalidos = ["MOVILIZACION", "MOVILIZACION VIA MUELLE", "TERRESTRE", "TRANSBORDO"]
    usd_merge = df_usd.merge(
        df_maestro[['Recalada','Régimen']],
        on='Recalada',
        how='left',
        suffixes=('', '_maestro')
    )
    usd_merge['Régimen'] = usd_merge.apply(
        lambda fila: fila['Régimen_maestro']
                     if str(fila['Régimen']).strip().upper() in [v.upper() for v in invalidos]
                     else fila['Régimen'],
        axis=1
    )
    df_usd = usd_merge.drop(columns=['Régimen_maestro'])
    
    # ========== 2. SERVICIOS 2 ==========
    df_usd = df_usd.merge(
        df_servicios[['Servicio','Servicios 2']],
        on='Servicio',
        how='left',
        suffixes=('', '_serv')
    )
    if 'Servicios 2_serv' in df_usd.columns:
        df_usd['Servicios 2'] = df_usd['Servicios 2_serv']
    cols_a_borrar = [c for c in df_usd.columns if c.startswith('Servicios 2_')]
    df_usd = df_usd.drop(columns=cols_a_borrar)
    stats['modificaciones'].append('Servicios 2 insertado')
    
    # ========== 3. TIPO ==========
    df_usd = df_usd.merge(
        df_tipo_ingreso[['Servicios 2','Tipo']],
        on='Servicios 2',
        how='left',
        suffixes=('', '_serv')
    )
    stats['modificaciones'].append('Tipo insertado')
    
    # ========== 4. CLASE CARGA - Completar vacíos ==========
    df_usd = df_usd.merge(
        df_maestro[['Recalada','Clase Carga']],
        on='Recalada',
        how='left',
        suffixes=('', '_maestro')
    )
    df_usd['Clase Carga'] = df_usd['Clase Carga'].fillna(df_usd['Clase Carga_maestro'])
    df_usd = df_usd.drop(columns=['Clase Carga_maestro'])
    stats['modificaciones'].append('Clase Carga completada')
    
    # ========== 5. CLASE CARGA - Reglas especiales ==========
    mapa_recaladas = dict(zip(df_maestro["Recalada"], df_maestro["Clase Carga"]))
    
    # Regla MOLIBDENO
    def asignar_clase_molibdeno(row):
        if row["Carga original"] == "MOLIBDENO":
            if str(row["Recalada"]) == "17":
                return "CONTENEDORES"
            else:
                return mapa_recaladas.get(row["Recalada"], row["Clase Carga"])
        return row["Clase Carga"]
    df_usd["Clase Carga"] = df_usd.apply(asignar_clase_molibdeno, axis=1)
    
    # Regla MERCADERIA GENERAL
    def asignar_clase_mercaderia(row):
        if row["Carga original"] == "MERCADERIA GENERAL":
            if str(row["Recalada"]) == "17":
                return "CONTENEDORES"
            elif any(palabra in str(row.get("observación", "")).lower() for palabra in ["envase", "envases"]):
                return "CARGA FRACCIONADA"
            else:
                return mapa_recaladas.get(row["Recalada"], row["Clase Carga"])
        return row["Clase Carga"]
    df_usd["Clase Carga"] = df_usd.apply(asignar_clase_mercaderia, axis=1)
    
    # Regla CATODOS COBRE
    def asignar_clase_catodos(row):
        if row["Carga original"] == "CATODOS COBRE":
            if str(row["Recalada"]) == "17":
                return "CONTENEDORES"
            else:
                return mapa_recaladas.get(row["Recalada"], row["Clase Carga"])
        return row["Clase Carga"]
    df_usd["Clase Carga"] = df_usd.apply(asignar_clase_catodos, axis=1)
    stats['modificaciones'].append('Reglas especiales aplicadas a Clase Carga')
    
    # ========== 6. CLIENTE2 ==========
    mapa_clientes = dict(zip(df_clientes["Cliente1"], df_clientes["Cliente2"]))
    mapa_maestro_cliente2 = dict(zip(df_maestro["Recalada"], df_maestro["Cliente2"]))
    
    def asignar_cliente2(row):
        cargas_validas = ["CONCENTRADO DE COBRE / CU", "MINERAL DE ZINC", "CONCENTRADO DE ZINC"]
        cargas_especiales = ["CATODOS COBRE", "ACIDO SULFURICO", "MOLIBDENO"]
        recaladas_especiales = ["17", "0000000G03"]
        clientes_especiales = [
            "COMPAÑIA MINERA ANTAPACCAY S.A.",
            "MINERA LAS BAMBAS S.A.",
            "SOCIEDAD MINERA CERRO VERDE S.A.A.",
            "HUDBAY PERU S.A.C"
        ]
        
        if row["Carga original"] in cargas_especiales:
            return "Otros"
        elif row["Cliente1"] in clientes_especiales:
            return mapa_clientes.get(row["Cliente1"], "Otros")
        elif str(row["Recalada"]) in recaladas_especiales and row["Carga original"] in cargas_validas:
            return mapa_clientes.get(row["Cliente1"], "Otros")
        else:
            return mapa_maestro_cliente2.get(row["Recalada"], "Otros")
    
    df_usd["Cliente2"] = df_usd.apply(asignar_cliente2, axis=1)
    stats['modificaciones'].append('Cliente2 asignado')
    
    # ========== 7. TIPO CARGA ==========
    mapa_clase = dict(zip(df_clase_carga["Carga original"], df_clase_carga["Carga"]))
    mapa_maestro_carga = dict(zip(df_maestro["Recalada"], df_maestro["Carga original"]))
    
    def asignar_carga_provisional(row):
        cliente = str(row["Cliente2"]).strip().upper()
        if any(x in cliente for x in ["CERRO VERDE", "ANTAPACCAY", "LAS BAMBAS"]):
            return "CONCENTRADO DE COBRE / CU AMA F"
        elif any(x in cliente for x in ["HUDBAY", "MARCOBRE"]):
            return "CONCENTRADO DE COBRE / CU"
        else:
            carga_original = str(row["Carga original"]).strip()
            if carga_original == "" or pd.isna(row["Carga original"]):
                return mapa_maestro_carga.get(row["Recalada"], "Otros")
            else:
                return carga_original
    
    df_usd["Carga_provisional"] = df_usd.apply(asignar_carga_provisional, axis=1)
    
    def asignar_tipo_carga(row):
        especiales = ["MOLIBDENO", "MERCADERIA GENERAL", "CATODOS COBRE"]
        carga_prov = str(row["Carga_provisional"]).strip()
        clase_carga = str(row["Clase Carga"]).strip().upper() if pd.notna(row["Clase Carga"]) else ""
        
        if carga_prov in especiales:
            if clase_carga == "CONTENEDORES":
                return mapa_maestro_carga.get(row["Recalada"], "Otros")
            else:
                return carga_prov
        else:
            return mapa_clase.get(carga_prov, "Otros")
    
    df_usd["Tipo Carga"] = df_usd.apply(asignar_tipo_carga, axis=1)
    stats['modificaciones'].append('Tipo Carga asignado')
    
    # ========== 8. ORDENAR COLUMNAS ==========
    orden_columnas = ["Mes", "Cliente2", "Tipo"]
    
    for col in df_usd.columns:
        if col not in ["Mes", "Cliente2", "Tipo", "Servicios 2", "Tipo Carga"]:
            orden_columnas.append(col)
            if col == "Servicio":
                orden_columnas.append("Servicios 2")
            if col == "Clase Carga":
                orden_columnas.append("Tipo Carga")
    
    df_usd = df_usd[orden_columnas]
    stats['modificaciones'].append('Columnas reordenadas')
    
    # Estadísticas finales
    stats['registros_finales'] = len(df_usd)
    stats['columnas_finales'] = len(df_usd.columns)
    
    return df_usd, stats