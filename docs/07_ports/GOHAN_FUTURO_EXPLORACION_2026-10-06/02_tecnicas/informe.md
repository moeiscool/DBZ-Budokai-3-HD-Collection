# Informe 02 — Técnicas de Shin Budokai → Budokai 3 HD (primer objetivo: Gohan del Futuro)

Fecha: 2026-10-06. Solo exploración / RE: no se ha tocado ningún fichero del proyecto ni se ha
lanzado el juego. Todo lo leído es PS2 GH (LE, mismo contenido que la HD en BE), las ISO de PSP
leídas en sitio (`iso.py`) y los ficheros del port actual. Scripts y salidas en esta carpeta
(lista al final); extracciones grandes en `D:\DBZ3HD\explore\02_tecnicas\`.

---

## 0. Resumen ejecutivo

1. **El port actual de Gohan del Futuro no tiene técnicas funcionales, y no es (solo) por
   `tecnicas.bin`.** Su moveset (`anm_forma1.bin`) y su cámara (`camara.bin`) son la
   "conversión comunitaria" `ghf_365/367`, que en realidad es **una copia byte a byte de los
   datos de Shin Budokai 2** (BSK, BCM, SPX idénticos; ver §2.4). El BSK de SB2 usa **líneas AP
   de 20 B** (B3: 16 B) y bloques de golpe de 160 B (B3: 128 B): el motor de B3 lee todas las
   propiedades de animación (golpes, efectos, voces, velocidad) desalineadas a partir de la
   segunda línea. Además su BCM usa semánticas de SB (cond 0x0004 = especial cuerpo a cuerpo en
   SB, pero **transformación** en B3), no tiene entrada de modo hiper (sin hiper no hay
   definitivo en B3), su `#ACC` (cámaras) está vacío y su `#SPX` es bytecode de SB (otra VM).
2. **`tecnicas.bin` (= `scratchpad/ghf/hd_BSP_GHF.amb`, mismo SHA-1) es el BSP de SB2 pasado por
   `ps2hd` como si fuera de B3.** Las capas de SB2 no son las de B3: `#AME` es otro sistema de
   partículas (nodos `Line/Sprite/Plane/Model/Gravity/Vortex…` frente a
   `Emitter/Particle/Field` de B3, cabecera 0x40 frente a 0x10), `#ASE` tiene bloques de 0xB0
   (B3 0xD0) y SB numera sus rayos con códigos que en B3 están **reservados** (0x15E/0x15F =
   aspecto de las ráfagas de ki). Comentarlo fue lo correcto; no hay nota escrita del motivo,
   pero los datos lo explican (§2.5).
3. **Lista real de técnicas de GHF (datos de SB2 Another Road):** 6 especiales + 2 definitivos,
   cada uno condicionado a un "booster" (equivalente SB de la cápsula). Kamehameha (rayo azul
   >E), bola de energía (>E), especial cuerpo a cuerpo (<E), explosión de corto alcance (>E),
   proyectil (<E), golpe + bola (<E); definitivos: rayo gigante azul (gemelo exacto del Super
   Kamehameha de Gohan adulto en SB2) y una onda magenta de tipo 12. Los nombres de SB2 son
   texturas, no texto: los nombres exactos quedan por confirmar (§2.3).
4. **En B3 una técnica = BCM (entrada/cápsula) → BSK (animación + AP1 golpe + AP7 efectos) →
   BSP (`#AST` energía / `#ASE` efecto visual / `#AME` partículas / texturas) y, solo para
   definitivos y agarres, SPX (cinemática) + `#ACC` (cámara).** Hallazgos nuevos con evidencia
   sobre los 38 personajes: el **coste de ki y las formas de una técnica viven en la cápsula**
   (`#SKC` +15 = ki en décimas de barra, 169/191 coinciden; +14 = máscara de formas), no en el
   BCM; el **beam struggle** se marca con el bit **0x2000** de la condición del BCM + la línea
   AP7 `c0=0x68`, y cada personaje con rayo tiene una **entrada de respuesta** (cond2 bit 0x4000,
   `c0=0x69`) (35/38 coinciden); **todo definitivo de B3 es P+K+G+E en modo hiper → golpe con HR
   tipo 3 → SPX ranura 0** (2º definitivo → ranura 1), con sus animaciones en los códigos
   **0x4A0+**; la ranura 20 es el agarre (P+G).
