# Gohan del Futuro (Shin Budokai) en B3 HD — estado del modelo, distancia con los HD nativos y cómo mejorarlo

Exploración e ingeniería inversa, sin cambios en el proyecto y sin arrancar el juego (2026-10-06).
Carpeta: `scratchpad/explore/03_modelo/` (scripts + PNG). Extracciones grandes: `D:\DBZ3HD\explore\03_modelo\`.

---

## 0. Resumen

1. **Origen exacto.** `traje1-4.bin` NO vienen de una conversión de la comunidad. Son
   `awo_tools/psp_amo.py → convert_model()` aplicado a `BCGHFB00..03.amb`, que son las entradas 71-74 de
   `PSP_GAME/USRDIR/data_btl_cmn.afs` de la ISO de *Another Road*. Al reconvertir salen **idénticos byte a byte**.
   El moveset (`anm_forma1.bin`) y la cámara salen de `BCGHF.amb` (entrada 70, vía `sb_amm.py` + `ps2hd`). Son
   idénticos a `scratchpad/ghf/ghf_anm_hd.bin` y `ghf_cam_hd.bin` de la sesión del 04-10.
2. **Calidad.** Es un modelo de PSP pasado tal cual.
   - Malla: 1505 triángulos frente a 2459 del Gohan adulto HD.
   - Texturas: 3 de 16 colores (256², 256², 128²) con la sombra pintada.
   - Una rampa "neutra" y alfa 255 en todo, así que **en juego no recibe sombra toon**: el PS trata alfa alta
     como "sin sombrear".
   - Normales del cuerpo bastante peores que las nativas, lo que mancha el brillo HD del borde.
   - Sin boca (no hay huesos M_*) y solo 2 caras de expresión.
3. **"Tira del cinturón": causa localizada.** Las colas del cinturón de PSP salen **en horizontal hacia
   delante** en la pose de reposo del modelo. En B3 las colas (y el pelo) **no se animan**: las mueve una
   simulación de física por cadenas (tabla del XEX por fid de modelo). `roster_ext` pone a **0** el puntero
   de física de los modelos nuevos, y el moveset de SB solo trae giro de OBI en **1 de 143** animaciones.
   Resultado: una "tabla" rígida que sale del cinturón (ver `cinturon_reposo.png`).
4. **Fuente mucho mejor en disco.** SDBH World Mission trae `model/bcghf`: el Gohan del Futuro de Dimps en
   EMD/EMB.
   - 3449 triángulos, texturas DXT1 de hasta 512² y **rampas toon 64×64** (el mismo concepto que la HD).
   - Boca con huesos `f_jaw`/`f_*mouth*`, **las 7 caras de B3** (L00, L01, L04, L05, L06, L09, L18) y
     cinturón de 4 eslabones por lado.
   - Su esqueleto es el de B3 con la Z espejada: mismos sufijos y mismos ejes locales.

---

## 1. Qué contienen los 4 trajes (evidencia)

Comandos: `analiza.py` → `analiza_out.txt`, `analiza_trajes234.txt`; `draw_oracle.py` (lint OK).

| | traje1 (B00) | traje2 (B01) | traje3 (B02) | traje4 (B03) | Gohan adulto HD (225) |
|---|---|---|---|---|---|
| Bin | 351.616 B | 354.656 | 357.248 | 383.712 | 814.816 |
| AWO / AZT | 199.232 / 152.320 | 202.272 / 152.320 | 204.864 / 152.320 | 214.752 / 168.896 | 278.624 / 536.128 |
| Huesos | 43 (GHF) | 44 | 44 | 43 | 54 (GHL) |
| AWG (cuerpo + variantes) | 13 | 12 | 12 | 14 | 19 |
| Ventanas AWG0 / índices | 1525 / 3932 | 1778 / 4034 | 1828 / 4010 | 1536 / 3950 | 2107 / 5100 |
| Triángulos dibujados | 1505 | 1539 | 1515 | 1511 | 2459 |
| Draws / materiales | 8 / 3 | 8 / 3 | 8 / 3 | 8 / 3 | 20 / 15 |
| Texturas | 256²,256²,128² + rampa 64² | igual | igual | + 1×128² | 20 (seis de 256², rampas por material) |
| Cara | NOR | **SS** (SSJ, rubio) | **SS** (SSJ) | SENZAI | S00 + 5 expresiones |
| Boca / dientes | no (sin M_*) | no | no | no | M_JAW, M_*MOUTH*, dientes |

- **El PSP original** (`BCGHFB00`): 43 huesos, 13 AMG, AMG0 de 2749 vértices de tira y 1505 triángulos.
  Las texturas son **4 bpp (16 colores)**. El conversor no pierde geometría: los 1505 triángulos
  sobreviven y las ventanas se sueldan 2749 → 1525. Se descarta el hijo `#RPT` (2,8 KB).
