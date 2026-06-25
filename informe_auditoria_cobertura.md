# Auditoría de Cobertura Veritrade vs. AAP
**Fecha:** 25 de junio de 2026
**Período analizado:** Enero – Mayo 2026
**Segmento:** Camiones y Tractocamiones Nuevos – Perú

---

## Objetivo

Validar qué porcentaje del mercado real de camiones captura la base de datos Veritrade, usando como referencia el reporte mensual de la **Asociación Automotriz del Perú (AAP)** — fuente oficial de unidades importadas.

---

## Metodología

1. Carga del reporte AAP (`refs/05-7-importacion-de-vehiculos-livianos-y-pesados-mayo-2026.xlsx`) y extracción de la hoja BASE filtrada por "CAMIONES Y TRACTO" + estado NUEVO.
2. Normalización de marcas en ambas fuentes (consolidación de sub-marcas Sinotruk: HOWO, SITRAK → SINOTRUK; Mercedes Benz → Mercedes-Benz).
3. Cruce por marca y mes entre AAP (unidades) y Veritrade (DUAs).
4. Diagnóstico de brechas y búsqueda de archivos adicionales en Veritrade.
5. Corrección de bug en el pipeline: registros de vehículos **nuevos** con km de fábrica (568–3,911 km) estaban siendo excluidos incorrectamente.

---

## Cobertura global

| | Unidades |
|---|---|
| Mercado total AAP | 12,508 |
| Veritrade inicial | 11,867 (94.9%) |
| Veritrade final | 12,726 (101.7%) |
| DUAs incorporados | +2,162 |

> El 101.7% es esperado: Veritrade captura DUAs de mayo/junio con fecha de registro posterior al cierre del reporte AAP.

---

## Gaps encontrados y resolución

| Marca | Cobertura inicial | Causa raíz | Resolución | Cobertura final |
|---|---|---|---|---|
| **MERCEDES-BENZ** | 36.7% | Tractocamiones Actros/Arocs excluidos por km de fábrica (≥568 km); datos bajo partida 8701210000 no incluida | Fix pipeline + descarga partida 8701210000 + partida 8704230000 | **102.2%** |
| **INTERNATIONAL** | 0% | Misma causa: vehículos nuevos con km excluidos | Fix pipeline | **90.0%** |
| **FREIGHTLINER** | 0% | Misma causa | Fix pipeline | **99.2%** |
| **IVECO** | 72.3% | Modelos TECTOR en partida 8704230000 no descargada; sub-marca IVECO ASTRA separada | Descarga adicional | **83.1%** |
| **VOLKSWAGEN** | 59.7% | Cobertura parcial de EURO MOTORS S.A. en partidas disponibles | Descarga adicional | **68.9%** |
| **HOWO MAX** | 52.9% | Decisión de negocio: registrado como SINOTRUK en Veritrade (importador WITHMORY). No es un gap real | — intencional — | 52.9% (intencional) |

---

## Bug corregido en pipeline

**Archivo:** `pipeline/silver.py` — función `debe_excluir()`

**Problema:** el filtro `km > 200` excluía vehículos nuevos con kilómetros de fábrica o transporte (ruta fábrica–puerto en Europa puede superar 500 km para tractocamiones).

**Fix:** el filtro de km ahora solo aplica cuando `estado ≠ NUEVO`.

```python
# Antes
if km is not None and float(km) > 200:
    return True, f"km={km}"

# Después
if estado not in cfg.estados_nuevos:
    if km is not None and float(km) > 200:
        return True, f"km={km}"
```

**Impacto:** recuperó 455 Mercedes Actros, 650 International y 337 Freightliner que estaban siendo filtrados incorrectamente.

---

## Marcas con cobertura sólida (sin intervención)

ISUZU 100.8% · FUSO 102.4% · VOLVO 100.7% · SHACMAN 99.2% · JAC 99.8% · HINO 107.0% · SINOTRUK 98.1% · SCANIA 113.9% · DONGFENG 99.8% · FOTON 107.2% · FAW 93.1% · JMC 96.8% · FORLAND 100.6% · CAMC 100.0%

---

## Pendientes menores

- **VOLKSWAGEN** (68.9%): ~29 DUAs de EURO MOTORS S.A. sin localizar en partidas disponibles.
- **IVECO** (83.1%): ~11 unidades TECTOR posiblemente en partida 8704221000 no verificada.

---

## Archivos agregados al pipeline

| Archivo | Partida | Período | DUAs nuevos |
|---|---|---|---|
| `Veritrade_...20260625003700.xlsx` | 8701210000 (tractocamiones) | Ene 2025 – May 2026 | +1,231 |
| `Veritrade_...20260625005834.xlsx` | 8704230000 (camiones pesados) | Ene 2025 – May 2026 | +931 |
| **Total** | | | **+2,162** |