5. **Viable con un enfoque híbrido**: convertir lo que es compatible (BCM, BSK, `#AST`, `#ASE`,
   texturas, animaciones) y **reconstruir sobre el donante B3** (Gohan adulto, ID 4) lo que no
   lo es (partículas `#AME`, cinemática SPX + cámara del definitivo, entradas de beam struggle y
   de modo hiper). Casi todo es automatizable; lo artesanal es elegir/recolorear las partículas
   y montar la cinemática del definitivo. Esfuerzo estimado: 6–9 sesiones + 3 rondas de prueba
   en juego.

---

## 1. Cómo define B3 HD una técnica, de punta a punta

### 1.1 La cadena

```
Cápsula (#SKC, data_usi 4)  ── ki (+15), formas (+14), cápsula requerida (+16 u16), clase (+8)
   │  (id en el bloque BCM, w8)
BCM (#BCM/#CCM, bin CAM)    ── botones, dirección, condición (w4 en PS2 / w5 en HD), cond2 (w6),
   │                           códigos de ataque suelo/aire (w12..w15)
BSK (#BSK/#CSK, bin ANM)    ── código → sub-bloque de 48 B: animación (almacén 3 = AMM propio)
   │                           + AP0..AP7 (líneas de 16 B)
   ├─ AP1: ventana de golpe → código HR → bloque HR (8×16 B: daño, tipo, aturdimiento)
   │        HR tipo 3 → guion SPX (ranura = código)            → #SPX + #ACC (cámara) del bin CAM
   └─ AP7 [frame u16][id u8][act u8][categoría u32][valor u32]:
        c0 = acción del motor   (0/1 ráfaga de ki, 0x32–0x38 cargas, 0x64/0x66 congelar/descongelar,
                                 0x68/0x69 beam struggle; probables: 0x46/0x47 inicio/fin de rayo,
                                 0x28 transformar — según la nota comunitaria de IW y los datos)
        c1 = sonido, c2/c3 = voz (ranura del banco de gritos), c5/c6 = efectos de golpe/suelo
        c4 = enlace al BSP: código de #AST (energía) o de #ASE (efecto visual)
BSP (data_cmn 504–555; tabla por ID 0x82333208; `tecnicas =` en personaje.toml)
   ├─ AMB[0] = #AST (bloques "wk" 0xF0: tipo, código, duración, velocidad, hueso, texturas del
   │            rayo, daño, radio, aturdimiento, formas) + #AMT pequeño + #AME
   ├─ AMB[1] = #ASE (bloques 0xD0: códigos inicio/medio/fin, hueso, enlace a #AME, formas)
   │            + #AME (+ #AWV)
   └─ resto: #AMT grande (texturas de efectos), #AME, #AMO (+#AMM) modelos de efecto, #ATR, #AWV
```

### 1.2 Gohan adulto (ID 4: CAM 231, ANM 234, BSP 528) — `gohan_adulto_b3.txt`

| Técnica | Cápsula (ki, formas) | BCM | Códigos | Lo que hace (AP7 / HR) |
|---|---|---|---|---|
| Kamehameha | 26 (10 = 1 barra, 0x0F) | >E, cond **0x2002**, cond2 1 | 0x24B/0x34B (+ 0x24C, 0x24D tras combo) | c0 0x64 congela f8 · c4 0x04/0x05 carga (ASE wk0) · c4 0x10 · **c0 0x68 f34** · c0 0x66 f35 · **c4 0x0 = AST wk0** (rayo, 250 de daño) f46 · c0 0x46/0x47 |
| Kamehameha (respuesta) | 26 | >E, cond 0x0002, **cond2 0x4003** | 0x26C | igual pero sin 0x64/0x66, **c0 0x69** en vez de 0x68, + c0 0x40/0x43 |
| Soaring Dragon Strike | 27 (20 = 2 barras, 0x0F) | <E, cond 0x0002 | 0x24E (+0x24F/0x250) | 5 golpes AP1 (80/30/90/100/110, el último tipo 2 = despide) · c4 0x24, 0x2C–0x30 (ASE) · c4 0x131 |
| Modo hiper | — | P+K+G+E, cond 0x0400 | 0x259 | c7 0x4, c8 0x72 (probable cámara), c0 0x64, c4 0x12C, c0 0x2C, c0 0x66 |
| Super Kamehameha (definitivo) | 28 (50 = 5 barras, 0x0E = no en forma base, requiere 23 SSJ) | P+K+G+E, cond **0x000A**, cond2 0x8001 | 0x25A | carrera; AP1 f30 HR 0x68 → **tipo 3, código 0 = SPX ranura 0** |
| Agarre | — | P+G | 0x258 | AP1 HR 0xD0 → tipo 3, código 0x14 = **SPX ranura 20** (rutina común, BASE 0x480) |

