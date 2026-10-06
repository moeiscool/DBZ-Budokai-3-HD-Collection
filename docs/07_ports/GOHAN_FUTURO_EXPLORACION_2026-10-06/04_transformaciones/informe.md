# Transformaciones de Gohan del Futuro (port de Shin Budokai: Another Road) en B3 HD

Fecha: 2026-10-06. Solo exploración y RE. No se ha tocado ningún archivo del proyecto ni se ha abierto el juego.
Scripts y volcados: en esta carpeta. Extracciones grandes: `D:\DBZ3HD\explore\04_transformaciones\`.

## 0. Resumen

- **El usuario tiene razón, con un matiz.** En *Another Road*, Gohan del Futuro (código `GHF`) tiene 4 formas: Normal, Super Saiyan, Super Saiyan 2 y Potencial liberado. Los parámetros de esas formas son idénticos a los de Gohan adulto de la misma ISO.
  - **El matiz:** en el port actual esas 4 formas son **4 trajes**, no transformaciones. Lo comprueban los nombres de hueso: `traje1` = `NOR_FACE`, `traje2` y `traje3` = `SS_FACE`, `traje4` = `SENZAI_FACE`. Además el port tiene `formas = 1`.
  - Por eso en el select se puede elegir "SSJ", pero en combate pelea siempre en la forma 0 y no puede transformarse.
- **En B3 transformarse no gasta ki.** Pide **tener al menos N barras**: la cápsula guarda N×10 en el byte +15. Con menos de **1 barra (1000 unidades)**, si te golpean vuelves a la forma normal.
  - P+K+G salta directamente a la forma más alta para la que tienes ki y cápsulas.
  - Cada forma tiene su propio "nivel base" de ki.
- **Gohan adulto (ID 4) en B3:**

  | Forma | Requisito | Exige | Nivel base de ki |
  |---|---|---|---|
  | Super Saiyan | ≥ 4 barras | — | 3 → 4 |
  | Super Saiyan 2 | ≥ 5 barras | SSJ | 4 |
  | Definitivo («Elder Kai Unlock Ability») | ≥ 6 barras | SSJ2 | 5 (moveset propio) |

- **Propuesta para Gohan del Futuro:** las mismas 3 transformaciones y las mismas cifras (4 / 5 / 6), con sus propios modelos de AR (B00–B03).
- **Qué falta construir:**
  1. La entrada P+K+G (código 0x2E0/0x3E0) en su BCM.
  2. Las dos animaciones de esos códigos, injertadas del donante.
  3. El requisito de ki por cápsula: hoy toda transformación nueva pide 5 barras y la ficha dice 3.
  4. El modelo por forma, para usar el SSJ2 propio.
  5. La configuración del mod: `formas = 4`, 3 cápsulas y 1 traje con 4 modelos.

## 1. Cómo codifica B3 HD las transformaciones (RE con evidencia)

### 1.1 Entrada de mando (BCM / `#CCM` del bin de cámara)

Los 17 personajes con formas tienen una sola entrada de arranque para transformarse:
`w0=0 w1=7 (P+K+G) w5=0x0004 (transformar) w6=1 w8=0 (sin cápsula) w9=0 (sin ki) w12..14 = 0x2E0 / 0x3E0 / 0x3E0`.

- Ejemplo, Gohan adulto (cam 231): `0000 0007 0000 0000 0000 0004 0001 0000 0000 0000 0000 0000 02e0 03e0 03e0 0000`.
- La entrada no lleva ni coste ni forma destino: lo decide el código del juego (§1.5).
- Script: `bcm_dump.py 4 3 2 0 7 8 9`.

### 1.2 Animación (`#CSK` del ANM)

- El bloque 0x2E0 de Gohan adulto (data_cmn 234) usa la animación 14 del **almacén global (pool 0)**, que es común a todos. Lleva 3 líneas AP.
- Esas líneas incluyen el efecto `0x64` del BSP (destello de transformación) y el grito (k3 = hueco del banco `lang_*`). Esto ya estaba documentado en `b1port`: "k0:0x64 + k3:0x29".
- Como la animación es global, injertar 0x2E0/0x3E0 del donante no necesita AMM.

