# Viabilidad de upscaling temporal en dbz3 (DLSS / DLAA / FSR3 / Frame Gen)

> Investigación 2026-09-29, a raíz de dos recompilaciones hermanas:
> [`zolaware/reblue`](https://github.com/zolaware/reblue) (Blue Dragon) y
> [`freefrank/LostOdysseyRecomp`](https://github.com/freefrank/LostOdysseyRecomp).
> **Conclusión corta**: DLSS/DLAA/FSR3 temporal/Frame Gen **no son viables hoy**
> en dbz3 sin construir el contrato temporal (color a resolución interna + depth
> + motion vectors + jitter) y, en la práctica, sin disponer de la capa GPU. Lo
> que sí es aprovechable de esos repos ya se ha adoptado (DRED +
> gamecontrollerdb) o queda como candidato (§6).

## 1. Base de cada proyecto (por qué no es una comparación 1:1)

| | dbz3 (este proyecto) | reblue | LostOdysseyRecomp |
|---|---|---|---|
| Recompilador | ReXGlue 0.10 | **ReXGlue 0.10** | XenonRecomp + XenosRecomp |
| Capa GPU | `rexgpu-xenos.dll` (Xenia), **no propia** | **propia** (`src/gpu/*`, fork de `plume`) | **propia** (`gpu/*`, `plume`) |
| DLSS / DLAA | — | — | **Sí** (NGX 310.9.1: SR + DLAA) |
| FSR | **FSR1** espacial (EASU/RCAS) + CAS en el presentador | — (solo MSAA/SSAA) | FSR 3.1 (upscaler) **+ FSR Frame Gen** |
| Frame Gen | — | — | DLSS-G (Streamline) + FSR FG, **diferido** |
| TAA propio | — | — | experimental |

**Dato clave**: reblue arranca del **mismo SDK que dbz3** (`reblue_manifest.toml`
→ `sdk_version = "0.10.0"`, `REXCVAR_*`, `rexglue_setup_target`) pero **sustituye
el plugin GPU** (`rexglue_setup_target(<target> [GPU_PLUGINS xenos])`): usa su
propio `src/gpu/` sobre `plume`. Eso es lo que le permite MSAA/SSAA "de verdad",
`render_scale` por debajo del 100 % y hooks de resolución de salida. **No es un
flag de configuración: es otra capa de render.**

LostOdysseyRecomp ni siquiera usa ReXGlue: es XenonRecomp/XenosRecomp + plume
(la línea de UnleashedRecomp). Es el que tiene el pipeline temporal completo, pero
sobre una GPU propia.

## 2. Por qué FSR1 sí funciona en dbz3 y FSR3/DLSS no

- **Lo que tenemos hoy**: `rexglue-sdk-0.10/src/ui/presenter.cpp` aplica
  **FSR1 espacial** (`guest_output_ffx_fsr_easu_ps` + `..._rcas_ps`) y **CAS**
  (`guest_output_ffx_cas_*`) sobre la imagen ya resuelta del guest. Es un filtro
  **espacial de un solo frame**: no necesita depth, ni movimiento, ni jitter.
- **Lo que exige un upscaler temporal** (FSR3/DLSS/DLAA/FG): color a **resolución
  de render** (no presentación), **depth** de la misma pasada, **motion vectors**
  con signo convencional (pasado←presente, en píxeles de render), **jitter** de
  cámara no aplicado a la UI/sombras/motion, y metadatos de color-exposición.
  Nada de eso lo entrega hoy el presentador: solo recibe la imagen final con la
  UI ya compuesta.
- **El FFX SDK presente incluye FSR3/FG**, pero el build los deja fuera:
  `rexglue-sdk-0.10/cmake/rexglue_fidelityfx.cmake` fuerza
  `FFX_API_ENABLE_FRAMEGEN_PROVIDER OFF` y solo se empaquetan los shaders FSR1
  EASU/RCAS + CAS. Habilitar FSR3 exigiría, además del SDK, los inputs de arriba.
- **Ya hay un stub temporal en el SDK, pero degradado a espacial**: el código
  `DispatchTemporalUpscaler` existe en `src/ui/d3d12/d3d12_presenter.cpp` /
  `vulkan_presenter.cpp`, pero por frame hace `reset=true`, pasa el color como
  depth **y** como motion vectors con `jitter=0` (el propio `presenter.cpp` lo
  advierte). `present_fsr_quality_mode` (FSR2/3) solo alimenta esa ruta, por eso
  el launcher lo mantiene oculto. Base previa: `ANALISIS_ESCALADO_RENDIMIENTO_2026-09-14.md`.

## 3. Lo que documenta LostOdysseyRecomp (la lección más valiosa)

Su `docs/notes/temporal-upscaling-feasibility.md` es, literalmente, el plan de lo
que nos tocaría. Puntos que aplican tal cual a dbz3:

- Poseer los shaders traducidos, el dispatch de draws, las superficies de depth y
  las command lists **es condición necesaria**; dbz3 **no** las posee (viven
  dentro de `rexgpu-xenos.dll`).
- Un filtro **post-presentación** "tiene un contrato sustancialmente más débil":
  no puede dar depth/objeto-movimiento/jitter fiables.
- **"Optical flow y vectores a cero no son motion vectors nativos"**: etiquetarlos
  como tal está prohibido en su propio criterio de aceptación.
- **Riesgo #1 = fronteras escena/UI y movimiento de objeto/skin**. En sus palabras:
  "una vez demostrado, el adaptador D3D12 del SDK es costo moderado; la
  incertidumbre alta es la identidad/historia de objeto y la frontera escena/UI,
  que **requieren RE específico del juego**; ningún DLL ni flag de post-proceso
  recupera su semántica".
- Su estado real (2026-09-27): DLSS SR ejecutando en RTX 5080 (Quality
  `1707x960 -> 2560x1440`), pero **Gate 3 no aprobado**, sin aceptación visual,
  **Frame Gen diferido** y **redistribución de NGX sin resolver** (licencia
  propietaria). Es decir: incluso con la capa GPU propia, es un proyecto de meses
  y todavía experimental.

**Para dbz3 esto se traduce en**: hacer DLSS/FG implicaría (a) exponer
color/depth/MV desde `rexgpu-xenos`, con RE del guest para la identidad de
objeto/skin, o (b) reemplazar el backend GPU por uno propio tipo `plume` (lo que
hizo reblue). Ninguna de las dos es "integrar una librería".

## 4. Contrato temporal que habría que construir (si algún día se retoma)

1. **Frontera escena/UI**: identificar el resolve de escena (color+depth) y el
   primer draw de UI posterior, por frame y por familia de escena.
2. **Depth y proyección**: depth de la misma pasada, convención (dbz3 usa
   reversed-Z en el guest), near/far, y reproyección con la cámara.
3. **Movimiento**: un campo de movimiento **hacia atrás** en píxeles de render.
   Cámara sola = solo geometría estática; hace falta movimiento de huesos/skin.
4. **Jitter**: desplazamiento de sub-píxel **solo** a la escena; nunca a UI,
   clears, sombras ni full-screen triangles.
5. **Color/exposición**: distinguir escena HDR/SDR y pre-exposición antes de
   derivar constantes del SDK.
6. **Resolución interna**: renderizar la escena a la resolución interna del modo
   (Quality/Balanced/Performance) y redimensionar consistentemente viewports,
   scissors, resolves y constantes de espacio de pantalla.

## 5. Lo que SÍ se puede hacer con lo que ya hay (sin tocar la GPU)

- **FSR1 + CAS** (ya presente): el upscaling espacial de salida y la nitidez.
- **`draw_resolution_scale`**: supersampling real del guest (2x/3x). Coste real
  medido: 3x ≈ 51 % GPU vs 1x+FSR ≈ 22 %. Por eso `1x` es el default.
- **FXAA/dither** (`swap_post_effect`, `dbz3_present_dither`).
- **Texturas HD** (`dbz3_hd_textures`) como palanca de nitidez sin coste temporal.

## 6. Aprendizajes de reblue adoptables en dbz3

**Ya adoptado (2026-09-29):**
- **DRED desacoplado de la capa debug**: cvar `d3d12_dred` (ON por defecto). El
  reporte de *device lost* nombra la queue/list (breadcrumbs) y las allocation
  nodes del page fault. Ver `github/patches/README.md` §2026-09-29.
- **`gamecontrollerdb.txt`** enviado junto al exe (el runtime ya tiene la cvar
  `hid_mappings_file`): el backend SDL reconoce mandos genéricos.

**Ya adoptado (2026-09-30, QoL del launcher — solo host):**
- **Etiquetas de botón (glyphs)**: cvar `dbz3_input_glyphs` (Xbox / PlayStation /
  Switch). La pestaña **Controles** cambia los nombres junto a cada keybind
  (`LT` vs `L2` vs `ZL`, `D-Pad Up`, `LS-Up`, ...) usando el helper
  `ButtonGlyph()` de `src/launcher/launcher_state.cpp`. Es solo cosmético: **no
  toca el mapeo del runtime** (a diferencia del glyph set de reblue, que
  reescribe bloques de una hoja DDS del guest vía hooks).
- **"Reparar instalación"** (`dbz3::settings::RepairInstallation()`): botón en el
  pie del launcher y bandera de un solo uso `dbz3_repair` (CLI
  `--dbz3_repair=true` / `REX_DBZ3_REPAIR=1`) que reabre el launcher y muestra un
  informe en un popup. Pone en cuarentena un `dbz3_user.toml` ilegible
  (`*.invalid`) y reescribe ajustes limpios, verifica `rexruntime.dll`,
  `rexgpu-xenos.dll`, `amd_fidelityfx_dx12.dll` y `gamecontrollerdb.txt`, y
  asegura la carpeta de datos de usuario. **No toca `us/eu/`, `mods/` ni las
  cachés.** Validado en runtime (uno de los informes dejó el `.invalid` de un
  toml roto y regeneró el bueno).

**Descartado (con motivo):**
- **PSO precache/predictor/recorder** (reblue `src/gpu/pipeline/pso_*`): el
  predictor y la disciplina de precache son agnósticos, pero el *build* de cada
  PSO depende de **plume** (`RenderGraphicsPipelineDesc`,
  `CreateHostGraphicsPipeline`). Contra `rexgpu-xenos` (Xenia) habría que
  reimplementar `Build` y el formato de caché; no es una tarea de launcher.
- **Hooks de resolución de salida** (reblue `src/gpu/hooks/output.cpp`): RE de
  guest con direcciones concretas de Blue Dragon (`0x82DDA670`, viewports,
  `VisualRender::ctor`, ...). No aplica a DBZ3; exigiría localizar los
  equivalentes del motor de Budokai (investigación, no QoL).
- **`frame_interp`** (reblue `src/engine/frame_interp.cpp`, 3.000+ líneas):
  desacopla render de la simulación a 30 Hz del guest con decenas de gates.
  Es RE de guest por juego; DBZ3 ya corre a 60 Hz fijos.
- **Idioma de UI vs voces**: reblue separa `bd_language` (`user_language`, boot)
  de `bd_opt_voice_type` (opción in-game contra `[Voice]` de `bd_boot.ini`). En
  DBZ3 el idioma de texto ya se controla (`dbz3_language`); el de voces vive en
  el motor del guest y requeriría localizar su opción (RE).
- **Perfiles**: reblue usa un directorio por perfil (`profiles/<name>` con su
  toml/saves/mods). Nuestro launcher ya tiene perfiles **de mods**
  (`dbz3_mod_profile` + `mods/profiles.txt`); un sistema de perfiles de ajustes
  completo es un rediseño de datos, no una mejora de un día.

**Candidatos siguientes (coste medio, sin rehacer la GPU):**
- **PSO precache adaptado a Xenia** (solo si se decide tocar `rexgpu-xenos`).
- **Perfiles de ajustes** (snapshots con nombre del `dbz3_user.toml`).

## 7. Riesgos y licencias

- **NVIDIA NGX/DLSS**: SDK propietario; LostOdysseyRecomp deja la redistribución
  de `nvngx_dlss.dll` **sin resolver**. No empaquetar sin resolverlo.
- **FSR**: redistribuible bajo la licencia del AMD FSR/FidelityFX SDK (ya
  embarcamos `amd_fidelityfx_dx12.dll`).
- **Código de terceros**: reblue es **BSD-3-Clause**, LostOdysseyRecomp es
  **GPLv3**. Si se reutiliza código, respetar licencia y atribución.
- **GameControllerDB**: zlib (https://github.com/mdqinc/SDL_GameControllerDB).

## 8. Recomendación

Mantener la estrategia **espacial** (FSR1/CAS/FXAA + escala interna + texturas HD)
como entrega. Tratar el upscaling temporal como **investigación acotada** con las
fases de §4, y **solo** retomarlo si se decide (a) instrumentar `rexgpu-xenos`
para color/depth/MV con RE del guest, o (b) migrar a un backend GPU propio. No
prometer DLSS/FSR3/Frame Gen al usuario.

## 9. Referencias

- `zolaware/reblue` — `src/gpu/settings.cpp`, `src/gpu/output*.cpp`,
  `src/gpu/dred.*`, `src/gpu/pipeline/pso_*`, `config/hooks/*.toml`.
- `freefrank/LostOdysseyRecomp` — `LostOdysseyRecomp/gpu/temporal_upscaler.h`,
  `upscaling_plan.h`, `dlss_ngx*.cpp`, `fsr_upscaler*.cpp`,
  `frame_generation_*.cpp`, `streamline_runtime.cpp`,
  `docs/notes/temporal-upscaling-feasibility.md`,
  `docs/notes/native-dlss-validation.md`, `cmake/Lo{Dlss,Fsr,Streamline}.cmake`.
- Local (solo mientras exista el clon): `%TEMP%\opencode\repos\`.
- Propio: `rexglue-sdk-0.10/cmake/rexglue_fidelityfx.cmake`,
  `rexglue-sdk-0.10/src/ui/presenter.cpp`.