Gohan joven (ID 3) sigue el mismo patrón (`gohan_teen_b3.txt`): Kamehameha cápsula 20 (0x24A,
respuesta 0x250), Soaring Dragon 21, Father-Son Kamehameha 22 (ranura 0, anims 0x4A0–0x4B6).

### 1.3 Ki y formas: en la cápsula, no en el BCM

En B3 los especiales tienen **w9 (ki) = 0** en el BCM (solo las ráfagas de ki tienen ki ahí:
350/375/400/425). El coste está en el registro `#SKC`:

```
cápsula 26 Kamehameha     clase 0x21 formas 0x0f ki 10 (1 barra)
cápsula 27 Soaring Dragon clase 0x21 formas 0x0f ki 20 (2 barras)
cápsula 28 Super Kameh.   clase 0x21 formas 0x0e ki 50 (5 barras) requiere 0x17 (SSJ)
cápsula 21/22 (Gohan joven) formas 0x04 = "solo SSJ2"  ← coincide con la ficha "Unusable without SSJ2"
```

`skc_ki_check.py`: en **169 de 191** cápsulas con texto "Consumes N Ki / N or more Ki", el byte
+15 vale exactamente 10·N (los 22 fallos son de OCR o de fusiones). Corrige
`docs/03_formatos/CAPSULAS_B3.md` (+15 no es "coste/nivel" sino ki; +16 es u16). Las cápsulas
nuevas de `roster_build` copian la plantilla (especial = 13 → ki 10; definitiva = 10 → ki 50),
que casualmente coincide con SB (1000 / 5000 de ki → 10 / 50).

### 1.4 Beam struggle (también responde a la petición de Discord de poder desactivarlo)

`beam_struggle_censo.txt` sobre los 38 personajes con BSP:
- Las entradas BCM con **bit 0x2000** en la condición son exactamente los códigos cuyo AP7 lleva
  **`c0 = 0x68`** (35/38 personajes; excepciones: Gohan joven en un remate, Buu M usa 0x2000
  para otra cosa, Omega Shenron tiene 0x68 sin el bit).
- Todo personaje con especial de rayo tiene **una** entrada extra de "respuesta" con **cond2 bit
  0x4000** (0x4003), misma cápsula y botones, cuyo AP7 no congela la pantalla y lleva
  **`c0 = 0x69`** (+ 0x40 / 0x43).
- Hipótesis (a validar en juego): 0x68 abre la ventana de choque durante la congelación; la
  entrada 0x4000 es el rayo de contraataque que entra en el forcejeo. Quitar las entradas
  cond2 0x4000 (o las líneas 0x68) debería desactivar los choques.

### 1.5 Definitivos: siempre cinemática SPX

`definitivos_b3.txt`: los 32 definitivos de B3 (29 personajes) son **P+K+G+E (0x0F), cond 0x000A** (0x001A si
dependen de la forma), su golpe tiene HR **tipo 3 → SPX ranura 0** (Vegeta y Buu M: 2º/3er
definitivo en ranuras 1/2). Las animaciones de la cinemática son bloques **sin AP** en los
códigos **0x4A0+** (Gohan adulto 16, Gohan joven 23, Goku 23): el guion SPX las empuja
(`08 20 a0 04`, `08 20 b0 04`) y lleva cámara (`#ACC` del bin CAM, 26 cámaras en Gohan adulto),
daño y efectos. Ranura 20 = agarre (BASE 0x480: códigos 0x480/0x481/0x488/0x489).
**Corrección** de notas anteriores (`b1port`, memoria): la ranura 0 no es "la acometida del
modo hiper" sino el definitivo (cuyo inicio es la persecución tipo Dragon Rush), y 0x4A0–0x4BB
no son "lanzamientos" sino las animaciones de la cinemática del definitivo.