### 1.3 Registro de combate por forma (`char372` 0x82329CF0 + 372·ID, +0xD0 = nº de formas, +212 + 20·f)

| Offset | Tipo | Significado | Evidencia |
|---|---|---|---|
| +0 | u16 | cápsula que exige la forma | `sub_82119108` (lha 0(r29)) |
| +2 | u16 | ID cuyo `char96` aporta el modelo | `sub_820F9970` |
| +4 | u16 | índice en `char96.formas[]` del ID de +2 (y del ANM: `anm[f]`) | `sub_820F9970`: lee `char96 + 16 + 8·(ID·12 + idx)` |
| +6 | u8 | tipo: 01 normal (reversible, hay más), 05 irreversible, 06 última (reversible), 07 especial/automática (Majin, nave), 08 forma de otro personaje | `sub_82119108` (≠6 para subir; el siguiente 0/7/8 corta) y `sub_82119258` (al revertir se para en 3/4/5/7) |
| +7 | u8 | bit 0: rutina de transformación "Saiyan" (1 en Kaioken/SSJ; 0 en Definitivo, Freeza, Cell…) | `sub_820FB5D0` elige el manejador 0x820FA940 o 0x820FA7D8 |
| +8 | u8 | parámetro de potencia (0/10/15/30 en Gohan). **Sin confirmar** (¿bonus de daño?) | SB lo tiene igual (BTLPARAM) |
| +9 | u8 | **nivel base de ki en barras** | `sub_82100760`: `+221 × 1000` |
| +10, +12 | u16 | 300/360/420 y 100/150/200, crecen con la forma. **Sin confirmar** | en SB son constantes (300/100) |
| +16 | ptr | tabla de físicas del personaje (floats, igual en todas sus formas) | `sub_820F9970` → +1380 |

### 1.4 `char96` formas (0x8234ABB8 + 96·ID, +16 + 8·idx)

Cada entrada es `u16 ID`, `u8 modelo dentro del traje`, `u8 boca`, `u8 ?`, `u8 aura` (3 = aura de forma, 4 = con rayos tipo SSJ2).

- Gohan adulto: `(4, m0, 0)`, `(4, m1, 3)`, `(4, m1, 4)`, `(4, m2, 0)`. Es decir, **SSJ2 reutiliza el modelo SSJ y solo añade los rayos**, y el Definitivo usa el modelo 2 (227/230).

### 1.5 Lógica en el código recompilado (`generated/`)

**`sub_82119108`: ¿a qué forma subo?**
- Si la forma actual es de tipo 6, no sube.
- Si no, recorre k = actual+1… y en cada forma comprueba tres cosas:
  1. que la forma esté activa (byte `fighter+8156+k`: cápsula equipada);
  2. que la máscara +14 de la cápsula incluya la forma actual;
  3. que haya **ki ≥ (+15)·100**, preguntado a `sub_82115518(fighter, ki, 2)`. Con el flag 2 **solo comprueba y no gasta**.
- Sigue subiendo mientras pueda y se queda en la última forma que cumple.
- Al final aplica un tope del combate (`fighter+7412`, +24 = forma máxima).

**`sub_82119258`: revertir.**
- Si el ki es ≥ **1000.0** (constante 0x8201B3F0 = 1 barra), no revierte.
- Si es menor, baja forma a forma hasta la primera de tipo 3/4/5/7, o hasta la forma 0. En la práctica: **SSJ / SSJ2 / Definitivo vuelven a la forma normal de golpe**.
- Hay un tope mínimo (+22).

**`sub_82100760`: nivel base de ki.**
- Devuelve `+9 × 1000` de la forma actual.
- **`sub_82116458`:** con cada golpe, el atacante gana `200 + 5·min(combo,5)·(9 − nivel base)`. Transformado (nivel base más alto), gana algo menos de ki por golpe.

**Unidades:** 1 barra = 1000; el máximo de B3 son 7 barras (SSJ4 pide "7 Ki Gauges").

### 1.6 Cápsula (`#SKC` data_usi 4, 40 B por registro)

