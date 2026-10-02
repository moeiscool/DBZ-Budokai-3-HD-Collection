# universal-modder — evaluación y aplicación al RE del port (2026-09-30)

> Se investigó `github.com/rehan-remade/universal-modder` (MIT, ~2k estrellas)
> como posible ayuda para portear contenido de otros juegos, ampliar y mejorar.
> Clonado en un directorio externo (`%TEMP%\opencode\universal-modder`) solo para
> estudio; NO se instaló nada en el proyecto ni se añadieron skills/API keys.

## Qué es (y qué NO es)

NO es un porteado ni un conversor de formatos. Es un **plugin de agente**
(Claude Code / Codex / Cursor / Gemini / Copilot / OpenCode) que aporta:

- **Skills** en formato Agent Skills (11): `mod-any-game`, `game-recon`,
  `reverse-engineering`, `mashup-mods`, `asset-pipeline`, `fal-assets`,
  `game-automation`, `showcase-video`, `publish-mod`, `share-field-notes`.
- **CLI `um`** (Python): `scan`, `kb`, `win` (drive/shot/record), `video`,
  `sprite`, `render3d`, `fal`, `publish check`, `backup`.
- **Knowledge base** de *field notes* (4 juegos: AoE2, GTA×Minecraft,
  Terraria×2) + 3 técnicas. **No hay notas de Budokai ni de Xbox 360/recomp.**
- **12 engine playbooks** (Unity, Unreal, .NET/XNA, Godot, Source, Bethesda,
  Minecraft, Genie, RE/FromSoft/RAGE/Cyberpunk, **native C++**, indie, retro).

Es **método + tooling para agentes**, no una librería. Los playbooks de motor
NO aplican al B3 HD (no es Unity/Unreal/.NET); DBZ B3 HD es **recompilado Xbox
360 nativo big-endian**, así que lo reutilizable es el método de RE y mashup.

## Lo directamente aplicable a este proyecto

### 1. Skill `reverse-engineering` → desbloquear el bind/skin de la Vía B (F4)

Es exactamente la metodología que falta para el bloqueo documentado en §3.4.6 /
§3.4.10 (`M_bind` real, mapeo hueso→slot σ). Puntos que adopta y encajan:

- **Ghidra/IDA vía MCP** para RE de `sub_82087F58` (el renderer que aplica la
  paleta): decompilar, renombrar y tipar acumulativamente; seguir xrefs.
- **RenderDoc (`renderdoc-mcp`)** para capturar la paleta en el frame de
  BIND/T-pose: ver cada draw, constant buffers (matrices view/proj) y el depth
  buffer. Es la vía alternativa a RE puro para obtener `M_bind` sin decompilar.
- **Regla de oro**: "reverse-engineer a binary file format and prove it with a
  round trip" — ya hicimos el round-trip del AWO; el método formaliza que el
  bind necesita su propio round-trip (aplicar paleta → reproducir T-pose →
  comparar contra el bin nativo).
- **Make it an oracle**: usar `_grow_tpl` (plantilla nativa crecida, renderiza
  PERFECTO) como **oráculo conocido bueno** y comparar el port contra él por
  variables, no a ojo.

### 2. Skill `mashup-mods` Pattern 3: "embed a decomp as a library"

Patrón generalizado `libsm64`/`G64`: envolver un decomp/recomp como librería
que recibe colisión+input y devuelve estado+mesh. **Es la descripción exacta de
lo que es ReXGlue** (un recomp con runtime). Ideas trasladables:

- **Recomp como oráculo de reimplementación** (`retro-decomp.md` cita
  explícitamente *"Xbox 360: XenonRecomp / ReXGlue"*). Un motor idiomático
  alternativo (patrón 4 tipo IW4L / Skate 3 Rust) leería el AWO/`data_cmn.afs`
  del usuario y usaría el recomp como ground truth. **Demasiado pesado para
  ahora**; se anota como vía futura, no como plan.
