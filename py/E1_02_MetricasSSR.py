# SCRIPT 2 - Calcular métricas E1 por SSR
# - Usa UF_UTM18S ya con riesgo_E1 y peso_E1
# - Calcula distancia a UF de alto y medio riesgo
# - Cuenta cuántas UF de cada riesgo hay en 1 km
# - Calcula E1_raw, E1_norm, E1_cat, E1_clas, UF_alto_id, expuesto_alto

import arcpy
import math

# === RUTAS DE ENTRADA ===
uf_path   = r"C:\ArcGIS_Proyectos\2025\SSR_Chiloe_MOP_BID\Trabajo\Trabajo GIS 01\GIS v02\E1.gdb\UF_UTM18S"
ssr_fc    = r"C:\ArcGIS_Proyectos\2025\SSR_Chiloe_MOP_BID\Trabajo\Trabajo GIS 01\GIS v02\E1.gdb\SSR_UTM18S"
out_gdb   = r"C:\ArcGIS_Proyectos\2025\SSR_Chiloe_MOP_BID\Trabajo\Trabajo GIS 01\GIS v02\E1.gdb"

arcpy.env.workspace = out_gdb
arcpy.env.overwriteOutput = True

# === CAMPOS DE UF ===
RIESGO_FIELD    = "riesgo_E1"
PESO_FIELD      = "peso_E1"
UF_ID_FIELD     = "UnidadFiscalizableId"   # ID textual de la UF

# === PARÁMETROS E1 ===
SEARCH_RADIUS_NEAR = "5000 Meters"   # radio máximo para Near
BUFFER_RADIUS_1KM  = "1000 Meters"   # radio para conteo de UF

# === CAMPOS A CREAR EN SSR ===
DIST_ALTO_FIELD      = "dist_UF_alto"       # DOUBLE (m)
DIST_MEDIO_FIELD     = "dist_UF_medio"      # DOUBLE (m)
CNT_ALTO_1KM_FIELD   = "cnt_UF_alto_1km"    # LONG
CNT_MEDIO_1KM_FIELD  = "cnt_UF_medio_1km"   # LONG
UF_ALTO_ID_FIELD     = "UF_alto_id"         # TEXT
EXP_ALTO_FIELD       = "expuesto_alto"      # SHORT (0/1)
E1_RAW_FIELD         = "E1_raw"             # DOUBLE
E1_NORM_FIELD        = "E1_norm"            # DOUBLE
E1_CAT_FIELD         = "E1_cat"             # TEXT
E1_CLAS_FIELD        = "E1_clas"            # SHORT

# === 0. Asegurar campos en SSR ===
ssr_fields = [f.name for f in arcpy.ListFields(ssr_fc)]

def ensure_field(fc, name, ftype, **kwargs):
    if name not in ssr_fields:
        arcpy.management.AddField(fc, name, ftype, **kwargs)
        ssr_fields.append(name)

ensure_field(ssr_fc, DIST_ALTO_FIELD,     "DOUBLE")
ensure_field(ssr_fc, DIST_MEDIO_FIELD,    "DOUBLE")
ensure_field(ssr_fc, CNT_ALTO_1KM_FIELD,  "LONG")
ensure_field(ssr_fc, CNT_MEDIO_1KM_FIELD, "LONG")
ensure_field(ssr_fc, UF_ALTO_ID_FIELD,    "TEXT", field_length=50)
ensure_field(ssr_fc, EXP_ALTO_FIELD,      "SHORT")
ensure_field(ssr_fc, E1_RAW_FIELD,        "DOUBLE")
ensure_field(ssr_fc, E1_NORM_FIELD,       "DOUBLE")
ensure_field(ssr_fc, E1_CAT_FIELD,        "TEXT", field_length=10)
ensure_field(ssr_fc, E1_CLAS_FIELD,       "SHORT")


# === 1. Crear layers de UF por riesgo ===
uf_alto_lyr  = "UF_alto_lyr"
uf_medio_lyr = "UF_medio_lyr"

arcpy.management.MakeFeatureLayer(uf_path, uf_alto_lyr,  f"{RIESGO_FIELD} = 'alto'")
arcpy.management.MakeFeatureLayer(uf_path, uf_medio_lyr, f"{RIESGO_FIELD} = 'medio'")