| Offset | Significado |
|---|---|
| +8 | clase 0x11 |
| +10 | rareza (precio 3.000 / 6.000 / 10.000 Z) |
| +14 | **máscara de formas desde las que se puede usar** (SSJ 0x01, SSJ2 0x03, Definitivo 0x07) |
| +15 | **requisito de ki ×10** (40 / 50 / 60) |
| +16 y +18 | u16, cápsula exigida para poder equiparla. El juego mira las dos: `sub_821B79F8` y `sub_8214CA30` |

- El byte +15 coincide con el texto oficial «With N or more Ki Gauges» en 30 de 34 cápsulas (OCR de `modding resources`).
- Las 4 que no coinciden son de Piccolo (57: dato 4 / texto 3; 58: 5 / 4), Dabura (4 / 3) y Cooler (5 / 4). Manda el dato: es lo que usa el código. El PS2 GH tiene los mismos valores.

### 1.7 Gohan en B3 (la referencia)

Tabla completa de los 17 personajes en `evid_tabla_b3.md`. "Exige" = cápsula que hay que tener equipada antes.

| ID | Forma | Cápsula | Requisito | Desde | Exige | Nivel base | Tipo | Modelo (traje 1/2) | Aura | Moveset |
|---|---|---|---|---|---|---|---|---|---|---|
| 4 Gohan adulto | Normal | — | — | — | — | 3 | 01 | 225 / 228 | — | 234 |
| | Super Saiyan | 23 (Rare, 6.000 Z) | **≥4** | 0 | — | 4 | 01 | 226 / 229 | 3 | 234 |
| | Super Saiyan 2 | 24 (Rare) | **≥5** | 0–1 | 23 | 4 | 01 | 226 / 229 (el del SSJ) | 4 (rayos) | 234 |
| | Definitivo «Elder Kai Unlock Ability» | 25 (Special, 10.000 Z, no intercambiable) | **≥6** | 0–2 | 24 | 5 | 06 | 227 / 230 | — | **233 propio** |
| 3 Gohan joven | Super Saiyan | 18 | ≥4 | 0 | — | 4 | 01 | m1 | 3 | 245 |
| | Super Saiyan 2 | 19 | ≥5 | 0–1 | 18 | 4 | 06 | m2 (propio) | 4 | **244 propio** |
| 2 Gohan niño | Unlock Potential | 16 | ≥3 | 0 | — | 4 | 06 | m0 | — | 251 |
| 0 Goku | Kaioken / SSJ / SSJ2 / SSJ3 / SSJ4 | 1–5 | 2 / 4 / 5 / 6 / 7 | — | cadena | 3 / 4 / 4 / 5 / 6 | — | — | — | — |

Otros parámetros por forma de Gohan adulto (campos sin confirmar): +8 = 0 / 10 / 15 / 30; +10 = 300 / 360 / 420 / 420; +12 = 100 / 100 / 150 / 200.

Texto oficial de las transformaciones de Gohan: «(Does not consume Ki Gauge when transformed)» y «Transformation is reversed if damage is taken with less than 1 full Ki Gauge!».

## 2. Qué tienen Shin Budokai y Another Road (ISO leídas en su sitio con `iso.py`)

### 2.1 Quién transforma en cada juego

- **Shin Budokai 1** (ULUS-10081, 18 personajes): no tiene Gohan del Futuro.
  - Gohan adulto `GHL`: Normal, SSJ, SSJ2 y Potencial liberado.
  - Gohan joven `GHM`: Normal, SSJ y SSJ2.
  - Tabla en el ELF (`SB1_BOOT.elf` 0x142578, registros de 24 B).
- **Another Road** (24 personajes): `BTLPARAM.DAT` (24 × 96 B) y el registro del ELF (`AR_BOOT.elf` 0x1B55F8 + 0x108·i). Volcado en `evid_ar_formas.txt`.

