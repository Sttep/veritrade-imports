# Auditoría de Diccionarios y Catálogos — Veritrade Imports
**Fecha:** 2026-07-09
**Fuentes:** `configuracion.xlsx` (hoja "marcas"), `data/vocab_extra.json`, `data/gold/camiones.parquet` (61,160 filas)

---

## Resumen

- **Total hallazgos:** 21

---

### Marca con resultado distinto según pase por reglas (silver) o LLM (gold)
- Estas marcas normalizan distinto según el camino que tome la fila (confianza=ALTA usa reglas, confianza=BAJA pasa por LLM) -- resultado inconsistente para el mismo texto declarado.
- Hallazgos: 10
  - HOMAN: reglas→HOMAN vs LLM→SINOTRUK
  - HOWO: reglas→HOWO vs LLM→SINOTRUK
  - IVECO ASTRA: reglas→IVECO ASTRA vs LLM→IVECO
  - SINOTRUK HOMAN: reglas→SINOTRUK HOMAN vs LLM→SINOTRUK
  - SINOTRUK HOWO: reglas→SINOTRUK HOWO vs LLM→SINOTRUK
  - SINOTRUK SITRAK C7H: reglas→SINOTRUK SITRAK C7H vs LLM→SINOTRUK
  - SINOTRUK WANGPAI: reglas→SINOTRUK WANGPAI vs LLM→SINOTRUK
  - SITRAK: reglas→SITRAK vs LLM→SINOTRUK
  - WACKER: reglas→WACKER vs LLM→WACKER NEUSON
  - WANGPAI: reglas→WANGPAI vs LLM→SINOTRUK

### Bug de precedencia: marca es clave de 'marcas' Y de 'aliases' (el alias nunca se aplica)
- Mismo bug corregido para SINOTRUK/IVECO/PEREYRA en 2026-07-08 -- Vocab.marca_canonica() revisa _marca_idx antes que _alias_idx.
- Hallazgos: 0
- Sin hallazgos

### marca_norm en camiones.parquet ausente de ambos catálogos
- Marcas resueltas 100% por inferencia del LLM, sin ningún catálogo local contra el cual validarlas.
- Hallazgos: 11
  - TLD: 5 filas
  - HUDSON: 4 filas
  - SUMO: 3 filas
  - WEIFANG: 2 filas
  - LTMG: 2 filas
  - SAAO: 2 filas
  - JIV: 1 filas
  - MST: 1 filas
  - ICLES: 1 filas
  - SITON: 1 filas
  - HAMAC: 1 filas

### marca_bruta repetida con distinto marca_normalizada en hoja 'marcas'
- Hallazgos: 0
- Sin hallazgos

### Modelos duplicados dentro de una misma marca en vocab_extra.json
- Hallazgos: 0
- Sin hallazgos

---

## Resumen

| Check | Hallazgos |
|---|---|
| Marca con resultado distinto según pase por reglas (silver) o LLM (gold) | 10 |
| Bug de precedencia: marca es clave de 'marcas' Y de 'aliases' (el alias nunca se aplica) | 0 |
| marca_norm en camiones.parquet ausente de ambos catálogos | 11 |
| marca_bruta repetida con distinto marca_normalizada en hoja 'marcas' | 0 |
| Modelos duplicados dentro de una misma marca en vocab_extra.json | 0 |