# === 2. Mapa OID -> UF_ID para UF (para llenar UF_alto_id) ===
uf_id_by_oid = {}
with arcpy.da.SearchCursor(uf_path, ["OID@", UF_ID_FIELD, RIESGO_FIELD]) as cur:
    for oid, ufid, riesgo in cur:
        if riesgo == "alto":
            uf_id_by_oid[oid] = ufid



# === 3. Calcular distancia a UF de alto riesgo (Near) ===
print("Calculando Near a UF de ALTO riesgo...")
arcpy.analysis.Near(ssr_fc, uf_alto_lyr, SEARCH_RADIUS_NEAR, method="PLANAR")

# Copiar NEAR_DIST a dist_UF_alto y NEAR_FID -> UF_alto_id
oid_field = arcpy.Describe(ssr_fc).OIDFieldName
near_fields = [oid_field, "NEAR_DIST", "NEAR_FID", DIST_ALTO_FIELD, UF_ALTO_ID_FIELD]

with arcpy.da.UpdateCursor(ssr_fc, near_fields) as cur:
    for oid, ndist, nfid, dist_alto, uf_alto_id in cur:
        # Distancia
        if ndist is None or ndist < 0:
            dist_val = None
        else:
            dist_val = float(ndist)

        # UF ID
        ufid_val = None
        if nfid is not None and nfid in uf_id_by_oid:
            ufid_val = uf_id_by_oid[nfid]

        cur.updateRow((oid, ndist, nfid, dist_val, ufid_val))



# === 4. Calcular distancia a UF de riesgo MEDIO (Near) ===
print("Calculando Near a UF de MEDIO riesgo...")
arcpy.analysis.Near(ssr_fc, uf_medio_lyr, SEARCH_RADIUS_NEAR, method="PLANAR")

near_fields_m = [oid_field, "NEAR_DIST", DIST_MEDIO_FIELD]
with arcpy.da.UpdateCursor(ssr_fc, near_fields_m) as cur:
    for oid, ndist, dist_medio in cur:
        if ndist is None or ndist < 0:
            dist_val = None
        else:
            dist_val = float(ndist)
        cur.updateRow((oid, ndist, dist_val))



# === 5. Buffers de 1 km alrededor de SSR ===
print("Creando buffer de 1 km alrededor de SSR...")
ssr_buf_1km = "SSR_buf_1km"
arcpy.analysis.Buffer(ssr_fc, ssr_buf_1km, BUFFER_RADIUS_1KM,
                      line_side="FULL", line_end_type="ROUND",
                      dissolve_option="NONE", dissolve_field=None)



# === 6. Spatial Join para contar UF de alto riesgo dentro de 1 km ===
print("Spatial Join para conteo UF ALTO en 1 km...")
sj_alto_fc = "SSR_buf_1km_SJ_alto"
arcpy.analysis.SpatialJoin(
    target_features=ssr_buf_1km,
    join_features=uf_alto_lyr,
    out_feature_class=sj_alto_fc,
    join_operation="JOIN_ONE_TO_ONE",
    join_type="KEEP_ALL",
    match_option="INTERSECT"
)
# Por defecto, SpatialJoin crea campo Join_Count

# Crear dict ORIG_FID -> Join_Count (alto)
cnt_alto_by_oid = {}
with arcpy.da.SearchCursor(sj_alto_fc, ["ORIG_FID", "Join_Count"]) as cur:
    for orig_fid, jcount in cur:
        cnt_alto_by_oid[orig_fid] = int(jcount) if jcount is not None else 0



# === 7. Spatial Join para contar UF de riesgo MEDIO dentro de 1 km ===
print("Spatial Join para conteo UF MEDIO en 1 km...")
sj_medio_fc = "SSR_buf_1km_SJ_medio"
arcpy.analysis.SpatialJoin(
    target_features=ssr_buf_1km,
    join_features=uf_medio_lyr,
    out_feature_class=sj_medio_fc,
    join_operation="JOIN_ONE_TO_ONE",
    join_type="KEEP_ALL",
    match_option="INTERSECT"
)

