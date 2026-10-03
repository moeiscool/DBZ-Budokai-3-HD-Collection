# MEMORY.md — DBZ Budokai 3 HD Collection (memoria operativa viva)

> Complemento de `AGENTS.md`. **AGENTS.md = referencia estable** (formato,
> constraints, comandos). **MEMORY.md = estado vivo** (qué se hizo, qué está en
> curso, qué falta, y el **protocolo de colaboración con Claude**). Actualizar
> este fichero al cerrar cada sesión; no duplicar aquí lo que ya está en AGENTS.

Última actualización: **2026-10-03** (RE del skinning Vía B + handoff a Claude).

---

## 0. PROTOCOLO DE MIGRACIÓN TEMPORAL A CLAUDE (LEER PRIMERO)

El mantenedor trabaja alternando **opencode** (local, este repo) y **Claude**
(migración temporal). El repo canónico es **este disco**; `github/` es la copia
versionable (sync manual con `tools/sync_github.ps1`).

### 0.1 Regla de oro
**Todo cambio que haga Claude debe volver a este disco como UN `.md` de
"handback"**. Claude **no** sube a GitHub. El mantenedor revisa el `.md` aquí y
aplica/sube desde opencode.

### 0.2 Al **entregar** el proyecto a Claude (lo que hace opencode)
1. Asegurar `git -C github status` limpio y commit local hecho (aunque no se suba).
2. Entregar: `AGENTS.md`, `MEMORY.md`, `docs/MIGRACION_CLAUDE.md` y el estado de
   `github/` (branch + commits ahead).