| Personaje | Formas | (potencia, nivel base) por forma | Tipo por forma |
|---|---|---|---|
| **GHF Gohan del Futuro (18)** | **4** | (0,3) (10,4) (20,4) (30,5) | 1, 1, 1, 2 |
| GHL Gohan adulto (2) | 4 | (0,3) (10,4) (20,4) (30,5) | 1, 1, 1, 2 |
| GHM Gohan joven (1) | 3 | (0,3) (10,4) (20,4) | 1, 1, 1 |

GHF es una copia exacta de GHL. Sus niveles base (3 / 4 / 4 / 5) son los mismos que los de Gohan adulto en B3. Solo cambia la potencia del SSJ2: 20 en SB, 15 en B3.

### 2.2 Archivos de `data_btl_cmn.afs` (AR)

| Archivo | Contenido |
|---|---|
| `BCGHF.amb` | moveset base |
| `BCGHFB00`–`B03` | modelos: `Bnn` = forma nn (como `BCGHMB02` = cara `SS2_FACE` de Gohan joven) |
| `BCGHFM1.amb` | el moveset base más un 2.º `#BSK` que **solo redefine el código 0x19F**: una animación, nada de golpes. GHL M3 redefine 0, 1 y 0x19F; GHM M2 redefine la postura |
| `BAR_GHF` | aura |
| `BSP_GHF` | técnicas |

Detalle de cada modelo (`evid_ar_ghf_mallas.txt`, `tex_*.png`, `pelo_formas.png`):

| Modelo | Forma | Cara (hueso) | Pelo | Notas |
|---|---|---|---|---|
| B00 | Normal | `NOR_FACE` | negro | |
| B01 | SSJ | `SS_FACE` | dorado (255,224,2), ojos verdes | |
| B02 | SSJ2 | `SS_FACE` | dorado, malla de pelo distinta (668 vértices frente a 726) | Mismo tono que el SSJ (el SSJ2 de Gohan joven es más oscuro: 234,189,1) |
| B03 | Potencial liberado | `SENZAI_FACE` («潜在») | negro | Variante de mano izquierda `GHF_L22_LHAND` con la **Espada Z**: 175 vértices, textura 3, la misma que en `BCGHLB03` de Ultimate Gohan. Solo se ve si una animación pide la mano 22 |

### 2.3 Cómo se transforma en SB

Hay una sola entrada en su BCM: `w0=0x20` + E, coste **0x0FA0 (4000)**, códigos 0x500/0x700. La tienen todos los que transforman; Android 18 y Bardock no la tienen.

- Esa entrada **sigue dentro del `camara.bin` del port** (bloque `0x172c`).
- B3 nunca usa `w0=0x10/0x20` en sus 38 movesets (`w0` solo vale 0, 1 o 2). Hay que comprobar en el juego si esa entrada se puede disparar. Si se dispara, haría la animación de SB y gastaría 4 barras sin cambiar de forma.
- Los definitivos de SB del port también usan `w0=0x10` y el port **no tiene modo hiper** (`bcm_summary`: `hiper = False`). Es otro pendiente, no de este tema.

### 2.4 Estado del port (`out/build/win-amd64-release/mods/port_gohan_futuro`)

- 4 trajes, que son las 4 formas (verificado por los nombres de hueso).
- Moveset = el `BCGHF` de SB, vía el port comunitario `ghf_365/367`, que es byte a byte el BCM de SB.
- `formas = 1`, `capsulas_forma = [0]`, `habilidades_transformaciones = []`.
- En el CSK hay 0x3E0 (un golpe de SB que el BCM no usa: dato muerto) y no hay 0x2E0.

## 3. Propuesta de formas y ki

**Recomendada: «Another Road + reglas de Gohan adulto de B3».** Sus datos de AR son los de Gohan adulto; B3 ya tiene esas reglas equilibradas; y existen modelos propios para las 4 formas.

