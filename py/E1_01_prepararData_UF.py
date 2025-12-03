# SCRIPT 1 - Preparar UF para indicador E1 (cercanía a fuentes de contaminación)
# Autor: NICOLAS FIERRO VIEDMA
# Contacto: nicofierrov@outlook.fr
# Descripción:
# - Lee la capa UF_UTM18S
# - Asigna un nivel de riesgo (alto/medio/bajo) según CATEGORIA/SUBCATEGORIA
# - Asigna un peso numérico (3/2/1) para usar en el indicador compuesto E1
# - Crea/actualiza los campos: riesgo_E1 (TEXT), peso_E1 (SHORT)





import arcpy
# === RUTAS DE ENTRADA (AJUSTA SI ES NECESARIO) ===
uf_path = r"C:\ArcGIS_Proyectos\2025\SSR_Chiloe_MOP_BID\Trabajo\Trabajo GIS 01\GIS v02\E1.gdb\UF_UTM18S"

# Nombre de campo en la FC UF que contiene la categoría y subcategoría.
# Ajusta estos nombres si no coinciden exactamente con tu esquema.
CATEGORIA_FIELD = "CategoriaEconomicaNombre"
SUBCATEGORIA_FIELD = "SubCategoriaEconomicaNombre"

# === CAMPOS A CREAR/ACTUALIZAR ===
RIESGO_FIELD = "riesgo_E1"    # texto: 'alto', 'medio', 'bajo'
PESO_FIELD   = "peso_E1"      # corto: 3, 2, 1



# === 1. Verificar / crear campos de salida ===

fields = [f.name for f in arcpy.ListFields(uf_path)]

if RIESGO_FIELD not in fields:
    arcpy.management.AddField(uf_path, RIESGO_FIELD, "TEXT", field_length=10)

if PESO_FIELD not in fields:
    arcpy.management.AddField(uf_path, PESO_FIELD, "SHORT")




# === 2. Tablas de riesgo (basado en subcategoría y categoría) ===
subcat_risk = {
# RIESGO ALTO
"Planta de Tratamiento de Aguas Servidas": ("alto", 3),
"Planta de tratamiento de aguas servidas": ("alto", 3),
"Planta de tratamiento de RILES": ("alto", 3),
"Relleno sanitario": ("alto", 3),
"Vertedero": ("alto", 3),
"Centro de almacenamiento de sustancias peligrosas": ("alto", 3),
"Transporte de sustancias peligrosas": ("alto", 3),
"Estación de servicio": ("alto", 3),
"Estacion de servicio": ("alto", 3),
"Matadero": ("alto", 3),
"Matadero / frigorìfico": ("alto", 3),
"Matadero / frigorifico": ("alto", 3),
"Planta procesadora de productos pecuarios": ("alto", 3),
"Planta de procesamiento no metálicos": ("alto", 3),
"Planta de procesamiento no metalicos": ("alto", 3),
"Planta de reciclaje": ("alto", 3),
"Central termoeléctrica": ("alto", 3),
"Central termoeléctrica a carbón": ("alto", 3),


# RIESGO MEDIO
"Centro de cultivo de salmones": ("medio", 2),
"Centro de cultivo de peces": ("medio", 2),
"Centro de cultivo de algas": ("medio", 2),
"Centro de cultivo de moluscos": ("medio", 2),
"Centro de cultivo de crustáceos": ("medio", 2),
"Astillero": ("medio", 2),
"Puerto": ("medio", 2),
"Terminal marítimo": ("medio", 2),
"Central hidroeléctrica": ("medio", 2),
"Parque eólico": ("medio", 2),
"Aserradero": ("medio", 2),
"Procesadora de madera": ("medio", 2),
"Cementerio": ("medio", 2),
"Línea de transmisión": ("medio", 2),


# RIESGO BAJO
"Centro comercial": ("bajo", 1),
"Proyecto inmobiliario": ("bajo", 1),
"Panadería": ("bajo", 1),
"Panaderia": ("bajo", 1),
"Establecimiento educacional": ("bajo", 1),
"Centro religioso": ("bajo", 1),
"Centro de culto": ("bajo", 1),
"Restaurante": ("bajo", 1),
"Restorán": ("bajo", 1),
"Otros": ("bajo", 1),
}


cat_risk = {
"Saneamiento ambiental": ("alto", 3),
"Energía": ("medio", 2),
"Pesca y acuicultura": ("medio", 2),
"Agroindustria": ("medio", 2),
"Comercio y servicios": ("bajo", 1),
"Educación": ("bajo", 1),
}


DEFAULT_RIESGO = "bajo"
DEFAULT_PESO = 1

# === 3. Asignar riesgo y peso a cada UF ===

campus = [CATEGORIA_FIELD, SUBCATEGORIA_FIELD, RIESGO_FIELD, PESO_FIELD]

with arcpy.da.UpdateCursor(uf_path, campus) as cursor:
    for cat, subcat, riesgo, peso in cursor:
        cat_str = (cat or "").strip()
        sub_str = (subcat or "").strip()

        # valores default
        r = DEFAULT_RIESGO
        w = DEFAULT_PESO

        # prioridad: subcategoría
        if sub_str in subcat_risk:
            r, w = subcat_risk[sub_str]

        # si no, categoría
        elif cat_str in cat_risk:
            r, w = cat_risk[cat_str]

        # actualizar fila
        cursor.updateRow((cat_str, sub_str, r, w))

print(f"Listo: campos '{RIESGO_FIELD}' y '{PESO_FIELD}' actualizados en UF_UTM18S")



