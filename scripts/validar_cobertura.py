"""
scripts/validar_cobertura.py
════════════════════════════
Validación mensual de cobertura Veritrade vs AAP.

Detecta automáticamente:
  - Marcas con brecha (< umbral)
  - Importadores conocidos en VT para esa marca
  - Si la brecha se explica por importador incompleto o partida desconocida
  - Genera checklist de descargas accionables

Uso:
  python scripts/validar_cobertura.py
  python scripts/validar_cobertura.py --mes 6 --anio 2026
  python scripts/validar_cobertura.py --umbral 88
"""
from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

# ── Umbrales ──────────────────────────────────────────────────────────────────
UMBRAL_OK    = 95   # >= OK, sin acción
UMBRAL_LEVE  = 88   # 88-94 → revisar / rezago normal
UMBRAL_GAP   = 88   # < 88 → acción requerida

# Excepciones permanentes: marcas cuya cobertura baja es esperada y documentada
EXCEPCIONES = {
    "HOWO MAX":    "WITHMORY declara como SINOTRUK en aduana — no es gap real",
    "SINOTRUK":    "Rezago metodológico AAP(MTC) vs VT(DUA) — ~91% es el techo real",
    "RAM":         "Vehículos de rescate/bomberos (8705300000) — baja relevancia comercial",
    "FORD":        "1 unidad histórica — insignificante",
}

# Mínimo de unidades AAP para considerar la marca en el análisis
MIN_UNIDADES_AAP = 5

# Meses con nombre para el reporte
MESES = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",
         6:"Jun",7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def detectar_ceros_sospechosos(series_mensual: pd.Series) -> bool:
    """Devuelve True si hay meses con 0 flanqueados por meses con datos."""
    vals = list(series_mensual.values)
    for i in range(1, len(vals) - 1):
        if vals[i] == 0 and vals[i-1] > 0 and vals[i+1] > 0:
            return True
    return False


def importadores_conocidos(vt_per: pd.DataFrame, marca: str, top_n: int = 8) -> pd.DataFrame:
    """Devuelve los importadores conocidos para una marca, con conteo mensual."""
    sub = vt_per[vt_per["marca_normalizada"] == marca].copy()
    if sub.empty:
        return pd.DataFrame()
    by_imp = sub.groupby("importador").size().sort_values(ascending=False).head(top_n)
    return by_imp