| Forma | Modelo | Cápsula nueva (nombre) | Requisito (no gasta) | Usable desde | Exige | Nivel base | Aura | Moveset |
|---|---|---|---|---|---|---|---|---|
| 0 Normal | BCGHFB00 (traje1) | — | — | — | — | 3 | — | SB base |
| 1 Super Saiyan | BCGHFB01 (traje2) | «Super Saiyan» (Rare) | **≥4 barras** | forma 0 | — | 4 | 3 | igual |
| 2 Super Saiyan 2 | BCGHFB02 (traje3) | «Super Saiyan 2» (Rare) | **≥5 barras** | formas 0–1 | SSJ | 4 | 4 (rayos) | igual |
| 3 Potencial liberado | BCGHFB03 (traje4) | «Potential Unleashed» (Special) | **≥6 barras** | formas 0–2 | SSJ2 | 5 | — | igual |

- **Revertir:** golpe recibido con menos de 1 barra → vuelve a Normal. El Potencial liberado es de tipo 06 (última forma, reversible), como el de Gohan adulto. En SB es de tipo 2 (última). No se sabe si en SB es permanente.
- **Nombre del Potencial liberado:** «Elder Kai Unlock Ability» no encaja con el personaje, porque en el futuro no hay Kaioshin anciano. Mejor «Potential Unleashed» o «Hidden Potential».
- **Alternativa «canon»:** solo Normal + SSJ (≥4). Es lo que muestra el anime y el manga: Gohan del Futuro no llegó al SSJ2. Se pierden B02 y B03.
- **Variante «sin el SSJ2 propio»:** SSJ2 = modelo SSJ + rayos, como hace Gohan adulto en B3. No necesita cambios en el runtime.
- **Si se quiere que transformarse cueste ki** (no es como B3): el código de la transformación solo comprueba. Habría que probar `w5 |= 0x0001` + `w9 = 4000` en la entrada P+K+G. No está verificado y no lo recomiendo.

### Qué necesita cada forma

| Necesidad | Origen |
|---|---|
| Modelo | Los 4 existen ya convertidos (traje1–4). Nada que derivar. |
| Moveset | El mismo para las 4 (el M1 de SB solo cambia 1 animación). `anm = [base]` → las formas 1–3 caen al de la forma 0, como el SSJ de Gohan adulto. |
| Animación de transformación | Injerto de 0x2E0/0x3E0 del donante 4 (animación global + AP). |
| Efecto | `0x64` del BSP del donante (el port usa el BSP de Gohan adulto, porque `tecnicas` está comentado). |
| Grito | k3 del banco `lang` del donante (voz de Gohan adulto de B3) hasta portar las voces de AR (`ZP2GHF*`, ATRAC3plus). |
| Aura | Tabla de auras del donante (`aura`, 18), con los rayos del SSJ2 vía el `char96` aura 4. |
| Caras de la barra de vida | 4 caras, renderizadas desde B00–B03. |
| Ficha de habilidades | 3 filas de transformación con «With over N Ki gauges». |
| Si algún día se pide una forma sin modelo | Recolorear el pelo (como B01 → SSJ2 oscuro 234,189,1) + aura 4. Hoy no hace falta. |

## 4. roster_build hoy y qué falta

**Ya funciona:**
- `formas = N`: el runtime solo puede **reducir** las formas del donante; el donante 4 tiene 4.
- Copia del `char372` y del `char96` del donante. Con eso se heredan niveles base, tipos (reversión), aura por forma, la tabla de físicas y el `+7`.
- `[[capsula]] tipo = "transformacion" forma = k`:
  - crea la cápsula (ID ≥ 596) con máscara `(1 << forma) − 1` y "exige la anterior";
  - genera `capsulas_forma` y la ficha (SCM) con las filas `0xFFFFFFFF` del donante;
  - no hereda las 23/24/25 del donante si el moveset es propio.
- `moveset = [...]` por forma (`anm[f]`; las que faltan = `0xFFFFFFFF` → forma 0).
- La cara de la barra de vida por forma, desde los modelos.

**Falta o está mal:**
1. **Requisito de ki por cápsula.** Hoy la plantilla de toda transformación es la 140 (LSSJ de Broly, +15 = 50), así que **toda transformación nueva pide 5 barras** (lo confirma el registro de Monster Form de Zarbon, 608). Además la ficha y el panel dicen 3, porque `capsulas.KI` está vacío fuera de IW.
   - Arreglo: clave `ki = N` → `rec[15] = 10·N` y `KI[id] = N`. Mejor aún: usar como plantilla la cápsula nativa del donante para esa forma (23/24/25), que trae la rareza, la máscara y el +15 correctos.
