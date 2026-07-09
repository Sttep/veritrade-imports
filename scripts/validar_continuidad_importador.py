"""
scripts/validar_continuidad_importador.py
═══════════════════════════════════════════
Detecta "ceros sospechosos" (mes sin unidades flanqueado por meses con datos)
por importador, para TODAS las marcas relevantes de camiones.parquet — sin
depender de que la cobertura agregada de la marca contra AAP ya haya caído
bajo el umbral de scripts/validar_cobertura.py.

Motivación (feedback del jefe, 9-jul): SINOTRUK está en EXCEPCIONES de
validar_cobertura.py (cobertura agregada ~91% es el techo real, rezago
metodológico esperado) — eso tapa cualquier gap real de un importador puntual
dentro de esa marca (caso Zapler S.A.C., detectado a mano el 2026-07-08, antes
de que existiera este script). detectar_ceros_sospechosos() solo corría hasta
ahora dentro del diagnóstico de validar_cobertura.py, y solo para marcas que
YA habían caído bajo el umbral — este script la aplica siempre, importador
por importador, marca por marca, sin ese filtro previo.

Solo lectura — no modifica ningún parquet/xlsx.

Uso:
  uv run python scripts/validar_continuidad_importador.py
  uv run python scripts/validar_continuidad_importador.py --marca SINOTRUK
  uv run python scripts/validar_continuidad_importador.py --anio 2026 --mes 6
"""
from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

MESES = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
         7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
