# Cómo están constituidos los agentes de este repo

Este documento complementa a `README.md` (que es el roster: qué hace cada agente y en qué
orden correrlos). Acá está la **anatomía común** a los 8 agentes existentes — el patrón a
seguir para que un agente nuevo arranque tan efectivo como los que ya están probados, en
vez de reinventar la estructura desde cero cada vez.

## 1. Mapa mínimo del proyecto que todo agente necesita

No hace falta que un agente lea todo `CLAUDE.md` — pero sí necesita saber esto de entrada,
porque es lo que determina qué puede tocar y dónde está la fuente de verdad de cada cosa:

```
data/bronze/   .xlsx crudo de Veritrade       (nunca se toca, nunca se versiona)
data/silver/   estructurado por silver.py     (determinístico, no versionado)
data/gold/     *.parquet normalizado          (el único nivel versionado en git;
                                                dedup por DUA+VIN)
configuracion.xlsx      catálogo de marcas/exclusión (fuente de verdad de negocio)
data/vocab_extra.json   extensión del vocabulario para el LLM de gold.py
app.py, pages/2_Camiones.py   dashboard Streamlit que lee data/gold/*.parquet
scripts/validar_*.py, detectar_*.py, auditar_*.py   validadores ya codificados
.beads/ (bd)   issue tracker — decisiones de negocio y bugs pasados quedan citados
                por id (ej. liz-uz5, liz-m7u) en los prompts de los agentes
```

Dos tracks independientes, sin superposición:
- **Datos**: `gatekeeper-datos` (pre-ingestión) → `auditor-datos` (post-ingestión).
- **Dashboard**: `rompe-dashboard`, `consultor-bi`, `ux-no-tecnico`, `ux-propone-mejoras`,
  `diseno-visual`, `jefe-exigente` (secuencia típica documentada en `README.md`).

## 2. Frontmatter

```yaml
---
name: nombre-del-agente
description: Qué hace + explícitamente qué NO hace y quién sí lo hace + cuándo usarlo.
tools: Read, Grep, Glob, Bash
---
```