2. **Entrada P+K+G en el BCM** del port: no existe.
   - Arreglo: nueva función en `capsulas.py` que copie la entrada del donante (`w1=7`, `w5=4`, 0x2E0/0x3E0/0x3E0) cuando `formas > 1` y el BCM no la tenga, y que anule la de SB (`w0=0x20`, 0x500/0x700, 4000).
3. **Injerto en el ANM** de los bloques 0x2E0/0x3E0 del donante: ya existe `capsulas.csk_graft`, que se usa para el modo hiper. 0x3E0 del port es un dato muerto (el BCM ni el SPX lo usan), así que se puede sobrescribir.
4. **Modelo por forma** (solo para usar el SSJ2 propio, B02):
   - Nueva clave `modelo_forma = [0,1,2,3]`, con `modelos_por_traje = 4`.
   - En el runtime: escribir `c96 + 16 + 8·f + 2` tras copiar las formas del donante (~3 líneas en `ApplyCharacter`).
   - En el builder: emitirla y usarla en `hud_images`. Hoy usa `hds[min(f, per−1)]`, que con el mapa del donante [0,1,1,2] daría caras equivocadas.
   - Sin esta clave, la variante sin runtime es `modelos = [B00, B01, B03]` + `modelos_por_traje = 3`, pero el builder sigue necesitando ese mapa para las caras (o `ui/hud_1..4.png`).
5. `make_record` escribe la cápsula exigida como u32 en +16 (acaba en +18). **Funciona**, porque el juego mira +16 y +18, pero no es como los registros nativos.
6. Mod: `formas = 4`, 1 traje con 4 modelos y 3 `[[capsula]]` de transformación con nombre y `ki`.

### Plan

1. `capsulas.py`:
   - `add_b3_transform(ccm, donor_ccm)`, que copia la entrada P+K+G y quita la de SB;
   - plantilla de transformación = la cápsula de esa forma en el donante;
   - clave `ki`.
2. `roster_build.py`:
   - aplicar el paso 1 si `formas > 1` y falta la entrada;
   - injertar 0x2E0/0x3E0 del ANM del donante (`csk_graft`);
   - `modelo_forma` (roster.toml + caras de la barra de vida).
3. `src/roster_ext.cpp`: leer `modelo_forma`. Después, rebuild del exe y **recopiar las DLL canónicas** (trampa de §4 / §7 de AGENTS.md).
4. `personaje.toml` del port:
   - `modelos = [traje1..4]`, `modelos_por_traje = 4`, `modelo_forma = [0,1,2,3]`, `formas = 4`;
   - 3 `[[capsula]]` con `tipo = "transformacion"`, `forma = 1/2/3` y `ki = 4/5/6`.
5. `roster_build.py construir --force` + `deep.py` / `verify_final.py`. Comprobar en el roster generado:
   - `capsulas_forma = [0, a, b, c]`;
   - el byte +15 = 40/50/60 en los registros;
   - la entrada P+K+G presente;
   - 0x2E0/0x3E0 presentes en el CSK.

**Esfuerzo:** ~½–1 día de herramientas + 1 sesión de prueba en el juego. Si se descarta el SSJ2 propio, no hay cambio de C++ (solo Python).

### Riesgos

- **Animación de SB "↑E"** (0x500/0x700) que aún está en el BCM: hay que quitarla, o puede gastar ki sin transformar.
- **Grito y voz** de la transformación: serán los de Gohan adulto de B3 hasta portar las voces de AR (ATRAC3plus).
- **BSP propio:** si en el futuro el port usa su propio BSP de SB (`tecnicas.bin`), la línea AP del efecto `0x64` lanzará un efecto equivocado. Precedente: Zarbon, `--quitar-efecto 64`.
- **IDs de las cápsulas:** se renumeran (596+, por orden de mods). Las listas «Custom» guardadas en `mods/capsulas_custom.txt` pueden quedar desplazadas.
- **Trajes:** pasar de 4 trajes a 1 cambia el select. El runtime rellena hasta 8 trajes repitiendo el primero, así que no debería cerrarse.
- **Espada Z:** solo aparece si una animación de SB pide la mano izquierda 22.
- **Fallo lateral** (otro tema): `ApplyExtraCostume` usa `char372 +4` como «modelo dentro del traje», pero ese campo es el índice en `char96.formas[]`. Con Gohan adulto el traje extra funciona por casualidad (la última escritura gana); con otros personajes puede no funcionar.
- **Modo hiper (P+K+G+E):** no existe en el port. No choca con P+K+G, pero sigue pendiente.

