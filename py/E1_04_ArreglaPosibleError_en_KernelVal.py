import arcpy

ssr_fc       = r"C:\ArcGIS_Proyectos\2025\SSR_Chiloe_MOP_BID\Trabajo\Trabajo GIS 01\GIS v02\E1.gdb\SSR_UTM18S"
ssr_shac_fc  = r"C:\ArcGIS_Proyectos\2025\SSR_Chiloe_MOP_BID\Trabajo\Trabajo GIS 01\GIS v02\E1.gdb\SSR_E1_con_SHAC"

def fix_kernel_field(fc):
    fields = [f.name for f in arcpy.ListFields(fc)]
    if "kernel_val_1" not in fields:
        print(f"[{fc}] No existe kernel_val_1, nada que hacer.")
        return

    if "kernel_val" not in fields:
        arcpy.management.AddField(fc, "kernel_val", "DOUBLE")

    print(f"Copiando kernel_val_1 -> kernel_val en {fc}...")
    with arcpy.da.UpdateCursor(fc, ["kernel_val_1", "kernel_val"]) as cur:
        for kv1, kv in cur:
            new_val = kv1 if kv1 is not None else kv
            cur.updateRow((kv1, new_val))

    print(f"Borrando campo kernel_val_1 en {fc}...")
    arcpy.management.DeleteField(fc, ["kernel_val_1"])

    print(f"Listo: {fc} ahora solo tiene 'kernel_val' con valores.")

fix_kernel_field(ssr_fc)
fix_kernel_field(ssr_shac_fc)