- **`description` hace doble trabajo**: no es solo para que el orquestador decida cuándo
  invocarlo — es el mecanismo anti-solapamiento del roster. Los 8 agentes existentes tienen
  al menos una frase tipo *"esto no es lo mío, eso lo hace X"* (ej. `diseno-visual`: "no
  layout/copy (eso lo hace ux-propone-mejoras) ni credibilidad ejecutiva (eso lo hace
  jefe-exigente)"). Sin esa frase, dos agentes terminan reportando el mismo hallazgo dos
  veces.
- **`tools` por defecto es de solo lectura**: `Read, Grep, Glob, Bash`. Ningún agente escribe
  código o datos salvo que se lo gatee explícitamente (ver punto 4). Esto es deliberado, no
  un olvido — el default de este repo es "encontrar y reportar", no "arreglar".

## 3. Estructura del cuerpo (patrón que se repite en los 8)

Todos convergen en 3-5 secciones numeradas con este orden lógico:

1. **Fuentes de verdad / punto de partida** — dónde mirar primero, en orden de prioridad, y
   qué hacer si dos fuentes contradicen (normalmente: "señalalo como decisión a confirmar,
   no lo resuelvas por tu cuenta"). Ejemplo: `diseno-visual` ordena
   `guia estructura antes ppt.txt` → constantes ya en código
   (`COLOR_PALETTE`/`pages/2_Camiones.py:34-58`) → paleta de la skill `dataviz` (NO asumida
   como estándar sin confirmar).
2. **Qué mirar / checklist** — el criterio concreto, con comandos exactos o líneas de archivo
   citadas (`archivo:línea`), nunca en abstracto. Ejemplo: `auditor-datos` trae los 6
   comandos `validar_*`/`detectar_*`/`auditar_*` con el orden y el flag
   `PYTHONIOENCODING=utf-8` que hace falta en Windows (`liz-d33`).
3. **Decisiones ya tomadas / ya arreglado — no lo vuelvas a levantar** — esta es la sección
   que más apalanca eficiencia entre sesiones. Cada bug ya resuelto o decisión de negocio ya
   tomada (con su bead id) se documenta acá para que el agente no vuelva a "descubrir" y
   reportar como nuevo algo que ya se decidió. Ejemplo: `auditor-datos` sección 3 documenta
   que `KAMA`/`KAMAZ` NO se consolidan (decisión de negocio 2026-07-08) pero que si
   `SINOTRUK`/`IVECO` aparecen sueltos SÍ es regresión real.
4. **Cómo reportar** — formato de salida y criterio de priorización (volumen/impacto real,
   no solo "existe un caso"), y el recordatorio de nunca modificar nada sin confirmación
   explícita del hallazgo puntual.
5. **(solo si tiene Edit/Write) Gate de edición** — reglas estrictas de cuándo sí puede
   aplicar un cambio: confirmación por propuesta puntual (no por el reporte entero), separar
   cambios mecánicos de cambios de gusto/decisión, y un paso de verificación obligatorio
   post-edición (`diseno-visual` corre `py_compile` + opcionalmente el driver de screenshot
   antes de dar el cambio por terminado).

## 4. La única excepción de escritura: `diseno-visual`

Es el único de los 8 con `Edit, Write` en `tools`. El patrón para justificar esa excepción
(y que sirve de plantilla si en el futuro otro agente necesita escribir) es:
- Superficie acotada explícitamente en el prompt (CSS/HTML inline de 3 archivos puntuales,
  nunca `data/` ni `.parquet`).
- Confirmación por cambio puntual, no blanket approval.
- Paso de verificación obligatorio después de cada edición, documentado en el prompt mismo
  (no delegado a "usa buen criterio").

Si se agrega un agente nuevo con permiso de escritura, repetir esta tríada explícitamente en
su prompt — no asumir que "ya se entiende" del contexto general del repo.

## 5. Cómo agregar un agente nuevo (checklist)

1. Decidir a qué track pertenece (Datos o Dashboard) o si es un track nuevo — si es nuevo,
   documentarlo en `README.md`.
2. Escribir la `description` con la frase explícita de qué NO hace y quién sí lo hace,
   comparando contra los agentes ya existentes del mismo track.
3. `tools` mínimos: arrancar de `Read, Grep, Glob, Bash`; agregar `Edit`/`Write` solo si el
   trabajo es literalmente imposible sin escribir, y en ese caso replicar la tríada del
   punto 4.
4. Cuerpo con las secciones del punto 3, en ese orden. La sección "decisiones ya tomadas" se
   puede arrancar vacía y se va llenando con el tiempo (citando bead id) cada vez que el
   agente reporte algo que el usuario responda "no, eso ya lo decidimos" — así ese mismo
   hallazgo no vuelve a aparecer en la próxima corrida.
5. Actualizar `README.md`: agregar la fila a la tabla del track correspondiente y, si aplica,
   su lugar en la secuencia típica de uso conjunto.
6. Si el agente reemplaza o se superpone con lógica de `scripts/validar_*.py` ya existente,
   no duplicar el check — el agente debe **correr** el script existente, no reimplementar su
   criterio en el prompt (ver `auditor-datos` sección 1: "si vas a agregar un check nuevo...
   no inventes un formato nuevo").

## 6. Por qué esto importa (el objetivo de "ver más y ser más eficientes")

Cada sección del punto 3 existe para evitar que un agente vuelva a pagar el costo de
descubrimiento que ya pagó una sesión anterior: las fuentes de verdad evitan que busque a
ciegas, el checklist con `archivo:línea` evita que re-explore el código para encontrar lo
que ya se sabe dónde está, y "decisiones ya tomadas" evita que vuelva a levantar como
hallazgo algo que el usuario ya resolvió o descartó. Cuantas más veces se corra un agente y
más se actualice su sección 3 con lo aprendido de esa corrida, más barata y más precisa es
la siguiente — ese es el mecanismo concreto de "cada vez ven más cosas y son más
eficientes", no algo que pase solo, hay que alimentarlo a mano después de cada ronda.