- **Publish check** (patrón: "converters that run on the user's files; game
  assets never committed"): refuerza la promesa ya vigente (§9.3: no subir
  `*.bin/*.afs/*.awo/...`).

### 3. `um publish check` → lint pre-release reutilizable

Script corto (125 líneas) que ya implementa parte de nuestra política §9.3.
Detecta: **ficheros de juego copiados verbatim** (por tamaño+hash contra el
install), **secretos** (FAL/Anthropic/OpenAI/GitHub/AWS/private keys, `.env`),
**huellas de decompilador** (`FUN_xxxx`/`sub_XXXX`/"Decompiled with"/ILSpy),
**rutas absolutas de usuario**, y **archivos de motor grandes** (`.pak/.bsa/...`).
Encaja como chequeo extra antes de `make_release.ps1`. Nota: nuestro `.gitignore`
de `github/` ya cubre gran parte; lo novedoso es el **hash-match contra los AFS
del install** y el escaneo de **secretos**.

### 4. Knowledge: técnica "Oracles" + "Driving real games safely"

- **Oracles** (round-trip, trace-replay, synthetic host, measurement scene,
  circuit-breaker a ~3 fallos, journal `MODLOG.md`): coincide con el protocolo
  de laboratorio de `RE_MASTER_2026_09.md` §4 (manifest, clasificación
  NO_EFFECT/INFRA_CRASH/PARSE_CRASH/...). Aporta dos ideas nuevas: **trace-replay**
  (grabar posiciones/velocidades reales por tick y reproducirlas contra el port)
  y **synthetic host** (construir contra un host falso con geometría conocida
  antes de tener el juego montado).
- **Driving real games safely**: solapa con nuestro arnés `tools/long_run.ps1`
  / `press_key.ps1` / `grab_window.ps1`. Sin acción inmediata.

### 5. `native.md` (engine playbook nativo C++)

Describe justo lo que ya hacemos: proxy DLL / hook `IDXGISwapChain::Present` +
ImGui / usar las matrices view-proj del juego para inyectar 3D en su pase
(ReShade addon). Confirma el enfoque; no aporta técnica nueva aquí.

## Lo que NO sirve / riesgos

- **`um scan`, playbooks de motor, `fal-assets`, `render3d`, `sprite`**: no
  aplican (motor nativo 360, no PC con loader; assets de pago fal.ai orientados
  a sprites 2D, no a portar geometría real).
- **Instalar el plugin** añadiría skills al cwd y un MCP de fal; no se hizo.
- Requiere Python 3.10+, ffmpeg, Blender (3D) y `FAL_KEY` (assets).
- **Regla de su KB**: no publicar ficheros de juego ni código decompilado —
  alineado con lo nuestro.

## Conclusión

Valor real = **método de RE** (Ghidra/IDA/RenderDoc vía MCP + oráculos +
round-trips), aplicable al único bloqueo vivo (bind/skin de la Vía B, §3.4.6).
No cambia la entrega (swap nativo HD↔HD). Vía B sigue **aparcada**; si se
retoma, este documento fija el protocolo: (1) oráculo `_grow_tpl` conocido bueno,
(2) capturar `M_bind` con RenderDoc en BIND/T-pose o RE de `sub_82087F58` con
Ghidra vía MCP, (3) round-trip del binding (aplicar paleta → reproducir T-pose →
comparar). Opcional: adoptar `um publish check` como lint pre-release.

## Referencias

- Repo: `github.com/rehan-remade/universal-modder` (MIT).
- Skills clave: `skills/reverse-engineering/SKILL.md`,
  `skills/mashup-mods/SKILL.md`,
  `skills/mod-any-game/references/engines/{native,retro-decomp}.md`.
- `knowledge/techniques/oracles-how-agents-know-a-mod-works.md`.
- `um/publish.py`.
- Nuestro bloqueo: `AGENTS.md` §3.4.6/§3.4.10,
  `docs/07_ports/SESION_DRAW_SEMANTICS_2026-09-11.md`,
  `docs/RE_MASTER_2026_09.md` §4/§5 (F4).