- **Las texturas** traen el color y la sombra pintados (`psp_tex0/1/2.png`). Las nativas HD son casi
  blancas (con líneas) y el color sale de la rampa.
- **Trajes 2 y 3 son el SSJ** (`trajes_ghf.png`). El "SSJ pendiente" es registrarlos como forma, no como
  traje. Emparejamiento probable: (B00, B01) y (B03, B02). Hay que confirmarlo con la tabla de AR.
- **Rarezas de las etiquetas.** El traje 2 usa manos `GHL_L00_LHAND/RHAND` (prefijo de Gohan adulto) y el
  traje 3 un hueso `XGF_NLA`. El enlace por sufijo funciona, pero hay que vigilar en juego el cambio de
  pose de mano (puño) del traje 2.
- **Normales** (`render_normales.py`):

  | | Desviación media frente a la normal suave | Normales > 45° | Normales invertidas |
  |---|---|---|---|
  | Cuerpo GHF (normales de la piel PSP) | 15° | 22 % | 5 % |
  | Rodillas, pies, cadera y hombros de GHF | 36-52° | | |
  | Cabeza y manos de GHF (recalculadas por psp_amo) | 0° | | |
  | Nativo HD | 4-9° | ~0 % | |

### Imágenes
- `trajes_ghf.png`: los 4 trajes.
- `ghf_vs_ghl.png`: GHF frente a Gohan adulto HD, cuerpo y cara (`render_hoja.py vs`).
- `malla_densidad.png`: alambre de GHF (1505), HD (2459) y SDBH (3449).
- `normales_rim.png`, con tres columnas: GHF tal cual, GHF con normales suaves y HD.
  - Fila 1: luz Lambert. Las manchas rectangulares del pantalón son normales malas.
  - Fila 2: máscara aproximada del brillo HD del borde.

---

## 2. Sombreado real de la HD (de los volcados de shaders)

`D:\DBZ3HD\shaders_dump`:

**PS toon `5F27AACEB38B1088`:**
- `color = base − rampa[u = ½·N·L + ½, v = c1.x]`.
- Si `base.a > c255.z`, `color = base` (sin sombrear).
- Después suma el brillo de borde `c39.x · (½(1−|N·V|)² + escalón((1−|N·V|)⁶ ≥ ½))`. La constante c255.x
  = ½ es una suposición.

**VS `F3AC1AA2FE3EA253`:**
- La paleta tiene 48 B por hueso. El peso de la ventana mezcla el hueso con otra transformación de la misma
  entrada de paleta.
- `o2.w = c39.x` solo si la normal ≠ 0. Los nativos ponen normal nula en lo "sin luz".

**Consecuencias:**
- Las texturas de GHF tienen **alfa 255 en todo**, así que en juego **todo GHF sale sin sombra toon**: solo
  color plano pintado más brillo de borde. Los nativos usan alfa 0, con alfa 255 únicamente en el blanco
  de los ojos.
- La rampa `psp_ramp.npy` se pensó para multiplicar: es blanca y gris, y blanco = sin cambio. **Restada,
  pondría el modelo casi negro** si alguien quitara el alfa sin cambiarla.
- La nota de memoria "color = base × (1 − rampa)" equivale a la resta solo con base blanca. El shader
  **resta**, y eso importa para bases de color como las de GHF.
- **Sin comprobar:** el contorno negro. La rampa nativa reserva las filas 56-63 (negro/blanco). Si el pase de
  contorno usa este mismo PS, el alfa 255 de GHF también le quitaría el contorno. Ver §6.

---

## 3. La "tira del cinturón"

**Evidencia** (`render_cinturon.py` → `cinturon_reposo.png`; las dos primeras son el estado actual en reposo,
de frente y de perfil; las dos últimas, con el arreglo):
- **Pose de reposo de GHF.** `OBI` está en (0, 2.18, 1.26), delante. `ROBI1-3` y `LOBI1-3` tienen giro
  identidad y avanzan en **+Z hasta z = 4.83**, es decir, en horizontal hacia delante.
- **Gohan adulto HD** también tiene las colas horizontales en reposo (hacia +X, con nudo lateral).
  Su moveset (234) **no tiene huesos OBI ni HAIR**: los mueve la física.