### 1.6 El BSP y sus códigos reservados (`bsp_censo_b3.txt`)

- `#AST` tipos usados en B3: 0 rayo (57), 1 bola (22), 11 (17), 3 proyectil (6), 2 barrera (4),
  12 (Kaio-shin), 4–15 sueltos. El tipo 12 de SB existe en B3.
- **AST 0x15E / 0x15F = aspecto de las ráfagas de ki** (rayo, daño 0, radio 0.7, huesos 15/14 =
  manos) en Goku, Gohan niño/joven, Goten, Vegeta, Trunks, Piccolo, Ginyu, 17, Buu… El motor
  los usa con `c0 = 0/1` (ráfaga). Es por esto que Zarbon "disparaba ráfagas de Broly".
- ASE 0x67/0x68/0x69/0xC8 están en 20/38 BSP (enlazan a #AME del AMB principal 0x0E–0x10);
  ASE 0x64 en 12. Conviene **heredarlos del donante**.
- Categorías AP7: el enlace al BSP es la **categoría 4** (confirmado con la nota comunitaria
  "Special effects breakdown" y con los datos). La categoría 0 son acciones del motor; el
  `--quitar-efecto 64` de `b1port` quita la congelación (0x64), no un efecto del BSP.

---

## 2. Shin Budokai: dónde están las técnicas y qué hizo la conversión comunitaria

### 2.1 Ficheros (SB2 Another Road, `data_btl_cmn.afs`, con nombres)

`BCGHF.amb` (= CAM+ANM juntos: `#AMC` vacío, `#SPX`, `#BCM`, `#BSK`, 3 `#AMM`), `BCGHFM1.amb`
(forma SSJ, mismo BCM, BSK extra), `BCGHFB00–03.amb` (modelos), `BAR_GHF.amb` (aura),
`BSP_GHF.amb` (técnicas), `AC_GHF.spx` (modo arcade, no técnicas). Textos de combate en
`data_btl_us.afs` (`MSG_CMTGHF.ms` = frases de victoria; nombres de técnicas = texturas).

### 2.2 Diferencias de formato medidas (B3 ↔ SB2)

| Capa | B3 | SB2 | Conversión |
|---|---|---|---|
| BCM | bloque 64 B; códigos 0x2xx/0x3xx; ki de especiales en la cápsula; cond 0x0004 = transformar | mismo bloque; códigos **0x4xx/0x6xx**; w9 = 1000/5000; w8 = **booster**; cond **0x0004 = especial cuerpo a cuerpo**; definitivos **^E** cond 0x0008; sin modo hiper | por reglas (§3) |
| BSK | sub-bloque 48 B; **líneas AP 16 B**; HR 8×16 B | sub-bloque 48 B igual; **líneas AP 20 B** (1373/1373 huecos medidos); HR 8×20 B | quitar 4 B de cola; AP1 con hitbox s16 (SB) → s8 (B3) (`bsk_oracle_ghl.txt`) |
| SPX | cabecera `20/74/15`, librería común embebida, ranuras 0/20 | cabecera `20/1B4/65` (101 ranuras), sin la librería, otra VM; definitivos y especiales **sin** SPX (solo agarre = 20 y 0/1 de mecánicas comunes) | no se puede convertir: se usa el del donante |
| `#AST` | 0xF0 | 0xF0, **mismos campos** (`ast_b3_vs_sb2_kamehameha.txt`); SB añade 2º daño (+0xCA) y +0xEC | copiar + renumerar código + reenlazar AME/AMT |
| `#ASE` | 0xD0; hueso +0x80; formas +0xAA | **0xB0**; hueso +0x48; formas +0x9E; códigos +0x6A igual | remapeo por oráculo (`ase_oracle_ghl.txt`, 7 pares GHL) |
| `#AME` | `#AME 02 00 00 00 n 10 00 00 00`, nodos Emitter/Particle/Field | `#AME 00 00 02 00 n 40 00 00 00 … 00 00 80 3f`, nodos Line/Sprite/Plane/Model/Gravity/Vortex/Omni Emitter… (`ame_nodos.txt`) | **no convertible**: sustituir por #AME del donante y recolorear |
| `#AMT` | PS2 psm 0x13/0x14 | PSP psm 4/5 con swizzle | `psp_amo.convert_amt` (ya existe) |
| Daño | — | SB ≈ B3 × 1,33–1,6 (Kamehameha 400 vs 250; jab 40 vs 30) | escalar ×0,63 (como B1) |

Curiosidad útil: el BSP de **Gohan adulto en SB2** (`BSP_GHL`) desciende del de B3 (mismos
códigos ASE 0x04/0x05, 0x24, 0x2C–0x2F; mismo AST código 0 Kamehameha): sirve de **oráculo**
para mapear campos SB→B3, igual que los pares PS2/HD sirvieron para `ps2hd`.

### 2.3 Técnicas reales de Gohan del Futuro (SB2) — `ghf_sb2.txt`

| # | Entrada (booster) | Código | Efecto (BSP SB) | Lectura |
|---|---|---|---|---|
| S1 | >E (12), ki 1000 | 0x460 (+0x461 remate) | AST 0x15F **rayo** tipo 0, tex 44/45 **azules**, 400/560 | **Kamehameha** (texturas = las del Kamehameha de GHL) |
| S2 | >E (2) | 0x488 (+0x489) | AST 0x160 bola tipo 1, hueso 14, 400/560 | bola de energía (¿Masenko?) |
| S3 | <E (6), **cond 0x0004** | 0x48B (+0x48C) | golpe AP1 35 + c4 0x142 (común) | especial cuerpo a cuerpo / embestida |
| S4 | >E (1) | 0x491 (+0x492) | AST 0x162 bola lenta, radio 17, dura 8–14 | explosión de corto alcance |
| S5 | <E (8) | 0x495 (+0x496) | AST 0x161 proyectil tipo 3, 500/600 | ráfaga/proyectil |
| S6 | <E (1) | 0x49C (+0x49D) | golpe + AST 0x15E bola, 500/650 | golpe y bola |
| U1 | ^E (1), ki 5000, cond 0x0008 | 0x499 | AST 0x168 **tipo 12**, 900, juggle, tex 24/57 **magenta** | definitivo 1 (onda magenta) |
| U2 | ^E (14), ki 5000 | 0x464 | AST 0x169 rayo **radio 23, 1000/1600**, tex 44/45 azules | definitivo 2 = gemelo exacto del **Super Kamehameha** de GHL en SB2 (mismos valores) |

Cada AST va en pareja (normal / potenciado). Ningún especial ni definitivo de SB2 usa SPX: el
"definitivo" de SB es un rayo con congelación (`c0 0x67` … `0x66`), no una cinemática. Los
nombres oficiales no están como texto en la ISO (búsqueda UTF-16/ASCII en `data_sys_us`,
`data_btl_us`, `BOOT.BIN`: sin resultados); son texturas de menú.

### 2.4 La "conversión comunitaria" es una copia (`oracle_ghf.py` del explorador 01)

```
ghf_367.bin: #BSK 157824 = SB2 BCGHF hijo 3 (idéntico) · 3 #AMM = hijos 5,6,7 (idénticos, formato SB)
ghf_365.bin: #AMC 32 B, #BCM 5996, #SPX 4136 = hijos 0, 2, 1 de BCGHF (idénticos)
```

El port del proyecto convirtió las AMM con `sb_amm.py` (bien) pero dejó el BSK tal cual
(`BSK del port == SB2: True`). Así lee B3 el AP7 del Kamehameha (código 0x460) en el `#CSK` HD:

```
SB2 real (20 B):  01 00 03 02 03 00 00 00 4a 00 00 00 00 00 00 00 00 00 00 00
                  0a 00 04 02 02 00 00 00 1c 08 00 00 …  (voz)   …  2d 00 09 02 04 00 00 00 5f 01 … (rayo 0x15F)
B3 leyendo 16 B:  f1 id3 cat3 val=0x4a | f0 cat33816586 val=0x2 | f0 cat0 val=0x207000b | f10 cat0 val=0 | …
```

### 2.5 Por qué `tecnicas.bin` está comentado

No hay nota escrita (handbacks, memoria, scratchpad), pero `personaje_full.toml` (14:22 del
04-10) lo tenía activo y el definitivo lo comenta. Los datos muestran que no podía funcionar:
- `#ACE` del port: `23 41 43 45 00 02 00 00 00 00 00 14 00 00 00 40 … 3f 80 00 00` frente al de
  B3 `23 41 43 45 00 00 00 02 00 00 00 08 00 00 00 10`: B3 leería versión/recuento/inicio
  erróneos en todos los `#AME`.
- `#CSE` con 18 bloques de 0xB0 que B3 recorre a 0xD0.
- AST con códigos 0x15E/0x15F (= ráfagas de ki en B3) con 400–650 de daño.
- Además el BSK no los alcanzaría (AP7 desalineado), así que no aportaba nada y sí riesgo.

### 2.6 Otros problemas del port actual que afectan a las técnicas

- `[[capsula]] reemplaza = 12, 2, 1, 8, 14`: el booster 1 lo comparten S4, S6 **y** U1 → la
  cápsula "Special 3" activaría también el definitivo U1; S3 (booster 6) se queda fuera.
- S3 lleva cond 0x0004 → B3 lo trata como **transformación** con <E (y `formas = 1`).
- Sin entrada de modo hiper (cond 0x0400) → en B3 los definitivos no son alcanzables; los
  definitivos de SB se pulsan con ^E, no con P+K+G+E.
- `#ACC` vacío (SB no usa cámaras): cualquier guion o línea de cámara del donante no tendría
  datos.
- El `#SPX` es de SB: si un agarre conectase (HR tipo 3 → ranura 20) B3 ejecutaría bytecode de
  otra VM (riesgo de cuelgue).
- `c0 = 0x7D0` en U2: código de SB desconocido para B3 → quitarlo.

---

## 3. Estrategia: "reformular" las técnicas de SB sobre el sistema de B3

**Principio**: el personaje se construye **sobre el donante B3** (Gohan adulto, ID 4: mismo
esqueleto por sufijo `GHL_*` ↔ `GHF_*`, mismas técnicas de familia Kamehameha) y se le injerta
lo propio de SB que sea compatible. Lo que B3 exige y SB no trae (modo hiper, cinemática,
cámara, entradas de beam struggle, efectos reservados) viene del donante.

### 3.1 Por capas

1. **BCM** (automático, reglas):
   - códigos 0x4xx/0x6xx → códigos libres 0x26x–0x27x / 0x36x–0x37x del rango de B3 (evita
     chocar con 0x480/0x488/0x489 del agarre del donante y con 0x4A0+ de la cinemática);
   - SB cond 0x0004 → 0x0002; booster → cápsula nueva (una por técnica, no por booster);
   - w9 → 0 y el ki a la cápsula (+15 = w9/100: 10 especiales, 50 definitivos);
   - remates (cond2 0x8000/0x8101, ventana 0x7530) → patrón de remate de B3 (hijos de combo
     con la misma cápsula, como 0x24C/0x24D del donante);
   - definitivos ^E → P+K+G+E cond 0x000A cond2 0x8001; injertar la entrada de **modo hiper**
     del donante y ordenarla delante (`capsulas.hyper_first`).
2. **BSK** (automático; compartido con el explorador de moveset): líneas 20 → 16 B, HR 160 →
   128 B, AP1 hitbox s16 → s8, daño ×0,63, voces c2/c3 a ranuras del banco de gritos
   (`gritos.py`), quitar códigos c0 desconocidos (0x7D0). Validable offline contra el par
   SB2-GHL / B3-GHL (mismos golpes).
3. **BSP híbrido** (automático + ajuste visual):
   - base = BSP del donante (528) completo → conserva ASE 0x67–0x69/0xC8/0x64, AST 0x15E/0x15F
     de ráfaga, `#AWV`, modelos y su `#AMM`;
   - añadir los AST de SB (copia de 0xF0) **renumerados** a códigos libres (0x1–0x9…), con las
     texturas del rayo importadas al `#AZT` grande del donante (`psp_amo.convert_amt` +
     `azt_append`) y el AP7 c4 del BSK reescrito al nuevo código;
   - añadir los ASE de SB remapeados 0xB0 → 0xD0 (tabla del oráculo GHL; huesos por tabla);
   - partículas: cada ASE/AST de SB se enlaza a un `#AME` **del donante con el mismo papel**
     (carga en manos = ASE 0x04/0x05 del Kamehameha; boca del rayo; impacto) y se recolorea
     (bloques de color RGBA float y texturas). El magenta de U1 y el azul de S1/U2 salen de las
     texturas de SB.
4. **Definitivo cinemático (U2 → "Super Kamehameha" de GHF)**: injertar del donante la entrada
   BCM, el bloque 0x25A (carrera + HR tipo 3 código 0), el **SPX completo** (ranuras 0 y 20),
   el **`#ACC` + `#ACL`** y las animaciones 0x4A0–0x4AF (`b1port.bsk_graft` + `Amm`); opcional:
   cambiar la animación del disparo final por la de SB (anim 132) **remuestreada a la duración
   de la del donante**, para no tocar los tiempos del guion. Los efectos del guion apuntan al
   BSP del donante, que está en la base híbrida.
5. **Segundo definitivo (U1, onda magenta tipo 12)**: dos opciones. (a) Especial potente no
   cinemático (es lo que es en SB; seguro). (b) 2º definitivo en ranura 1 (precedente: Vegeta
   cápsula 44, Buu M) injertando una segunda cinemática de otro donante: más trabajo y riesgo.
   Recomendado (a) en la primera versión.
6. **Beam struggle para S1 (Kamehameha)**: marcar sus entradas con 0x2000, insertar en su AP7
   `c0 0x64` (inicio), `c0 0x68` y `c0 0x66` anclados al frame de disparo (en el donante: 38,
   12 y 11 frames antes del c4 del rayo) y crear la entrada de respuesta cond2 0x4003 con su
   variante (sin 0x64/0x66, `c0 0x69`, 0x40, 0x43). Todo copiando el patrón de 0x24B/0x26C.
7. **Cápsulas**: 6 especiales + 1–2 definitivos con nombre provisional, ki de SB (+15), formas
   (+14 = 0x01 con `formas = 1`), sin "reemplaza" por booster sino por técnica.

### 3.2 Qué se automatiza y qué es artesanal

| Automatizable (herramienta `sbport.py` o ampliar `b1port`/`ps2hd`) | A mano / iterativo |
|---|---|
| BSK 20→16, HR, AP1 hitbox, daño, remapeo de códigos | Elegir qué #AME del donante representa cada efecto de SB |
| BCM: conds, boosters → cápsulas, ki, hiper, remates | Recolorear partículas hasta que "parezcan oficiales" |
| AST: copia, renumeración, texturas, enlaces | Qué animación de GHF sustituye a cuál en la cinemática |
| ASE: remapeo 0xB0→0xD0 por oráculo | Equilibrio de daño/ki fino |
| Injerto de hiper, definitivo (SPX, ACC, 0x4A0+), agarre | Nombres oficiales de las técnicas |
| Patrón de beam struggle anclado al frame de disparo | Decidir U1 como especial o como 2º definitivo |
| Comprobaciones offline (todas las líneas AP con categorías válidas, códigos c4 existentes en el BSP, sin 0x15E/0x15F con daño, estilo `deep.py`) | |

---

## 4. Plan concreto, riesgos, esfuerzo y validación

| Fase | Contenido | Esfuerzo | Validación |
|---|---|---|---|
| F0 | Conversor SB→B3 de BSK/BCM (con el explorador de moveset) + comprobador offline | 1–2 sesiones | offline vs par GHL; en juego: golpes y combos de GHF |
| F1 | BSP híbrido (donante + AST/ASE de SB + texturas) y AP7 c4 reescritos | 1–2 sesiones | offline: cada c4 existe; en juego: S1–S6 disparan su energía |
| F2 | Partículas: mapeo de papel + recoloreado | 1 sesión + iteraciones | capturas en juego frente a vídeo de SB2 |
| F3 | Hiper + definitivo cinemático injertado (U2) + agarre del donante | 1–2 sesiones | en juego: LT/L2, P+K+G+E, cinemática completa sin poses rotas |
| F4 | Beam struggle (S1) + cápsulas (ki/formas/nombres) | 0,5 sesión | en juego: Kamehameha contra Kamehameha |
| F5 | U1 como especial potente; voces de técnicas | 0,5 sesión | en juego |

Riesgos:
- **Motor B3 + datos parciales de SB**: cualquier código c0 desconocido o enlace AME roto puede
  cerrar el juego → limpiar con lista blanca de categorías/valores vistos en B3.
- **Cinemática**: las animaciones de la víctima salen del AMM 2 (3712 anims genéricas); el de
  SB tiene el mismo recuento pero otro contenido → usar el AMM 2 del donante.
- **Huesos extra de GHF** (`LOBI1-3`, faldón): quedan en reposo durante las animaciones del
  donante; puede notarse.
- Las ranuras ASE 0x67–0x69/0xC8 y el byte +20 de la cápsula (0x45 heredado de Goku en el
  definitivo nuevo) tienen función no confirmada.
- Choque con el trabajo de otros exploradores (moveset, transformaciones): F0 es común.

En juego hace falta validar (el usuario guía hasta el personaje): golpes normales tras F0;
cada especial S1–S6 (efecto, daño, ki); modo hiper y definitivo; beam struggle S1 contra un
rayo de B3; que la ráfaga de ki (E) siga con su aspecto y daño normales; Edit Skills con las
cápsulas nuevas.

---

## 5. Preguntas abiertas

1. Nombres oficiales de S2–S6 y U1 (¿Masenko? ¿la onda magenta?): confirmar con el usuario /
   Kanzenshuu, o descodificar las texturas de la lista de comandos de SB2.
2. ¿U1 como especial potente (recomendado) o como 2º definitivo cinemático?
3. ¿Se quiere beam struggle para GHF desde el principio?
4. ¿Qué hace exactamente cond2 0x4000 y c0 0x68/0x69 (prueba A/B en juego antes de ofrecer el
   interruptor de Discord)?
5. Significado de `#SKC` +20 (4 en los especiales de Gohan, 0x48 en su definitivo) y de las
   categorías AP7 7/8 (¿cámara del modo hiper?).

---

## 6. Evidencias y scripts (en esta carpeta)

- `tec_b3.py` — cadena BCM→BSK→BSP→SPX de un personaje B3 (`python tec_b3.py <cam> <anm> <bsp>`).
- `tec_sb.py` — lo mismo para SB2 con sus formatos (`python tec_sb.py BCxxx.amb BSP_xxx.amb`).
- `tree.py`, `sbafs.py` (copia del explorador 01) — árbol #AMB LE/BE; lector de AFS de PSP.
- `skc_ki_check.py` / `skc_ki_check.txt` — ki y formas en el `#SKC`.
- `gohan_adulto_b3.txt`, `gohan_teen_b3.txt`, `goku_b3.txt`, `nappa_b3.txt` — cadenas B3.
- `ghf_sb2.txt`, `ghf_m1_sb2.txt` — técnicas de GHF en SB2 (forma base y SSJ).
- `beam_struggle_censo.txt`, `definitivos_b3.txt`, `bsp_censo_b3.txt` — censos de los 38.
- `ast_b3_vs_sb2_kamehameha.txt`, `ase_oracle_ghl.txt`, `bsk_oracle_ghl.txt`, `ame_nodos.txt`
  — comparaciones de formato B3 ↔ SB2.
- `texturas_rayos_montaje.png` — texturas: U1 (magenta 24/57), S1/U2 (44/45), GHL SB2 (34), B3 (42).
- `sb2_btl_us.txt`, `sb2_sys_us.txt` — listados de AFS de SB2.
- En `D:\DBZ3HD\explore\02_tecnicas\`: bins PS2/HD extraídos (528, 529, 231, 234, 241, 245…),
  `BSP_GHL_sb2.amb`, `BCGHL_sb2.amb`, `BSP_CMN_sb2.amb`, `menu_*.amb`, texturas PNG; caché de
  `afs_pair` en `tmp\` (se fijó `TEMP` ahí para no escribir fuera).