def resumen_mensual_vt(vt_per: pd.DataFrame, marca: str, meses: list[int]) -> dict:
    sub = vt_per[vt_per["marca_normalizada"] == marca]
    return {m: int((sub["mes"] == m).sum()) for m in meses}


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mes",    type=int, default=None, help="Mes hasta el que analizar (default: último en AAP)")
    ap.add_argument("--anio",   type=int, default=None, help="Año a analizar (default: último en AAP)")
    ap.add_argument("--umbral", type=int, default=UMBRAL_GAP, help="Umbral %% para acción (default: 88)")
    args = ap.parse_args()

    # ── Cargar datos ──────────────────────────────────────────────────────────
    aap_path = ROOT / "data" / "gold" / "aap_camiones.parquet"
    vt_path  = ROOT / "data" / "gold" / "camiones.parquet"

    if not aap_path.exists():
        print("ERROR: no se encontro data/gold/aap_camiones.parquet")
        print("Ejecuta: python pipeline/aap.py")
        return 1
    if not vt_path.exists():
        print("ERROR: no se encontro data/gold/camiones.parquet")
        return 1

    aap = pd.read_parquet(aap_path)
    vt  = pd.read_parquet(vt_path)

    # Detectar año y mes máximo en AAP
    anio_max = args.anio or int(aap["año"].max())
    mes_max  = args.mes  or int(aap[aap["año"] == anio_max]["mes_num"].max())
    umbral   = args.umbral

    print(f"\n{'='*65}")
    print(f"  VALIDACION DE COBERTURA  —  Ene–{MESES[mes_max]} {anio_max}")
    print(f"{'='*65}")
    print(f"  Umbral de accion: < {umbral}%  |  Excepciones: {len(EXCEPCIONES)} marcas\n")

    # ── Filtrar al período ────────────────────────────────────────────────────
    aap_per = aap[(aap["año"] == anio_max) & (aap["mes_num"] <= mes_max)]

    vt["_dt"] = pd.to_datetime(vt["fecha_dua"], errors="coerce")
    vt_per = vt[(vt["_dt"].dt.year == anio_max) & (vt["_dt"].dt.month <= mes_max)].copy()
    vt_per["mes"] = vt_per["_dt"].dt.month

    meses_periodo = list(range(1, mes_max + 1))

    # ── Calcular cobertura por marca ──────────────────────────────────────────
    aap_tot = aap_per.groupby("marca_norm")["unidades"].sum()
    vt_tot  = vt_per.groupby("marca_normalizada").size()

    marcas_aap = set(aap_tot[aap_tot >= MIN_UNIDADES_AAP].index)

    resultados = []
    for marca in sorted(marcas_aap):
        aap_n = int(aap_tot.get(marca, 0))
        vt_n  = int(vt_tot.get(marca, 0))
        cob   = vt_n / aap_n * 100 if aap_n > 0 else 0
        resultados.append({"marca": marca, "aap": aap_n, "vt": vt_n, "cob": cob})

    df_res = pd.DataFrame(resultados).sort_values("aap", ascending=False)

    # ── Sección 1: Resumen global ──────────────────────────────────────────────
    total_aap = df_res["aap"].sum()
    total_vt  = df_res["vt"].sum()
    cob_global = total_vt / total_aap * 100

    print(f"  {'Marca':<22} {'AAP':>6} {'VT':>6} {'Cob%':>7}  Estado")
    print(f"  {'-'*58}")
    for _, r in df_res.iterrows():
        if r["marca"] in EXCEPCIONES:
            estado = f"excepcion ({r['cob']:.0f}%)"
        elif r["cob"] >= UMBRAL_OK:
            estado = "OK"
        elif r["cob"] >= UMBRAL_LEVE:
            estado = "leve"
        else:
            estado = "<<< ACCION REQUERIDA"
        print(f"  {r['marca']:<22} {r['aap']:>6} {r['vt']:>6} {r['cob']:>6.1f}%  {estado}")
    print(f"  {'-'*58}")
    print(f"  {'GLOBAL':<22} {total_aap:>6} {total_vt:>6} {cob_global:>6.1f}%")

    # ── Sección 2: Marcas con brecha → diagnóstico automático ─────────────────
    marcas_gap = df_res[
        (df_res["cob"] < umbral) & (~df_res["marca"].isin(EXCEPCIONES))
    ]

    if marcas_gap.empty:
        print(f"\n  Todas las marcas estan dentro del umbral ({umbral}%). Sin accion requerida.")
    else:
        print(f"\n{'='*65}")
        print(f"  DIAGNOSTICO — {len(marcas_gap)} marca(s) con cobertura < {umbral}%")
        print(f"{'='*65}")

        descargas_importador = []  # (importador, marca, razon)
        sin_datos_vt = []

        for _, r in marcas_gap.iterrows():
            marca = r["marca"]
            aap_n = r["aap"]
            vt_n  = r["vt"]
            cob   = r["cob"]
            brecha = aap_n - vt_n

            print(f"\n  [{marca}]  AAP={aap_n}  VT={vt_n}  Cobertura={cob:.1f}%  Brecha=-{brecha}")

            imps = importadores_conocidos(vt_per, marca)

            if imps.empty:
                # Marca sin ningún registro en VT → partida desconocida
                print("    DIAGNOSTICO: marca sin ningun registro en VT.")
                print("    Causa probable: partida arancelaria no descargada.")
                print("    Accion: buscar en Veritrade por nombre de marca o")
                print("            consultar con el importador para identificar partida.")
                sin_datos_vt.append(marca)
            else:
                print("    Importadores conocidos en VT:")

                tiene_ceros_sospechosos = False
                for imp, cnt in imps.items():
                    # Breakdown mensual por importador
                    sub = vt_per[
                        (vt_per["marca_normalizada"] == marca) &
                        (vt_per["importador"] == imp)
                    ]
                    por_mes = pd.Series(
                        {m: int((sub["mes"] == m).sum()) for m in meses_periodo}
                    )
                    ceros = detectar_ceros_sospechosos(por_mes)
                    meses_str = " ".join(
                        f"{MESES[m]}={int(por_mes[m])}" for m in meses_periodo
                    )
                    flag = " <-- CEROS SOSPECHOSOS" if ceros else ""
                    print(f"      {cnt:>4}  {imp}")
                    print(f"            {meses_str}{flag}")

                    if ceros:
                        tiene_ceros_sospechosos = True
                        descargas_importador.append((imp, marca,
                            "ceros sospechosos en meses intermedios"))

                # Evaluar si la brecha puede ser partida desconocida
                vt_mes = resumen_mensual_vt(vt_per, marca, meses_periodo)
                aap_mes = {
                    m: int(aap_per[aap_per["mes_num"]==m]["unidades"][
                        aap_per["marca_norm"]==marca
                    ].sum() if not aap_per[
                        (aap_per["marca_norm"]==marca) & (aap_per["mes_num"]==m)
                    ].empty else 0)
                    for m in meses_periodo
                }

                # Si la brecha es persistente en todos los meses → posible partida
                meses_con_brecha = sum(
                    1 for m in meses_periodo
                    if aap_mes.get(m,0) > 0 and vt_mes.get(m,0) < aap_mes.get(m,0) * 0.8
                )

                if not tiene_ceros_sospechosos and meses_con_brecha >= len(meses_periodo) // 2:
                    print(f"    DIAGNOSTICO: brecha persistente y uniforme en {meses_con_brecha}/{len(meses_periodo)} meses.")
                    print("    Importadores conocidos parecen completos (sin ceros sospechosos).")
                    print("    Causa probable: partida arancelaria no cubierta o rezago metodologico.")
                    # Check partidas used
                    partidas_usadas = vt_per[vt_per["marca_normalizada"]==marca]["partida"].value_counts()
                    print(f"    Partidas actuales en VT: {dict(partidas_usadas.head(5))}")
                elif tiene_ceros_sospechosos:
                    print("    DIAGNOSTICO: importadores con meses sin datos.")
                    print("    Accion: descargar por nombre de importador (ver lista arriba).")
                else:
                    print("    DIAGNOSTICO: brecha leve — posible rezago de DUAs recientes.")
                    print("    Accion: re-verificar en 2 semanas antes de descargar.")

        # ── Sección 3: Checklist de descargas ─────────────────────────────────
        print(f"\n{'='*65}")
        print("  CHECKLIST DE DESCARGAS")
        print(f"{'='*65}")

        if descargas_importador:
            print("\n  POR IMPORTADOR (prioridad alta — ceros sospechosos detectados):")
            seen = set()
            for imp, marca, razon in descargas_importador:
                if imp not in seen:
                    print(f"  [ ] Veritrade → Importador: '{imp}'")
                    print(f"      Marca afectada: {marca} | Razon: {razon}")
                    seen.add(imp)
        else:
            print("\n  No se requieren descargas por importador.")

        if sin_datos_vt:
            print("\n  MARCAS SIN DATOS EN VT (investigar partida):")
            for marca in sin_datos_vt:
                print(f"  [ ] Investigar partida para: {marca}")
                print("      Sugerencia: buscar en Veritrade por nombre de importador conocido")

        if not descargas_importador and not sin_datos_vt:
            print("\n  Las brechas detectadas son probablemente rezago metodologico.")
            print("  Recomendacion: re-verificar en 2 semanas.")

    # ── Sección 4: Auto-tabla importadores por marca ───────────────────────────
    print(f"\n{'='*65}")
    print("  IMPORTADORES CONOCIDOS POR MARCA (derivado del parquet actual)")
    print("  Usar como referencia para descargas futuras")
    print(f"{'='*65}")

    marcas_relevantes = df_res[df_res["aap"] >= 30]["marca"].tolist()
    for marca in marcas_relevantes:
        imps = importadores_conocidos(vt_per, marca, top_n=3)
        if not imps.empty:
            imp_list = ", ".join(f"{imp}({n})" for imp, n in imps.items())
            print(f"  {marca:<22} {imp_list}")

    print(f"\n{'='*65}")
    print(f"  Parquet: {vt_path.name} | {len(vt):,} filas totales")
    print(f"  AAP ref: {aap_path.name} | periodo Ene-{MESES[mes_max]} {anio_max}")
    print(f"{'='*65}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