- **La física está en el XEX** (imagen US descifrada):

  | Dirección | Contenido |
  |---|---|
  | `char96` + 8 (0x8234ABB8 + 96·ID) | Lista de modelos de 12 B: `[fid, puntero de cadenas de física, caché]` |
  | Fid 225 de Gohan adulto | → 0x823389A0: 5 cadenas, HAIR1-3, LOBI1 y ROBI1 |

  Registro de cada cadena, 0x180 B:
  - Nombre del hueso raíz.
  - +0x1F: número de articulaciones (3, es decir, cadenas de 4 huesos).
  - Límites por articulación en radianes.
  - Amortiguación y gravedad.
  - Esferas de colisión WAIST, LLEG1 y LLEG2.
- **El fallo.** `roster_ext.cpp` escribe a propósito `+4 cadenas de fisica = 0` (líneas ~311 y ~500) para
  los modelos de personajes y trajes nuevos, así que **GHF no tiene física**. Sus colas quedan en reposo
  salvo en la única animación que trae claves de OBI (1 de 143).

**Arreglos posibles:**
- **A (el más simple, sin C++).** En los 4 trajes, girar en el eje del AWG el bind local de `ROBI1`/`LOBI1`
  unos +80° sobre X (las colas cuelgan). Las ventanas son locales al hueso, así que la malla las sigue.
  Además, quitar o recomponer las pistas OBI de esa animación 136 del ACM.
  - Comprobado offline con FK de `altura.py` y el reposo real: columnas 3-4 de `cinturon_reposo.png`.
  - Colas rígidas, sin balanceo.
- **B (como los nativos).** Una clave en `roster.toml` para dar al modelo un puntero de cadenas: copiar el
  del donante o escribir registros propios.
  - Con el modelo PSP (3 huesos por lado) los registros del donante esperan 4: hay que escribir registros
    con +0x1F = 2.
  - Con el modelo de SDBH (4 por lado) el registro de Gohan adulto encaja tal cual.

---

## 4. Opciones de mejora, ordenadas por calidad/esfuerzo

| # | Opción | Ganancia | Esfuerzo | Límite / bloqueo |
|---|---|---|---|---|
| 1 | **Arreglos rápidos sobre el port PSP:** cinturón (A), alfa 0 + rampas por material (cuerpo: gris restada; piel: rampa cálida), normales suaves, texturas IA ×2 | Media: aparece la sombra toon, el borde HD queda limpio, líneas nítidas | **~1 día** (cambios en `psp_amo.convert_amt` y un pase de normales; verificación offline con draw_oracle/model_render) | Hay que respetar el tamaño del bin (§5). La silueta sigue siendo PSP. |
| 2 | **Reconstruir desde SDBH WM (`bcghf`)** | **Alta**: 3449 triángulos, texturas 512², rampas propias, cicatriz, boca y 7 caras, cinturón de 4 eslabones (física del donante) | **3-5 días**: adaptador EMD/ESK en `b3_gateway`; espejo Z; rampa HD = 1 − rampa XV (color plano por material); escala y cadera con `altura.py`; manos | **Manos.** SDBH las piel-a dedos y B3 usa variantes rígidas L01..L22. Opciones: hornear las poses o reutilizar las variantes PSP/GHL. El presupuesto de texturas obliga a reducir alguna 512². Costumes b00, b01, b03 (falta saber si hay SSJ). |
| 3 | Kitbash con piezas HD de Gohan adulto (manos y variantes) | Baja-media | 0,5-1 día | Las manos GHF y GHL tienen ambas 187 ventanas (mismo linaje) y la muñequera tapa la costura. **Cabeza y pelo no sirven**: GHF tiene otro peinado y la cicatriz. |
| 4 | Subdivisión o suavizado de malla | Baja (redondea pero emborrona los picos toon) | 1-2 días | Solo 1 hueso + peso por ventana (con el padre): los vértices nuevos entre huesos no-padre se agrietan. IB u16; lo validado son 5148 ventanas / 8376 índices. **Desaconsejado.** |
| 5 | Repintado a mano | Alta en caras/texturas | Días de artista | Sin herramienta: solo merece la pena sobre la opción 2. |
| 6 | Upscale en tiempo de ejecución (`dbz3_texture_upscale` ×2/×3) | Solo nitidez (Catmull-Rom) | 0: ya existe y se aplica solo a las DXT3 de GHF | Sin detalle nuevo; opcional para el usuario. |

**Otras fuentes revisadas:**
- B3, IW y B2 no tienen Gohan del Futuro.
- Shin Budokai 1: su `data_btl_cmn.afs` tiene 206 entradas, ninguna GHF.
- Solo existen AR (PSP) y SDBH WM (PC).

