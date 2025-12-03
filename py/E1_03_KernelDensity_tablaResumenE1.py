# SCRIPT 3 - Kernel + tablas resumen para E1
# - Genera un raster de Kernel Density ponderado por peso_E1 (UF)
# - Extrae el valor de densidad a cada SSR (kernel_val)
# - Crea tablas resumen por COMUNA y por SHAC:
#   * promedio E1_norm
#   * proporción de SSR en Alta exposición (E1_clas = 4)

import arcpy
from arcpy.sa import KernelDensity, ExtractMultiValuesToPoints

arcpy.CheckOutExtension("Spatial")

# === RUTAS ===
# Ruta a Unidades Fiscalizables
uf_path   = r"C:\ArcGIS_Proyectos\2025\SSR_Chiloe_MOP_BID\Trabajo\Trabajo GIS 01\GIS v02\E1.gdb\UF_UTM18S"
# Ruta a SSR
ssr_fc    = r"C:\ArcGIS_Proyectos\2025\SSR_Chiloe_MOP_BID\Trabajo\Trabajo GIS 01\GIS v02\E1.gdb\SSR_UTM18S"
# Ruta a SHAC
shac_fc   = r"C:\ArcGIS_Proyectos\2025\SSR_Chiloe_MOP_BID\Trabajo\Trabajo GIS 01\GIS v02\GIS v02.gdb\SHAC_WGS84_18S"
# Ruta output .gdb
out_gdb   = r"C:\ArcGIS_Proyectos\2025\SSR_Chiloe_MOP_BID\Trabajo\Trabajo GIS 01\GIS v02\E1.gdb"

arcpy.env.workspace = out_gdb
arcpy.env.overwriteOutput = True

# === CAMPOS CLAVE ===
PESO_FIELD    = "peso_E1"      # en UF
E1_NORM_FIELD = "E1_norm"
E1_CLAS_FIELD = "E1_clas"

# Campo de COMUNA en SSR
COMUNA_FIELD = "COMUNA" 

# Campo identificador de SHAC en la capa de polígonos
# Colocar el nombre de la variable que se quiere 
# usar al hacer Spatial Join, por ejemplo: "SHAC", "SHAC_NOMBRE", etc.
SHAC_ID_FIELD = "COD_SHAC"

# === 1. Kernel Density ponderado por peso_E1 ===

# Sintaxis correcta:
# KernelDensity(in_point_features, population_field, cell_size, search_radius, area_unit_scale_factor)

kd_raster = KernelDensity(
    uf_path,              # puntos
    PESO_FIELD,           # campo peso
    100,                  # cell size (m)
    5000,                 # search radius (m)
    "SQUARE_KILOMETERS"   # área para normalizar
)

kd_out_path = out_gdb + r"\E1_KD_UF"
kd_raster.save(kd_out_path)

print(f"Raster de Kernel guardado en: {kd_out_path}")


# === 2. Extraer valor de Kernel a cada SSR (kernel_val) ===

KERNEL_FIELD = "kernel_val"

ssr_fields = [f.name for f in arcpy.ListFields(ssr_fc)]
if KERNEL_FIELD not in ssr_fields:
    arcpy.management.AddField(ssr_fc, KERNEL_FIELD, "DOUBLE")
    ssr_fields.append(KERNEL_FIELD)

print("Extrayendo valor de Kernel a cada SSR...")
ExtractMultiValuesToPoints(ssr_fc, [[kd_out_path, KERNEL_FIELD]])

print("Listo: campo 'kernel_val' actualizado en SSR_UTM18S.")



# === 3. Campo indicador de Alta exposición (E1_high) ===

E1_HIGH_FIELD = "E1_high"   # 1 si E1_clas == 4 (Alta), 0 en otro caso

if E1_HIGH_FIELD not in ssr_fields:
    arcpy.management.AddField(ssr_fc, E1_HIGH_FIELD, "SHORT")
    ssr_fields.append(E1_HIGH_FIELD)

print("Marcando SSR con Alta exposición (E1_clas = 4)...")

with arcpy.da.UpdateCursor(ssr_fc, [E1_CLAS_FIELD, E1_HIGH_FIELD]) as cur:
    for e1_clas, e1_high in cur:
        val = 1 if e1_clas == 4 else 0
        cur.updateRow((e1_clas, val))

# === 4. Tablas resumen por COMUNA ===

stats_comuna = out_gdb + r"\E1_stats_comuna"

arcpy.analysis.Statistics(
    in_table=ssr_fc,
    out_table=stats_comuna,
    statistics_fields=[
        [E1_NORM_FIELD, "MEAN"],
        [E1_NORM_FIELD, "MIN"],
        [E1_NORM_FIELD, "MAX"],
        [E1_HIGH_FIELD, "SUM"],    # nº SSR en Alta
        [E1_CLAS_FIELD, "COUNT"]   # nº SSR totales
    ],
    case_field=COMUNA_FIELD
)

print(f"Tabla resumen por COMUNA creada: {stats_comuna}")



# === 5. Spatial Join SSR -> SHAC para incorporar atributo de SHAC ===
# Esto crea una nueva FC con los puntos SSR y el campo del SHAC intersectado.

ssr_shac_fc = out_gdb + r"\SSR_E1_con_SHAC"

print("Haciendo Spatial Join SSR -> SHAC (INTERSECT)...")

arcpy.analysis.SpatialJoin(
    target_features=ssr_fc,
    join_features=shac_fc,
    out_feature_class=ssr_shac_fc,
    join_operation="JOIN_ONE_TO_ONE",
    join_type="KEEP_ALL",        # mantiene SSR sin SHAC (serán SHAC_ID NULL)
    match_option="INTERSECT"
)

print(f"Feature class SSR+SHAC creada: {ssr_shac_fc}")


# === 6. Tablas resumen por SHAC ===
# Usamos el campo ID del SHAC que se colocó, de la FC resultante (SSR_E1_con_SHAC)

stats_shac = out_gdb + r"\E1_stats_shac"

arcpy.analysis.Statistics(
    in_table=ssr_shac_fc,
    out_table=stats_shac,
    statistics_fields=[
        [E1_NORM_FIELD, "MEAN"],
        [E1_NORM_FIELD, "MIN"],
        [E1_NORM_FIELD, "MAX"],
        [E1_HIGH_FIELD, "SUM"],
        [E1_CLAS_FIELD, "COUNT"]
    ],
    case_field=SHAC_ID_FIELD
)

print(f"Tabla resumen por SHAC creada: {stats_shac}")
print("SCRIPT 3 listo: kernel_val + tablas resumen E1 por COMUNA y SHAC.")