## 5. Validación en el juego (cuando el usuario no use el PC)

1. Select: 1 traje de Gohan del Futuro, con el modelo Normal.
2. Edit Skills: aparecen las 3 cápsulas y no deja equipar SSJ2 sin SSJ (ni Potencial sin SSJ2).
3. Combate, P+K+G:
   - con 3 barras, no pasa nada;
   - con 4, pasa a SSJ (pelo B01, aura dorada, cara 2, grito);
   - con 5 desde Normal, pasa **directamente** a SSJ2 (rayos, pelo B02);
   - con 6, pasa a Potencial (pelo negro).
4. Recibir un golpe con menos de 1 barra → vuelve a Normal.
5. Quieto en SSJ, el ki tiende a 4 barras; en Potencial, a 5.
6. Pausa → lista de habilidades: «With over 4/5/6 Ki gauges», sin «3».
7. Combos, ráfagas, especiales y definitivo funcionan en las 4 formas, y no hay cierre al cambiar de modelo.
8. La CPU con Gohan del Futuro también se transforma.
9. Ya no existe el "↑+E" de SB.
10. La partida y la lista «Custom» se guardan y se cargan bien.

## 6. Preguntas abiertas

- ¿Fiel a Another Road (4 formas, recomendado) o canon (solo SSJ)?
- ¿SSJ2 con su modelo propio (B02, necesita runtime) o como B3 (modelo SSJ + rayos, solo Python)?
- Nombre de la 3.ª cápsula: «Potential Unleashed» o «Hidden Potential».
- ¿Mantener 4 trajes además de las formas? (No recomendado: AR no tiene trajes alternativos.)
- ¿Portar ya las voces de AR (ATRAC3plus) para el grito de transformación, o esperar?
- Campos +8 / +10 / +12 del registro por forma: su efecto exacto en combate no está confirmado (se heredan del donante).

## 7. Evidencia (esta carpeta)

| Archivo | Contenido |
|---|---|
| `evid_tabla_b3.md` | Las 17 transformaciones nativas: requisito, máscara, exige, nivel base, tipo, modelo, aura |
| `evid_char372_formas.txt`, `evid_char96_formas.txt` | Volcados de la imagen US (`out/analysis/guest_image/dbz3_us_image.bin`) |
| `evid_skc_transformaciones.txt`, `skills_ocr.json`, `b3_caps.json` | Catálogo de cápsulas, textos oficiales (OCR) y hoja PAL |
| `evid_funciones_ppc.txt` | `sub_82119108`, `sub_82119258`, `sub_82100760`, `sub_820FB5D0`, `sub_820F9970` |
| `evid_ar_formas.txt`, `ar_btl_cmn.txt`, `sb1_btl_cmn.txt` | Tablas de formas y listados de los AFS de SB |
| `evid_ar_ghf_mallas.txt`, `tex_BCGH*.png`, `pelo_formas.png` | Mallas, texturas y pelo de cada forma |
| `bcm_dump.py`, `forms.py`, `c96.py`, `skc.py`, `tabla_b3.py`, `fn.py`, `scan*.py`, `psp_afs.py`, `sb_bcm.py`, `psp_tex.py`, `psp_mesh.py`, `psp_hair.py`, `ar_formas.py` | Scripts (solo lectura) |
| `D:\DBZ3HD\explore\04_transformaciones\ar\` y `AR_BOOT.elf` / `SB1_BOOT.elf` | Extracciones grandes de las ISO |