**IA en disco** (sin instalar nada):
- `realesrgan-ncnn-vulkan.exe` **no está** (`texture_upscale_b3.py` lo busca en `%TEMP%\opencode\realesrgan`
  o en `mod center hd\tools\realesrgan`).
- **chaiNNer** sí está instalado (`%LOCALAPPDATA%\chaiNNer`). Su Python lleva torch 2.7 cu128 y spandrel 0.4.1.
- Hay modelos del usuario en `E:\Emuladores\Retrobat\bios\pcsx2\textures\CREAR TEXTURAS\models`:
  4x-AnimeSharp, 2x-AnimeSharpV4_RCAN, 4x-UltraSharpV2, 4xNomos8kDAT, RealESRGAN_x4plus y otros.
- Prueba hecha: `upscale_ia.py`, en GPU, con unos segundos de cálculo → `upscale_ojos.png`.
  - **4x-AnimeSharp y 2x-AnimeSharpV4_RCAN** dejan las líneas limpias.
  - Lanczos solo suaviza.
- Maqueta en memoria: `mejoras_cara.png` / `mejoras_cuerpo.png`, con cuatro columnas:
  - A: tal cual.
  - B: IA ×2.
  - C: IA + normales suaves + alfa 0 + rampa gris restada.
  - D: nativo.

---

## 5. Límites del formato y del motor que condicionan cada opción

- **Tamaño del bin.** Al crecer el `#AZT` se corrompe la memoria del guest: Krillin ×2 (1,56 MB de AZT) se
  deforma y ×4 se cierra (`docs/07_ports/TEXTURAS_HD_RUNTIME_UPSCALE.md` §2.1).
  - Los nativos llegan a unos 948 KB de bin (Goku 264) y 610 KB de AZT.
  - Regla segura: **cada traje GHF ≤ ~800 KB y AZT ≤ ~600 KB**.
  - IA ×2 en cuerpo y cabeza (512²) y manos 256² da unos 603 KB de AZT y ~800 KB de bin: en el límite de
    los nativos. Dejando las manos en 128², unos 545 / 745 KB.
- **AWG0.** IB u16 (≤ 65535 ventanas); probado en juego hasta 5148 ventanas / 8376 índices. La TABLA de
  paleta debe ir justo tras el IB (`grow()` ya lo cumple). `B_count` = primitivas. Lint: `draw_oracle.py`.
- **Piel.** 1 hueso por ventana más un peso de mezcla en el VS. No hay pesos de 4 huesos (SDBH tiene hasta
  4): hay que colapsar al dominante.
- **Normales.** Las nulas apagan el brillo de borde (`o2.w = 0`). El brillo depende mucho de |N·V|, así que
  las normales malas se ven como manchas.
- **Alfa de la textura base.** Alfa alta = sin sombra toon (eso hace hoy GHF entero). Los ojos necesitan
  alfa 255; el resto, 0.
- **Rampa.** Se resta. Las de SDBH/Xenoverse multiplican (piel = degradado de color de piel), así que hay
  que convertirlas: rampa HD ≈ color plano del material × (1 − rampa XV).
- **Física.** Las cadenas van por fid de modelo y nombre de hueso raíz, y `roster_ext` la anula en los
  modelos nuevos.
- **Boca.** Sin huesos M_* no hay lip-sync. Las ranuras estándar que faltan apuntan al marcador del slot 12
  (nota del 04-10).

---

## 6. Plan recomendado

**Fase 1: arreglar y pulir el port PSP actual** (~1 día, riesgo bajo, todo offline salvo la prueba final).
1. Cinturón (arreglo A): girar el bind de `ROBI1`/`LOBI1` en el AWG0 y en los AWG auxiliares que los lleven,
   en los 4 trajes, y limpiar las claves OBI de la animación 136. Verificación: FK con `posar.py` en reposo,
   andar y golpe.
2. Sombra toon: alfa 0 en las texturas base (255 solo en el blanco de los ojos, detectable por color) y una
   rampa por material.
   - Cuerpo: rampa 6 de Gohan adulto, gris restada.
   - Cabeza y manos: rampa de piel calculada como `piel_PSP − sombra_objetivo`.
   - Rampas por material: el bin ya tiene 3 materiales, no hay que partir draws.
3. Normales suaves soldadas por posición en las partes con piel. Es lo que `psp_amo._smooth_normals` ya hace
   para las rígidas.
4. Texturas IA: 4x-AnimeSharp con el Python de chaiNNer, reducidas a 512/512/128 (o 256), DXT3, sin pasar
   del presupuesto.