3. Indicar a Claude el **alcance exacto** de la sesión (p.ej. "RE rutina CPU de
   skinning") y pedirle el handback (§0.3).

### 0.3 Al **recibir** de Claude (instrucción a Claude, copiar tal cual)
> **INSTRUCCIÓN OBLIGATORIA PARA CLAUDE**: al terminar tu trabajo, genera **un
> único fichero Markdown** llamado `HANDOFF_CLAUDE_<AAAA-MM-DD>_<tema>.md` con:
> 1. **Resumen** de lo hecho (qué, para qué).
> 2. **Lista EXACTA de ficheros** creados/modificados/borrados (rutas relativas al
>    repo) y, por cada uno, **qué cambia** (idealmente un `diff` unificado o el
>    contenido completo si es nuevo).
> 3. **Comandos** que ejecutaste y su resultado (build/tests).
> 4. **Qué NO pudiste hacer** o quedó a medias + riesgos/suposiciones.
> 5. **Siguiente paso recomendado**.
> - **NO** hagas push a GitHub. **NO** reescribas `AGENTS.md`/`MEMORY.md` salvo que
>   esta memoria lo pida explícitamente; en su lugar, propón el cambio en el
>   handback. Entrega ese `.md` como único artefacto accionable.
> - Usa rutas relativas y evita datos personales (rutas `C:\Users\...`).

### 0.4 Al **volver** de Claude a opencode (lo que hace opencode)
1. Leer el `HANDOFF_CLAUDE_*.md`, aplicar los diffs/ficheros indicados.
2. Actualizar `MEMORY.md` (esta sección + §2) y, si aplica, `AGENTS.md`.
3. `powershell -ExecutionPolicy Bypass -File tools\sync_github.ps1` (corre
   `publish_check.ps1`; exit 1 = fallo) → commit → **push solo si el mantenedor lo pide**.

---

## 1. ESTADO VIVO (2026-10-03)

### 1.1 Git
- Repo versionable: `github/` (NO es el repo de trabajo; se sincroniza manual).
- **`master` ahead 10** respecto a `origin/master`; **sin push** (esperar OK del usuario).
- Últimos commits locales: `f753948` (RE skinning), `a30c8ac` (publish_check),
  `5fc4821` (Vía A + fix normales), `7c2fd6c`, `0394903`.
- Entorno de build limpio: sin procesos, toml sin flags dev, DLLs canónicas
  (`rexgpu-xenos.dll` 6360064 B / `rexruntime.dll` 10920448 B).

### 1.2 Releases
- **v1.3.0 = Latest** (2026-09-30). Todo lo demás no-Latest (ver AGENTS §3.0/§9.2).

### 1.3 Vía A (inyección PS2→HD) — entrega aproximada
- Funciona; mejor resultado `cell_win2`.
- **Defecto brazo/cabeza = sombreado de geometría aproximada** (NO bug de
  rotación de normales). §23.
- **Fix de normales**: `awo_tools/awg_normal_fix.py` (copia `nrm` nativo HD sobre
  el bin del port). Mod `cell_nfix` validado en runtime (demo limpia). §23.1.
- Comparador: `awo_tools/awg_diff.py`.

### 1.4 Vía B (port completo) — 🔴 DESBLOQUEO DIAGNÓSTICO 2026-10-03
- **RE del skinning (nuevo, §24)**: se instrumentó `rexgpu-xenos` (REVERTIDO) y
  se volcaron shaders + constantes por draw. Resultado **duro**:
  - **Ningún VS indexa constantes dinámicamente** (sin `a0`/`arl`/`lc`) → **sin
    paleta de huesos en GPU**.
  - **Ningún shader usa `memexport`** → sin skinning GPU/“compute”.
  - El VS del cuerpo (`FDF960B5D7869030`) es **transform rígida** con **una sola
    matriz 4×4 en `c0..c3`**, **idéntica** en los ~33 chunks (`indx_offset=0`,
    counts 3..1995).
  - ⇒ **El skinning es CPU-side (Xenon)**: el guest lee bind-pose, aplica
    matrices de hueso y escribe **world-space**; el VS solo proyecta.
  - **Refuta la hipótesis "causa = shader de skinning"** (§3.4.6/§10 y §22).
- **Nuevo foco**: RE de la **rutina CPU de skinning en el código recompilado**
  (qué espacio/orden de vértices espera el guest). Ver §2 "SIGUIENTE".

### 1.5 Bloque C (lint pre-release)
- `tools/publish_check.ps1` (reimpl. de `um publish check`): FAIL por ficheros de
  juego/build/secretos; WARN por huellas de decompilador, rutas personales, sin
  README. Integrado al final de `tools/sync_github.ps1`. Auto-excluye su propio
  fichero. Estado: **PASS (44 WARN, 0 FAIL)** sobre `github/`.

---

## 2. SIGUIENTE (prioridad)

1. **RE de la rutina CPU de skinning** (Vía B) — el bloqueo real. Localizar en
   `generated/` (US) / `generated_eu/` (EU) el código que lee los vértices del
   bin y aplica matrices de hueso; determinar el **espacio/orden** esperado
   (bind-pose por hueso). Candidato histórico: `sub_82087F58` (AGENTS §3.4.10).
   - Medida auxiliar: volcar el **VB final world-space** del draw del cuerpo
     (no el bin) para comparar port vs nativo en el mismo frame/pose.
2. **Decidir `cell_nfix`** (adoptar como mejora Vía A reproducible vs dejarlo en
   línea de trabajo).
3. **Push** de los 10 commits locales (espera OK del mantenedor).
4. Vía A opcional: refinar inyección (`--bone-aware`/`--normal-only` por zona).

---

## 3. NO REPETIR / TRAMPAS (derivadas de esta sesión)

- La hipótesis "el problema del port es el shader de skinning" está **REFUTADA**
  (§24). No volver a RE del shader para Vía B.
- `dump_shaders` (cvar) vuelca el ucode **bin + disasm**; `DumpUcode` ya está
  cableado en `translator.cpp:340` (no hace falta cablearlo).
- El game NO avanza de pantalla con `PostMessage` (falta `has_focus_`). Para
  navegar: ventana **visible + `SetForegroundWindow` + `keybd_event` real**
  (`SendInput`); con `long_run.ps1` la ventana va oculta → los Return no entran.
- Los logs de captura por draw pueden ser **cientos de MB** (656–730 MB);
  leerlos **en streaming** (`Select-String -Context`), nunca con arrays completos.
- Cualquier instrumentación del SDK se **revierte** y se recopian las DLLs
  canónicas (`tools\copy_sdk_dlls.ps1`); verificar tamaño (6360064 / 10920448).

---

## 4. REFERENCIAS CLAVE
- `AGENTS.md` — referencia operativa completa (formato, comandos, invariantes).
- `docs/MIGRACION_CLAUDE.md` — handoff detallado + plantilla de handback.
- `docs/07_ports/SESION_DRAW_SEMANTICS_2026-09-11.md` — §21 (oráculo), §22 (VB
  runtime), §23/§23.1 (Vía A + fix normales), **§24 (RE skinning, nueva)**.
- `docs/07_ports/UNIVERSAL_MODDER_2026-09-30.md` — origen del Bloque C.
- `docs/RE_MASTER_2026_09.md`, `docs/HOJA_DE_RUTA_2026_09.md`.