MESES_ES = {1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
            7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"}

# Marcas con menos volumen en VT que esto no vale la pena chequearlas mes a mes
# (con pocas unidades, cualquier mes en 0 es ruido, no señal).
MIN_UNIDADES_MARCA = 20
# Importadores con menos filas que esto en el período generan el mismo ruido.
MIN_FILAS_IMPORTADOR = 5

# Duplicados de scripts/validar_cobertura.py (NO se importan de ahí para evitar un import
# circular -- ese script ya importa detectar_ceros_sospechosos() de acá). Mismos valores; si
# cambian allá, actualizar acá también.
UMBRAL_GAP_COBERTURA = 88
MIN_UNIDADES_AAP = 5
EXCEPCIONES_COBERTURA = {"HOWO MAX", "SINOTRUK", "RAM", "FORD"}

# Importador+marca ya documentados en informe_auditoria_cobertura.md -- no repetir como
# hallazgo "nuevo" cada corrida (evita ruido de re-descubrir el mismo caso todos los meses).
YA_DOCUMENTADOS = {
    ("HOWO", "ZAPLER S.A.C."): "investigado 2026-07-08 (caso original que motivó este script)",
}


def detectar_ceros_sospechosos(series_mensual: pd.Series) -> bool:
    """Devuelve True si hay meses con 0 flanqueados por meses con datos.

    Extraída de scripts/validar_cobertura.py (2026-07-09) — validar_cobertura.py
    la importa de acá para no duplicar la lógica."""
    vals = list(series_mensual.values)
    for i in range(1, len(vals) - 1):
        if vals[i] == 0 and vals[i - 1] > 0 and vals[i + 1] > 0:
            return True
    return False


def meses_sospechosos(por_mes: pd.Series, meses_periodo: list[int]) -> list[int]:
    """Mismos criterios que detectar_ceros_sospechosos(), pero devuelve CUÁLES meses en vez de
    un booleano -- para poder decirle a alguien exactamente qué mes re-descargar."""
    vals = list(por_mes.values)
    return [meses_periodo[i] for i in range(1, len(vals) - 1)
            if vals[i] == 0 and vals[i - 1] > 0 and vals[i + 1] > 0]


def marcas_ya_cubiertas_por_cobertura(vt_anio: pd.DataFrame, anio: int) -> set[str]:
    """Marcas cuya cobertura agregada vs AAP ya está bajo el umbral de validar_cobertura.py --
    esas marcas ya generan su propio checklist de importadores en la Sección 3 de ese script, no
    hace falta duplicarlo acá. Si no hay aap_camiones.parquet, no filtra nada (todo se reporta).

    OJO: el período de comparación se alinea al último mes con datos en AAP (no al último mes en
    VT, que suele adelantarse a la publicación de AAP) -- comparar VT-hasta-junio contra
    AAP-hasta-mayo infla la cobertura artificialmente porque VT tiene un mes extra que AAP
    todavía no reportó."""
    aap_path = ROOT / "data" / "gold" / "aap_camiones.parquet"
    if not aap_path.exists():
        return set()
    aap = pd.read_parquet(aap_path)
    aap_anio = aap[aap["año"] == anio]
    if aap_anio.empty:
        return set()
    mes_max_aap = int(aap_anio["mes_num"].max())

    aap_per = aap_anio[aap_anio["mes_num"] <= mes_max_aap]
    aap_tot = aap_per.groupby("marca_norm")["unidades"].sum()
    vt_tot = vt_anio[vt_anio["mes"] <= mes_max_aap].groupby("marca_normalizada").size()

    cubiertas = set()
    for marca, aap_n in aap_tot.items():
        if aap_n < MIN_UNIDADES_AAP or marca in EXCEPCIONES_COBERTURA:
            continue
        vt_n = int(vt_tot.get(marca, 0))
        cob = vt_n / aap_n * 100 if aap_n else 0
        if cob < UMBRAL_GAP_COBERTURA:
            cubiertas.add(marca)
    return cubiertas


def _fecha_es(d: date) -> str:
    return f"{d.day} de {MESES_ES[d.month]} de {d.year}"


def escribir_markdown(path: Path, anio: int, mes_max: int, hallazgos: list[dict], n_marcas: int):
    ahora = datetime.now()
    fecha_larga = _fecha_es(ahora.date())
    hora_str = ahora.strftime("%H:%M")

    nuevos = [h for h in hallazgos if h["categoria"] == "nuevo"]
    ya_cubiertos = [h for h in hallazgos if h["categoria"] == "ya_cubierto"]
    ya_conocidos = [h for h in hallazgos if h["categoria"] == "ya_conocido"]
    sin_importador = [h for h in hallazgos if h["categoria"] == "sin_importador"]

    lineas = [
        f"## Continuidad por importador — {fecha_larga} {hora_str}\n",
        f"Período: Ene-{MESES[mes_max]} {anio} · {n_marcas} marca(s) analizadas "
        f"(≥ {MIN_UNIDADES_MARCA} unidades) · {len(hallazgos)} importador(es) con ceros sospechosos.\n",
    ]

    if not nuevos:
        lineas.append("Sin hallazgos nuevos accionables en esta corrida.\n")
    else:
        lineas.append("### Checklist de descarga (nuevo, no visto en corridas anteriores)\n")
        for h in sorted(nuevos, key=lambda h: -h["filas"]):
            accion = (f"meses a revisar: {', '.join(MESES[m] for m in h['meses_accion'])}"
                      if h["meses_accion"] else
                      "solo mes final en 0 -- posible rezago, re-verificar en 2 semanas antes de descargar")
            lineas.append(f"- [ ] **{h['importador']}** ({h['marca']}, {h['filas']} filas) — {accion}")
            lineas.append(f"      {h['detalle']}")
        lineas.append("")

    if ya_cubiertos:
        lineas.append("### Ya cubierto por el checklist de `validar_cobertura.py` (no duplicar)\n")
        for h in ya_cubiertos:
            lineas.append(f"- {h['importador']} ({h['marca']}, {h['filas']} filas) — "
                           f"la marca ya está bajo el umbral de cobertura, su propio checklist la incluye")
        lineas.append("")

    if ya_conocidos:
        lineas.append("### Ya documentado en corridas anteriores\n")
        for h in ya_conocidos:
            razon = YA_DOCUMENTADOS.get((h["marca"], h["importador"]), "")
            lineas.append(f"- {h['importador']} ({h['marca']}, {h['filas']} filas) — {razon}")
        lineas.append("")

    if sin_importador:
        lineas.append("### Hallazgo de calidad de dato aparte (no accionable como descarga)\n")
        for h in sin_importador:
            lineas.append(f"- {h['filas']} fila(s) de **{h['marca']}** con `importador` vacío/nulo "
                           f"en el parquet — no se puede buscar en Veritrade sin nombre, hace falta "
                           f"revisar el dato de origen, no es un gap de cobertura.")
        lineas.append("")

    bloque = "\n" + "\n".join(lineas) + "\n"

    if not path.exists():
        header = f"# Auditoría de Cobertura — Veritrade Imports\n\n---\n{bloque}"
        path.write_text(header, encoding="utf-8")
    else:
        with path.open("a", encoding="utf-8") as f:
            f.write("\n---\n" + bloque)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--marca", help="Filtrar por una marca puntual (substring, sin distinguir mayúsculas)")
    ap.add_argument("--anio", type=int, default=None, help="Año a analizar (default: último en camiones.parquet)")
    ap.add_argument("--mes", type=int, default=None, help="Mes hasta el que analizar (default: último del año elegido)")
    ap.add_argument("--min-unidades-marca", type=int, default=MIN_UNIDADES_MARCA,
                     help=f"Ignorar marcas con menos de N unidades VT en el período (default {MIN_UNIDADES_MARCA})")
    ap.add_argument("--min-filas-importador", type=int, default=MIN_FILAS_IMPORTADOR,
                     help=f"Ignorar importadores con menos de N filas en el período (default {MIN_FILAS_IMPORTADOR})")
    ap.add_argument("--no-markdown", action="store_true",
                     help="No escribir/actualizar informe_auditoria_cobertura.md")
    args = ap.parse_args()

    vt_path = ROOT / "data" / "gold" / "camiones.parquet"
    if not vt_path.exists():
        print("ERROR: no se encontro data/gold/camiones.parquet")
        return 1
    vt = pd.read_parquet(vt_path)

    vt["_dt"] = pd.to_datetime(vt["fecha_dua"], errors="coerce")
    anio = args.anio or int(vt["_dt"].dt.year.max())
    mes_max = args.mes or int(vt[vt["_dt"].dt.year == anio]["_dt"].dt.month.max())
    meses_periodo = list(range(1, mes_max + 1))

    vt_anio = vt[vt["_dt"].dt.year == anio].copy()
    vt_anio["mes"] = vt_anio["_dt"].dt.month
    vt_per = vt_anio[vt_anio["mes"] <= mes_max]

    print(f"\n{'=' * 65}")
    print(f"  CONTINUIDAD POR IMPORTADOR  —  Ene-{MESES[mes_max]} {anio}")
    print(f"{'=' * 65}")
    print("  Corre SIEMPRE, sin depender del umbral de marca de validar_cobertura.py")
    print("  -- asi se detectan gaps de importador ocultos dentro de marcas con")
    print("  EXCEPCIONES (ej. SINOTRUK -- ver esa constante en validar_cobertura.py).\n")

    marca_tot = vt_per.groupby("marca_normalizada").size()
    marcas = sorted(marca_tot[marca_tot >= args.min_unidades_marca].index)
    if args.marca:
        marcas = [m for m in marcas if args.marca.upper() in str(m).upper()]

    if not marcas:
        print("  Ninguna marca cumple el filtro / umbral de volumen.")
        return 0

    marcas_cubiertas = marcas_ya_cubiertas_por_cobertura(vt_anio, anio)

    hallazgos = []
    for marca in marcas:
        sub_marca = vt_per[vt_per["marca_normalizada"] == marca]
        imp_tot = sub_marca.groupby("importador").size()
        importadores = imp_tot[imp_tot >= args.min_filas_importador].sort_values(ascending=False)

        for imp, cnt in importadores.items():
            sub = sub_marca[sub_marca["importador"] == imp]
            por_mes = pd.Series({m: int((sub["mes"] == m).sum()) for m in meses_periodo})
            if not detectar_ceros_sospechosos(por_mes):
                continue

            # importador puede llegar como NaN real o como string literal "nan"/"none" (ya
            # pasó por .astype(str) en algún punto del pipeline) -- tratar ambos como vacío.
            imp_str = "" if pd.isna(imp) or str(imp).strip().upper() in ("NAN", "NONE", "") else str(imp)
            meses_str = " ".join(f"{MESES[m]}={int(por_mes[m])}" for m in meses_periodo)
            meses_accion = meses_sospechosos(por_mes, meses_periodo)

            if not imp_str:
                # Sin importador no se puede buscar en Veritrade -- es un hallazgo de calidad de
                # dato aparte, no una accion de descarga.
                categoria = "sin_importador"
            elif (marca, imp_str) in YA_DOCUMENTADOS:
                categoria = "ya_conocido"
            elif marca in marcas_cubiertas:
                categoria = "ya_cubierto"
            else:
                categoria = "nuevo"

            hallazgos.append({
                "marca": marca, "importador": imp_str, "filas": int(cnt),
                "detalle": meses_str, "meses_accion": meses_accion, "categoria": categoria,
            })

    print(f"  {len(marcas)} marca(s) analizadas (>= {args.min_unidades_marca} unidades en el período).\n")

    if not hallazgos:
        print("  Sin ceros sospechosos en ningun importador del periodo analizado.")
    else:
        print(f"  {len(hallazgos)} importador(es) con ceros sospechosos")
        print("  (mes con 0 unidades flanqueado por meses con datos):\n")
        for h in sorted(hallazgos, key=lambda h: -h["filas"]):
            etiqueta = {"nuevo": "", "ya_cubierto": " [ya cubierto por validar_cobertura.py]",
                        "ya_conocido": " [ya documentado]",
                        "sin_importador": " [sin importador -- no descargable]"}[h["categoria"]]
            print(f"  [ ] {h['marca']:<18} {h['importador'] or '(sin importador)'}"
                  f"  ({h['filas']} filas en el período){etiqueta}")
            print(f"       {h['detalle']}")

    print(f"\n{'=' * 65}")
    print(f"  Parquet: {vt_path.name} | período Ene-{MESES[mes_max]} {anio}")
    print(f"{'=' * 65}\n")

    if not args.no_markdown:
        informe_path = ROOT / "informe_auditoria_cobertura.md"
        escribir_markdown(informe_path, anio, mes_max, hallazgos, len(marcas))
        print(f"  Informe actualizado: {informe_path.name}\n")
    else:
        print("  --no-markdown: no se escribió el informe.\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