5. SSJ: registrar (B00, B01) y (B03, B02) como 2 formas (`formas = 2`, 2 modelos por traje), en coordinación
   con el informe de transformaciones.

**Fase 2: reconstrucción desde SDBH WM** (3-5 días, la mejor calidad).
1. Adaptador `--emd` para `b3_gateway` (base: `sdbh_stats.py` / `render_sdbh.py`), con plantilla GHL (225).
   Espejo Z; ejes y sufijos ya coinciden (§7).
2. Rampas: 1 − rampa XV ponderada por el color plano de cada material. Texturas 512 → ajustar al presupuesto.
3. Caras L00..L18 a variantes AWG; boca y dientes a los huesos M_* de la plantilla, para que funcione el
   lip-sync con la boca del donante.
4. Manos: reutilizar las variantes PSP/GHL (rápido) u hornear las poses de dedos (lento).
5. Física: añadir en `roster_ext` una clave tipo `fisica = "donante"` que copie el puntero +4 del modelo del
   donante (cadenas de 4 huesos compatibles).

**Qué hay que comprobar en el juego** (en segundo plano, con la partida protegida):
- Cinturón en reposo, andando, en el golpe fuerte y en agarres (el set GOK_).
- Que aparece la sombra toon y que **el modelo no se pone negro** (si se pone negro, la rampa está mal).
- Contorno negro antes y después de cambiar el alfa (abierto, §2).
- Brillo HD con `dbz3_hd_rim_light` a 0 y a 1.
- Selector y combate con **GHF contra GHF** (dos copias en memoria) y texturas ×2: que no haya deformación
  (el síntoma del Krillin ×2).
- Pose de mano (puño) del traje 2, que tiene etiquetas `GHL_`.
- Con SDBH: altura (pies en el suelo), codos y rodillas, y lip-sync.

**Riesgos:**
- Presupuesto de memoria al crecer las texturas: hay que medir los trajes más grandes.
- Umbral exacto del alfa y forma del contorno: deducidos del PS, sin verificar en juego.
- Parecido con lo oficial: el usuario exige aspecto nativo; conviene comparar con los oficiales
  (match-official-assets).
- SDBH es un modelo más moderno: puede verse más "Xenoverse" que B3.
- Licencia y origen: los assets de SDBH son de otro juego, como el resto de ports.

---

## 7. Notas técnicas sueltas

- **Esqueleto de SDBH.** `bcghfb00.esk` lleva 96 huesos en la Z de B3. Las posiciones locales y los
  cuaterniones coinciden con los de GHL al aplicar el espejo z → −z, q(x, y, z, w) → (−x, −y, z, w):
  larmrot, larm1, lhandrot, llegrot, lfoot1, obi y lobi1/2 comprobados.
  - Huesos de B3: `waist ... f_jaw, f_lmouth1/2, f_rmouth1/2, f_dteeth/uteeth, xghf_obi, xghf_lobi1-4,
    xghf_robi1-4`.
  - Dedos `LIndex1..` y caras `xghf_L00..L18_face`.
- **EMD (versión 0x9300, LE).** Listas de triángulos; vértices de 48 B (flags 0x207: pos, normal, uv,
  4 índices de hueso y 3 pesos). Cada submalla lleva 2 texdefs: [textura base, rampa 64²] del EMB.
- **Moveset.** `anm_forma1.bin`: los ACM 1, 2 y 3 tienen 143, 3712 y 257 animaciones; solo el 1 lleva
  pistas GHF_OBI con datos, y solo en una animación.
- **Archivos en D:** `D:\DBZ3HD\explore\03_modelo\`:
  - `BCGHFB00-03.amb`, `BCGHFM1.amb` (de la ISO de AR);
  - `gohan_hd_225/228.bin` (descomprimidos);
  - `reconv_traje1-4.bin` (idénticos a los del mod).

**Scripts** (todos en esta carpeta, solo lectura del proyecto):

| Script | Qué hace |
|---|---|
| `analiza.py` | Estadísticas del bin |
| `posar.py` | FK con un ANM |
| `render_cinturon.py` | Pose de reposo del cinturón y arreglo A |
| `render_hoja.py` | Trajes y GHF frente a GHL |
| `render_normales.py` | Lambert y brillo de borde |
| `render_mejoras.py` | Maqueta de la fase 1 (rampa restada como el PS) |
| `upscale_ia.py` | Upscale con el Python de chaiNNer |
| `sdbh_stats.py`, `render_sdbh.py`, `render_malla.py` | Modelo de SDBH y densidad de malla |