cnt_medio_by_oid = {}
with arcpy.da.SearchCursor(sj_medio_fc, ["ORIG_FID", "Join_Count"]) as cur:
    for orig_fid, jcount in cur:
        cnt_medio_by_oid[orig_fid] = int(jcount) if jcount is not None else 0



# === 8. Copiar conteos a SSR ===
print("Copiando conteos de UF a SSR...")
with arcpy.da.UpdateCursor(ssr_fc, [oid_field, CNT_ALTO_1KM_FIELD, CNT_MEDIO_1KM_FIELD]) as cur:
    for oid, cnt_alto, cnt_medio in cur:
        # ORIG_FID corresponde al OID original de SSR en el buffer
        new_cnt_alto  = cnt_alto_by_oid.get(oid, 0)
        new_cnt_medio = cnt_medio_by_oid.get(oid, 0)
        cur.updateRow((oid, new_cnt_alto, new_cnt_medio))



# === 9. Calcular E1_raw, expuesto_alto ===
print("Calculando E1_raw y expuesto_alto...")
max_raw = 0.0

fields_calc = [DIST_ALTO_FIELD, DIST_MEDIO_FIELD,
               CNT_ALTO_1KM_FIELD, CNT_MEDIO_1KM_FIELD,
               E1_RAW_FIELD, EXP_ALTO_FIELD]

with arcpy.da.UpdateCursor(ssr_fc, fields_calc) as cur:
    for dist_alto, dist_medio, cnt_alto, cnt_medio, e1_raw, exp_alto in cur:
        d_alto_km  = None
        d_medio_km = None

        if dist_alto is not None and dist_alto >= 0:
            d_alto_km = dist_alto / 1000.0
        if dist_medio is not None and dist_medio >= 0:
            d_medio_km = dist_medio / 1000.0

        # Componentes de E1_raw (puedes ajustar coeficientes)
        comp_dist_alto  = 0.0
        comp_dist_medio = 0.0
        comp_cnt        = 0.0

        if d_alto_km is not None:
            comp_dist_alto = 3.0 / (1.0 + d_alto_km)   # peso 3 para alto riesgo

        if d_medio_km is not None:
            comp_dist_medio = 2.0 / (1.0 + d_medio_km) # peso 2 para medio riesgo

        cnt_alto  = cnt_alto  if cnt_alto  is not None else 0
        cnt_medio = cnt_medio if cnt_medio is not None else 0

        # peso para cantidades en 1 km
        comp_cnt = 0.5 * cnt_alto + 0.25 * cnt_medio

        e1_val = comp_dist_alto + comp_dist_medio + comp_cnt

        # expuesto_alto = 1 si hay UF alto dentro de 1 km o muy cerca
        exp = 0
        if cnt_alto > 0:
            exp = 1
        elif dist_alto is not None and dist_alto <= 1000:
            exp = 1

        max_raw = max(max_raw, e1_val)

        cur.updateRow((dist_alto, dist_medio, cnt_alto, cnt_medio, e1_val, exp))

print(f"Máximo E1_raw observado: {max_raw}")



# === 10. Normalizar E1_raw a E1_norm y crear E1_cat / E1_clas ===
print("Normalizando E1 y creando categorías...")

def clasificar_e1(e_norm):
    if e_norm is None:
        return ("Muy baja", 1)
    if e_norm < 0.25:
        return ("Muy baja", 1)
    elif e_norm < 0.50:
        return ("Baja", 2)
    elif e_norm < 0.75:
        return ("Media", 3)
    else:
        return ("Alta", 4)

if max_raw > 0:
    with arcpy.da.UpdateCursor(ssr_fc, [E1_RAW_FIELD, E1_NORM_FIELD,
                                        E1_CAT_FIELD, E1_CLAS_FIELD]) as cur:
        for e1_raw, e1_norm, e1_cat, e1_clas in cur:
            if e1_raw is None:
                en = None
            else:
                en = float(e1_raw) / max_raw

            cat, clas = clasificar_e1(en)
            cur.updateRow((e1_raw, en, cat, clas))
else:
    print("OJO: max_raw = 0, no se normaliza E1.")

print("Listo SCRIPT 2: métricas E1 calculadas en SSR_UTM18S.")


