# Movesets de Shin Budokai 1 / 2 (PSP) → Budokai 3 HD

Informe de exploración y RE. Primer objetivo: Gohan del Futuro (GHF). Fecha: 2026-10-06.

- No se ha lanzado el juego y no se ha tocado ningún fichero del proyecto.
- Todo lo que se cita se ha medido con los scripts de esta carpeta. Se leen las ISOs en su sitio, sin extraerlas.
- Este informe se escribió sin leer `AGENTS.md`; las secciones que cita se consultaron con grep.

---

## 0. Resumen ejecutivo

1. **SB1 y SB2 usan el mismo motor que B3, pero hay diferencias que rompen la compatibilidad.**
   - Los contenedores y las versiones coinciden: `#AMB` v3, `#BSK` v4, `#AMM` v2, `#BCM`, y `#SPX ver 0.01` con la misma máquina virtual.
   - Por dentro cambian varias disposiciones:
     - las líneas AP miden **20 B** (16 en B3);
     - los bloques de reacción al golpe (HR) miden **160 B** (128 en B3);
     - las animaciones del AMM están **comprimidas**, con una tabla de 8 B (16 en B3);
     - el **espacio de códigos de ataque está renumerado**;
     - los **índices del almacén global de animaciones** son otros;
     - las **funciones nativas del SPX** están renumeradas.
2. **La "conversión comunitaria" de Gohan del Futuro (`ghf_365/367`) no convierte nada.**
   - Es un reempaquetado byte a byte de los hijos de `BCGHF.amb` de SB2.
   - El port actual `port_gohan_futuro` solo descomprime el AMM (con `sb_amm.py`). El `#CSK` es el BSK de PSP sin cambios: 157 824 B en los dos.
   - Por eso B3 lee los golpes, las ventanas de impacto, el daño y los efectos con el paso equivocado. **No se cuelga, pero casi seguro que pega mal.** Hay que validarlo en el juego.
3. **Las diferencias son sistemáticas y se pueden medir con oráculos.** Hay 17 personajes que están a la vez en SB y en B3 (Goku, Vegeta, Piccolo, Cell, Buu ×3…). Al casar sus animaciones por pose salen:
   - el 80 % de las animaciones propias son **idénticas** (0,0°);
   - el 78 % de las animaciones del almacén global son **idénticas** (206 de 265);
   - una tabla estable de **códigos de motor SB → B3** (96 códigos);
   - la **escala de daño**: B3 = 0,85 × SB (mediana de 8 847 golpes);
   - qué campos coinciden en el BCM, el HR y los efectos.
4. **Veredicto: es VIABLE un `sbport.py` genérico, al estilo de `b1port.py`.**
   - Saldría mejor que el port de B1, porque aquí las animaciones, los efectos comunes y los campos de golpe se conservan.
   - Lo único que no se puede portar directamente son los guiones SPX propios de SB: llaman a funciones nativas renumeradas. Afectan a pocos golpes: 4 en GHF, que llaman a las ranuras SPX 30/40/50.
   - Se usaría el SPX del donante B3, como ya hace `b1port`.
5. **Esfuerzo estimado:** unos 5–7 días de trabajo para GHF completo, con las herramientas y 2–3 rondas de prueba en el juego. Después, unos 2–3 días para generalizarlo a los 24 personajes de SB2 y los 18 de SB1. Los efectos propios (BSP) y las voces son trabajo aparte.

---

## 1. Estructura de las ISOs PSP

Las dos ISOs están en `ps2_games/` y se leen con `mod center hd/iso.py`. Contienen AFS con **tabla de nombres** (48 B por entrada, el puntero va tras la tabla de offsets). El lector está en `sbafs.py`.

| Fichero | SB1 (ULUS_10081) | SB2 (Another Road) | Contenido |
|---|---|---|---|
| `USRDIR/data_btl_cmn.afs` | 206 entradas, 132 MB | 286 entradas, 185 MB | Todo lo de combate por personaje (ver abajo) |
| `data_btl_voice_us.afs` (+ `_jp`) | 12,7 MB | 19,1 MB | Voces de combate `BC<XXX>SND.amb`, `BC<XXX>M<n>S.amb` (cabecera **PPHD** + PS-ADPCM/VAG) y frases `ZP1/ZP2<XXX>A0` (RIFF ATRAC3plus) |
| `data_sys_*.afs` | — | — | Menús, imágenes, voces de sistema |
| `PSP_GAME/SYSDIR/BOOT.BIN` | ELF en claro | ELF en claro (3,1 MB) | No contiene nombres de fichero: el juego usa índices AFS (se buscó `BCGHF`; solo aparece `MSG_SYS_CHAR_GHF`) |

Los listados completos están en `sb1_btl_cmn.txt` y `sb2_btl_cmn.txt` (índice, tamaño, nombre y cabecera).

**Ficheros de cada personaje en `data_btl_cmn.afs`** (por ejemplo, GHF en SB2):

| Entrada | Nombre | Contenido |
|---|---|---|
| 70 | `BCGHF.amb` | **Moveset**: `#AMB` [AMC (stub de 32 B), SPX, BCM, BSK, —, AMM propio, AMM2, AMM3] |
| 71–74 | `BCGHFB00..B03.amb` | Modelos (trajes o formas): [`#AMO`, `#AMT`, `#RPT`]. El `#RPT` "LOBI1/AROBI1" es la **física del cinturón**, y es la tira de cinturón que el port tiene pendiente. |
| 75 | `BCGHFM1.amb` | El mismo moveset más un **segundo BSK pequeño** que sobrescribe códigos sueltos (en GHF solo el `0x19F`; en GOK `0,18c,18d,190,191,198-19a,19f`). Va ligado a un modelo concreto B0n; falta confirmar cuál. |
| 76 | `BAR_GHF.amb` | Aura: [AMT + AME…, AMO] |
| 77 | `BSP_GHF.amb` | Efectos de técnicas: `#AMB` de [AST/ASE, AMT, **`#AME` v0x00020000** con cabecera 0x40], **otro formato** que el `#AME` v2 de B3 |
| 164 | `AC_GHF.spx` | SPX aparte, de 24 ranuras; su uso no está identificado |
| 209 | `EV_ACGHFED.spx` | SPX de evento (`EV_AC<XXX>00/01/02/ED`) |
| 0 | `BCCMN.AMB` | Común: [AMT, BSK (0x800 códigos, 1 HR), **AMM global** (265 animaciones, almacén 0), AMM (5 422)] |

**Personajes (código → B3).** El ID B3 está en `corpus.PAIRS`.

| Código | SB1 | SB2 | Personaje | ¿Está en B3? |
|---|---|---|---|---|
| GOK | ✓ | ✓ (huesos XGK4) | Goku | ID 0 |
| VGT | ✓ | ✓ | Vegeta | ID 7 |
| PIC | ✓ | ✓ | Piccolo | ID 11 |
| KLL | ✓ | ✓ | Krilin | ID 10 |
| GHM | ✓ | ✓ | Gohan adolescente | ID 3 |
| GHL | ✓ | ✓ | Gohan adulto | ID 4 |
| TRX | ✓ | ✓ | Trunks (esqueleto XTRX) | ID 8 |
| TRF | | ✓ | Trunks, otra variante (XTRX; probablemente del Futuro con espada) | parcial |
| FRZ, CEL, COO, BRL, 18G | ✓ | ✓ | Freezer, Cell, Cooler, Broly, C-18 | 27, 33, 38, 40, 30 |
| BUS | ✓ | ✓ | Kid Buu (XBUS) | 36 |
| BUL, BUM | | ✓ | Majin Buu (XBUL), Super Buu (XBGX) | 34, 35 |
| BDK, DBR | | ✓ | Bardock, Dabura | 39, 37 |
| **GHF** | | ✓ | **Gohan del Futuro** | **no** |
| **GGT** | ✓ | ✓ | **Gogeta SSJ** (esqueleto VGT) | no (B3 solo trae Gogeta SSJ4 como forma) |
| **VTO** | ✓ | ✓ | Vegetto (esqueleto VGT) | solo como fusión de B3 |
| **GTX** | ✓ | ✓ | Gotenks | solo como forma de Goten |
| **JNB, PKH** | ✓ | ✓ | Janemba, Pikkon | no (ya hay ports de IW en el proyecto) |

---

## 2. El oráculo comunitario: la conversión GHF no transforma nada

`oracle_ghf.py` compara cada hijo de `ghf_365.bin` / `ghf_367.bin` (`modding resources/Infinite World to Budokai 3 Moveset Ports/Future Gohan (Shin Budokai)/`) con los de `BCGHF.amb`:

```
ghf_367.bin 0 #BSK 157824  idéntico a SB2 hijo [3]
ghf_367.bin 1 #AMM 1737148 idéntico a SB2 hijo [5]
ghf_367.bin 2 #AMM 176116  idéntico a SB2 hijo [6]
ghf_367.bin 3 #AMM 9756    idéntico a SB2 hijo [7]
ghf_365.bin 0 #AMC 32      idéntico a SB2 hijo [0]
ghf_365.bin 1 #AML 5       (stub, igual que el #AML de 5 B de todos los B3)
ghf_365.bin 2 #BCM 5996    idéntico a SB2 hijo [2]
ghf_365.bin 3 #SPX 4136    idéntico a SB2 hijo [1]
```

La comunidad solo repartió los hijos en el formato ANM = [BSK, AMM, AMM, AMM] y CAM = [AMC, AML, BCM, SPX].

En el mod actual (`out/build/win-amd64-release/mods/port_gohan_futuro/moveset/anm_forma1.bin`):
- el `#CSK` mide 157 824 B, el mismo BSK de PSP pasado a BE con `ps2hd.conv_bsk`, que da por hecho líneas de 16 B;
- el `#ACM` sí está descomprimido: su tabla es `00000009 00000000 00000018 …`, es decir, pasó por `awo_tools/sb_amm.py`.

---

## 3. Diferencias de formato, con evidencia

### 3.1 AMM (animaciones): **resuelto ya por `awo_tools/sb_amm.py`**

- **SB:** tabla de 8 B `[u16 fotogramas][u16 opciones][u32 huesos]`. Las pistas están comprimidas: claves en u8 y valores s16/f32.
- **B3:** tabla de 16 B `[flags 9/0x19][0][fotogramas][ptr]`.
- Ejemplo (`BCGHF` AMM, entrada 0): SB `18000000 98040000` frente al ACM del mod `00000009 00000000 00000018 00000910`.
- Para comparar se usó `sb_amm.convert`. Con eso, las animaciones casan por pose al 0,0° (ver 3.6). El descompresor está validado.

### 3.2 BSK: **líneas AP de 20 B** (B3: 16 B)

Mismo golpe, primer combo de Gohan adulto, SB2 `GHL 0x400` frente a B3 `ID 4 0x200` (`apdump.py`):

```
SB2  AP tipo 1 (golpe), 20 B por línea:
     0900 0001 0000 0000 0100 0f16 0000 0000 0000 0000   <- fotograma 9, HR 0, props 1, parte 0x0f, radio 0x16
     0d00 0000 ffff ffff 0000 0f00 0000 0000 0000 0000   <- cierre (HR 0xFFFF)
B3   AP tipo 1, 16 B por línea:
     0800 0001 0000 0000 0100 0e00 0000 0000
     0b00 0000 ffff ffff 0000 0e00 0000 0000
```

- Al leerlas de 16 en 16, la línea 2 de SB sale como `0000 0000 0d00 0000 ffff ffff …`: fotograma 0, HR 0x0d, props 0xFFFF. Eso es basura, y es lo que el juego lee hoy en el port de GHF.
- Con un paso de 20 B, las distribuciones de SB2 coinciden con las de B3: los mismos tipos AP 0–7 y las mismas clases de efecto.
- Los 4 bytes de cola valen 0 en todas las líneas, salvo en las de tipo 1 (`apstats.py`).

**Línea de golpe (tipo 1), campos por byte** (`t1hit.py`, comprobado con golpes casados en `pairhits.py`):

| Campo | SB (20 B) | B3 (16 B) |
|---|---|---|
| fotograma, idx, 0x01 | +0..+3 | +0..+3 |
| código HR (u16; SB llega a >255 bloques) | +4 | +4 |
| props | +8 | +8 |
| parte del cuerpo | +10 | +10 |
| radio | **+11** | **+12** (+11 = 0) |
| posición x, y, z | **3 × s16 en +12, +14, +16** | **3 × i8 en +13, +14, +15** |

Ejemplo casado (Krilin, SB `0x18c` ↔ B3 `0xfc`):

```
SB 1200 0001 0601 0000 6000 0496 0000 0000 0000 0000
B3 1200 0001 5d00 0000 6000 0400 9600 0000
```

### 3.3 BSK: **bloques HR de 160 B** (8 líneas de 20 B; B3: 8 de 16 B)

- La sección HR de SB mide `n_hr × 160` en los 42 personajes de SB1 y SB2.
- Las líneas tienen los mismos campos que B3: `[daño u16][grunt u8][visual u8][tipo u16][código u16][empuje f32][específico u32]`, más una cola de 4 B que vale 0 en las 53 296 líneas.
- Ejemplo del mismo golpe:

```
HR SB 7800 c800 0200 0200 0000 8c42 0000 0000 0000 0000
HR B3 7800 40e7 0200 0200 0000 8c42 0000 0000
```

- Coincidencia de campos sobre 70 872 líneas casadas (`hrcols.py`): tipo 84 %, código 79 %, empuje 73 %, grunt/visual 70 %, daño 21 %. El daño sale distinto porque está reequilibrado.
- **La conversión de una línea HR es truncarla a 16 B.**
- **Escala de daño (`dmgscale.py`):** B3/SB = **0,846** de mediana, con cuartiles 0,67 / 0,85 / 0,92 sobre 8 847 golpes. Por personaje va de 0,71 (C-18) a 1,0 (Majin Buu). Recomendación: multiplicar por 0,85.

### 3.4 BSK: sub-bloque de animación (48 B), casi idéntico

Comparación de 18 468 sub-bloques casados (`subblk.py`):

- +6, +0xC, +0xE, +0x12–0x16 y +0x24: 100 % iguales.
- **+0x10:** SB lleva el bit **0x80** donde B3 lleva 0 (5 452 casos). Es una bandera exclusiva de SB y hay que quitarla.
- **+0x1C–+0x22:** campos de enlace o código siguiente (`0x1a7`, `0x130`, `0x1a0`, `0xffff`). Son **códigos** y hay que pasarlos por la tabla de remapeo.
- +0x28 / +0x2C: número y offset de las AP. Se recalculan.

### 3.5 BSK: **el espacio de códigos está renumerado**

Códigos definidos de media por personaje y por rango de 0x100 (`apstats` / corpus):

```
SB1/SB2: 0x0:12  0x100:53  0x200:7  0x300:8  0x400:81  0x500:17  0x600:81  0x700:17  0x800:6-9
B3     : 0x0:23  0x100:6   0x200:161 0x300:117 0x400:22
```

Disposición deducida:

| SB | B3 | Qué es |
|---|---|---|
| 0x000–0x1FF (suelo), 0x200–0x3FF (aire, **+0x200**) | 0x000–0x0FF / 0x100–0x1FF (aire, **+0x100**) | Posturas y movimientos básicos que dispara el motor |
| 0x400–0x5FF suelo, 0x600–0x7FF aire | 0x200–0x2FF suelo, 0x300–0x3FF aire | Ataques que lanza el BCM (numeración propia de cada personaje) |
| 0x500+i / 0x508+i / 0x510+i | 0x2E0+i / 0x2E8+i / 0x2F0+i | Familias de transformación (almacén global 6/7/8 ↔ 14/15/16) |
| 0x700+i / 0x708+i | 0x3E0+i / 0x3E8+i | Las mismas, en el aire |
| 0x800, 0x801, 0x808, 0x809 | 0x480, 0x481, 0x488, 0x489 | **BASE de agarre**: el SPX 20 hace `push16 BASE` en los dos juegos |

**Tabla estable de códigos de motor** (`enginemap.py` → `engine_map.json`). Se casan por animación en los 17 pares y se aceptan con un 60 % de acuerdo o más:

```
0->0  1->2  3->4  6->7  7->8  8->9  9->a  a->b  15->10  16->11
40->3c 41->38 42->39 43->3a 44->13b
194..197->f4..f7  198->f8 199->f9 18c->f8 18d->f9 191->f9 19f->f6
241->138 242->139 244->13b  3e0..3e7->3c8..3cf
453->257 (golpe del agarre) 653->357  500..517->2e0..2f7  700..70f->3e0..3ef  800->480 801->481
```

Los votos completos, incluidos los ataques de cada personaje, están en `code_votes.json`.

**Códigos que dispara el motor de B3 y que SB no aporta.** Se injertan del donante, como en `b1port`:

```
3b ea ec-ed fa-ff 13a 13c 1ec-1ed 233 23e 256 259 280-293 2a0-2b1 2c0-2d9 333 33e 356 359
3d0-3d7 433-437 46e-471 482-48d 490-4bb 4c0-4c1
```

Esta lista se calcula a partir de `b1port.ENGINE` menos los códigos que cubre la tabla. Incluye el modo híper (0x259), el Dragon Rush (familia 0x280), los lanzamientos y los agarres. Los códigos SB 0x1C0–0x1E7 se parecen a 0x280/0x2A0/0x2C8, pero el acuerdo es bajo (13–20 votos de 65–100), así que también se injertan.

### 3.6 Almacén global de animaciones (almacén 0): **los mismos datos con otro índice**

- `globalmap2.py` compara `BCCMN.AMB` hijo 2 de SB, descomprimido, con `data_cmn` 165 hijo 0 de B3 (359 animaciones; es el paquete común `[AMM, AMM, AMC, AML, BSK(2172), SPX]`).
- **206 de 265 animaciones son idénticas por pose (0,0°)**, pero en otro índice. Ejemplos: `2->4, 6->14, 7->15, 8->16, 25->35, 26->36, 196->201, 197->202` (las dos últimas son la animación del agarre).
- La tabla completa está en `global_map_sb2.json`; SB1 da el mismo resultado (`global_map_sb1.json`).
- Hay 59 animaciones de SB sin pareja (por ejemplo 222, 241, 243). La propuesta es copiarlas al AMM propio del personaje, como almacén 3, para no perderlas.
- Hoy el port de GHF usa los índices de SB tal cual. En el juego, el 6 de SB pide la animación 6 de B3, que es otra.

### 3.7 AMM propio, AMM2 y AMM3

- **AMM propio.** Casado por pose (`posematch.py`, con giros de los huesos del cuerpo en t = 0, 0,5 y 1), entre el **74 y el 90 %** de las animaciones de SB son exactamente las de B3 del mismo personaje (`animmatch.log`).
  - Las animaciones de SB usan el esqueleto del modelo de SB, por ejemplo XGHF_* en GHF. `psp_amo.py` mantiene esos nombres, así que no hace falta reorientar nada.
  - Las del donante sí hay que reorientarlas, con `b1port.retarget` y `altura.py`.
- **AMM2** (animaciones de la víctima, tabla dispersa de 3 712 entradas): SB tiene 1 322 entradas no nulas y B3 49, en índices distintos. **Se usa el del donante**, que trae los agarres.
- **AMM3** (257 entradas): B3 solo usa la 256; SB usa la 129 y siguientes. Se usa el del donante.

### 3.8 BCM (combos y entradas): el mismo bloque de 64 B, pero con otras banderas

`bcmstats.py` da las distribuciones y `bcmpairs.py` casa los campos por animación. En la PS2, `w4` es la condición y `w5` el tipo; en HD van al revés (ver `capsulas.py`).

| Campo | SB | B3 | Regla de conversión |
|---|---|---|---|
| w0 dirección | 0, 1, 2, **0x10 (↑), 0x20 (↓)** | 0, 1, 2 | ↑/↓ no existen en las entradas de B3. Definitivos ↑+E → P+K+G+E en modo híper (como `adapt_iw_bcm`); ↓+E con w4 0x20 → transformación P+K+G. Los ataques normales con ↑ casaron con `w1=3` de B3 (5 votos): **validar**. |
| w1 botones | 1, 2, 5, 8 | 1, 2, 3, 5, 6, 7, 8, 0xF | La transformación pasa a w1=7 y el híper a 0xF (del donante) |
| w3 | **0x7530** en 104 entradas | siempre 0 | Poner 0 |
| w4 condición | 1 (cuesta ki), 2 (especial con cápsula), **4, 8, 0x10, 0x20, 0x40, 0x80** | 1, 2, 4, 0x400, 0x2002, 0x12… | SB 4 → especial B3 (2). SB 8 → definitivo. SB 0x20 → transformación (4). SB 0x80 + w6 0x100 → definitivo en híper (B3 `w1=f w4=1a w6=8001`). |
| w5 | 2 en 88 entradas (variante "alternativa") | 0 | Poner 0 |
| w6 | 1 suelo, 0x40 aire, **0x100, 0x101, 0x8000, 0x8101** | 1, 0x40, 0x8001, 0x4003 | Quitar 0x100. Las entradas duplicadas con w6 0x8000 (+ w3 0x7530) son la "variante tras combo": se pasan a la pareja B3 `w4 0x2002 / w6 0x4003`, o se descartan. |
| w9 ki | Ráfagas 0x12c–0x177 (**igual que B3**); especiales 1000; definitivos 5000; transformación 4000 | Ráfagas iguales; especiales 0 | Ráfagas: copiar. Especiales y definitivos: 0, y pasar el coste en barras ((w9+500)//1000) a la cápsula, como hace `capsulas.KI` |
| w12–w15 códigos | 0x4xx / 0x6xx | 0x2xx / 0x3xx | Remapear: tabla de motor + reubicación |
| cabecera (0x50 B) | 19 de 24 iguales a la de B3; 3 (GHF incluido) llevan un bloque copiado | 36 de 38 iguales | Usar la cabecera estándar de B3 |

Ejemplo de entrada de especial en GHF y su pareja en B3:

```
SB2 GHF: 0001 0008 0000 0000 0002 0000 0101 0000 000c 03e8 0000 0000 0460 0660 0660 0000   (→+E, cápsula 12, ki 1000)
SB2 GHF: 0001 0008 0000 7530 0002 0002 8000 0000 000c 03e8 0000 0000 0461 0661 0661 0000   (variante)
B3 GohL: 0001 0008 0000 0000 2002 0000 0001 0000 001a 0000 0000 0000 024b 034b 034b 0000
B3 GohL: 0001 0008 0000 0000 0002 0000 4003 0000 001a 0000 0000 0000 026c 036c 036c 0000
```

SB no tiene modo híper; su equivalente es el estado con w6 0x100. Hay que injertar del donante la entrada híper (P+K+G+E, 0x400) y el agarre (P+G), igual que en `b1port.convert_bcm`. El agarre de SB, `w1=5 → 0x453`, va a la 0x257 de B3.

### 3.9 SPX: **la misma máquina virtual, con las funciones nativas renumeradas**

La ranura 20 (el agarre) es el mismo programa en los dos juegos. Solo cambian la BASE y la dirección de la rutina común:

```
SB2 GHF/KLL: 08 20 00 08  01 30 70 05 00 00  02 73 02  12 10 04  0b 76    push16 0x800; call 0x570; pop 4; ret
B3 GohanL : 08 20 80 04  01 30 20 25 00 00  02 73 02  12 10 04  0b 76    push16 0x480; call 0x2520; ...
```

**Las nativas** (`01 10 id 02 80 02 12 10 nn`) están renumeradas:
- `spxbuiltins.py` → `spx_builtins.txt`: de 69 IDs comunes, 56 tienen otro tamaño de argumentos.
- Al alinear la rutina de agarre salen las parejas SB→B3 `8→8, 64→64, 17→33, 18→34, 22→38, 26→42`. En ese tramo B3 suma 16, pero no es un desplazamiento único.
- La alineación global por tamaño de argumentos (`spxalign.py`, `spxmap.py`) no basta. Haría falta alinear grafos de llamadas, que son la librería común que todo SPX lleva delante de la 1.ª ranura (SB 0x7B4 B, B3 0x2784 B).

**Ranuras** (`spxslots.py`):
- SB2 GHF usa las ranuras 0, 1, 20, 30, 40, 50 y 100. B3 usa 0 (Dragon Rush en híper) y 20 (agarre).
- SB llama a sus ranuras desde líneas AP tipo 7 de **clase 10**. En GHF: ranura 30 en `0x528/0x728`, ranura 40 en `0x529-52a/0x729-72a` y ranura 50 en `0x52b/0x72b`.
- En B3 la clase 10 existe pero casi no se usa.
- Hay golpes HR tipo 3 de SB que llaman a guion: 18G y CEL en `0x453` (agarre, ranura 10/100), y PIC y TRX en `0x18c-19f`.

→ **Decisión: usar el SPX del donante.** Se reubican los códigos que empuja (`b1port.spx_code_refs`) y se quitan las líneas de clase 10 de SB y los golpes de tipo 3 que apunten a ranuras de SB, convirtiéndolos en tipo 2 como en `b1port.bsk_fix_b1_hits`. Más adelante, opcional: traductor de nativas SB→B3.

### 3.10 Cámara (AMC)

- El AMC de cada personaje en SB es un stub con 0 animaciones (32 B). En B3 lleva unas 26 cámaras (14–127 KB).
- Las cámaras de los definitivos de SB salen de otro sitio: el SPX o lo común.
- Las líneas de clase 5, que contienen valores de cámara o de ralentización, **coinciden al 100 %** (por ejemplo, `0x4b0/0x44e` en la BASE de agarre de los dos juegos).
- → **Usar el AMC del donante.** Los definitivos de SB quedarían sin cámara cinemática propia: validar.

### 3.11 Efectos, sonidos y voces (AP tipo 7)

Formato `[fotograma][0x02 idx][clase u32][valor u32]` (+4 B de cola en SB). Resultado de casar líneas por fotograma y clase en golpes casados (`t7pairs.py` → `t7_maps.json`):

| Clase | Qué es | Iguales | Acción |
|---|---|---|---|
| 0 | Efecto (índice del BSP; los < 0x64 son comunes) | **97 %** | Copiar. Los ≥ 0x64 apuntan al BSP propio: quitarlos (`--quitar-efecto`) o convertir el BSP. |
| 1 | Sonido | 0 % | Tabla por mayoría (por ejemplo `3d→51` 507/507, `f→17` 398/414, `10→18`) |
| 2 | Chispa o impacto | 0 % | Tabla por mayoría (`7f7→32`, `be0→2b`, `39→35`) |
| 3 | Ranura de grito del banco de idioma | 5 % | Remapeo por rangos (SB 0x0b–0x12 → B3 0x13–0x1a, que son variantes aleatorias; `1a→27`, `1b→28`) |
| 4 | — | 76 % | Copiar más tabla |
| 5, 6, 8, 9 | — | 99–100 % | Copiar |
| 0xA (10) | Llamada a ranura SPX | — | Quitar (SPX del donante) |
| 0xB… | Exclusivas de SB | — | Quitar |

**BSP propio:** el `#AME` de SB es de otra versión (`00000200`, cabecera 0x40; B3 `02000000`, cabecera 0x10). De momento, BSP del donante; convertirlo es un trabajo aparte.

**Voces:** `BC<XXX>SND.amb` es PPHD + PS-ADPCM, un formato fácil que ya se decodifica en B1 (`gritos.scei_bank`) y entra por la pasarela RXADPC. Las frases ZP son ATRAC3plus. En el equipo ya hay un ffmpeg que las decodifica (`AppData/Roaming/easy-whisper-electron/.../ffmpeg.exe`; `-decoders` muestra `atrac3plus`). No hace falta instalar nada.

---

## 4. Qué le pasa probablemente hoy a `port_gohan_futuro` (validar en el juego)

1. **Golpes.** Las líneas AP se leen cada 16 B sobre datos de 20 B. Las ventanas de golpe, los HR, los efectos, los sonidos, la velocidad y el giro salen desplazados. Daño y reacción aleatorios o nulos; puede haber golpes que no conectan.
2. **HR.** El bloque h se lee en `128·h` cuando en realidad está en `160·h`, con tipos de aturdimiento basura (los `0xcccd`, `0x999a` que salen al leer 16 B).
3. **Almacén global con otro índice.** La transformación (0x500), el agarre (196/197) y la pose 0x2 piden otras animaciones.
4. **El motor dispara códigos de B3 que no están en el moveset.** Faltan el agarre (BASE 0x480), el híper (0x259) y el Dragon Rush (0x280…). En su sitio están los ataques de SB en 0x480–0x4BB.
5. **BCM.** La entrada ↑+E (definitivo) y la ↓+E (transformación) usan direcciones que B3 no tiene en entradas. Las entradas duplicadas con w6 0x8000 / w3 0x7530 tienen un efecto desconocido. Las especiales cuestan ki por el BCM y además por la cápsula.
6. **SPX de SB.** Si alguna vez se ejecutan sus ranuras, llamarían a nativas equivocadas. Hoy probablemente nunca se llaman, porque la clase 10 se lee desalineada.

---

## 5. Diseño de `sbport.py` (genérico SB1/SB2 → B3 PS2 → `ps2hd`)

Se reutiliza lo que ya hay: `b1port` (AMM, BSK, BCM, injertos, retarget, SPX), `sb_amm`, `psp_amo`, `ps2hd`, `capsulas` (adaptación, híper primero), `gritos`, `altura` y `roster_build`.

```
sbport.py --juego sb2 --personaje GHF --donante-anm 234 --donante-cam 231 [--forma-m 75]
          --modelos traje1..4.amb --salida DIR [--quitar-efecto 64..]
```

1. **Lectura.** `sbafs.Afs` lee `BC<XXX>.amb` (y `M<n>`) desde la ISO; `sb_amm.convert` descomprime los AMM.
2. **Normalizar el BSK** (nuevo, unas 150 líneas):
   - AP de 20 → 16 B: copiar `[0:16]`. Solo en las de tipo 1 se reordena la caja de golpe (radio a +12, s16 → i8 en +13..+15).
   - HR de 160 → 128 B (truncar cada línea). Daño × 0,85.
   - Quitar el bit 0x80 en +0x10 del sub-bloque.
3. **Remapear códigos.**
   - **Motor:** `engine_map.json`, más las familias 0x500/0x700/0x800 por desplazamiento.
   - **Ataques del BCM:** reubicar 0x4xx/0x6xx en huecos libres de 0x2xx/0x3xx, que no estén en `ENGINE`, manteniendo la pareja suelo/aire (+0x100).
   - El mismo mapa se aplica en el BCM (w12–15), en los enlaces del sub-bloque (+0x1C..+0x22) y en el SPX del donante (`spx_code_refs`).
4. **Almacén 0.** Usar `global_map_sb*.json`. Las animaciones sin pareja se copian al AMM propio (almacén 3).
5. **Injertos del donante** (`b1port.bsk_graft`). Se injerta todo lo que lista §3.5: híper, Dragon Rush, agarre y lanzamientos (BASE del donante).
   - De serie, el agarre entero del donante, por la víctima en AMM2.
   - Opcional: la animación de agarre de SB (0x800…) con la víctima del donante, si cuadran los fotogramas.
6. **Efectos.**
   - Clases 1, 2, 3 y 4 por `t7_maps.json`.
   - Quitar las clases 10 y 11+.
   - Quitar las de clase 0 ≥ 0x64 (o mantenerlas si se convierte el BSP).
   - Golpes HR tipo 3 a ranuras de SB → tipo 2.
7. **BCM.** Aplicar las reglas de §3.8 y luego las de `capsulas` (cápsulas propias, KI en barras, `hyper_first`).
8. **Formas.**
   - La familia 0x500 (↓+E) de SB es la transformación. En B3 sería P+K+G → 0x2E0 con la forma 2.
   - La forma 2 usa el mismo moveset más la sobrescritura del `M<n>` (por ejemplo, 0x19F → 0x0F6).
   - Modelos `B0n` con `psp_amo`.
9. **Cámara y SPX:** del donante. **AMM2 y AMM3:** del donante.
10. **Comprobación:** un `deep.py`/`verify_final.py` para SB:
    - la tabla de códigos cubre todo `ENGINE`;
    - no quedan líneas de 20 B;
    - los índices de almacén son válidos;
    - el SPX del donante solo cambia en los bytes reubicados.

---

## 6. Plan paso a paso y esfuerzo

| # | Paso | Esfuerzo | Validación |
|---|---|---|---|
| 1 | `sbport.py` paso 2: normalizar el BSK (20 → 16, HR, banderas) y comprobar contra el corpus con un round-trip de campos | 0,5–1 d | Sin juego: las distribuciones de 3.2/3.3 deben ser iguales a las de B3 |
| 2 | Remapeo de códigos y almacén 0 (tablas ya calculadas) | 1 d | Sin juego: cada código del BCM existe en el BSK y cada código de motor está cubierto |
| 3 | Injertos del donante y BCM | 1–1,5 d | **Juego:** combos, golpes, daño, agarre, híper, Dragon Rush |
| 4 | Efectos y sonidos por tabla; gritos (PPHD → pasarela) | 1 d | **Juego:** sonidos y voces correctos al golpear |
| 5 | Transformación SSJ de GHF (forma 2, modelos B01/B03, `M1`) | 1 d | **Juego:** transformarse y volver |
| 6 | Generalizar y probar 2–3 personajes más (Janemba SB, Gogeta SSJ, Pikkon) | 2–3 d | **Juego** |
| 7 | (Opcional) BSP propio: conversor `#AME` de SB | 2–4 d | **Juego:** técnicas con sus efectos |
| 8 | (Opcional) Traductor de nativas SPX SB → B3 para recuperar los guiones de SB | 3+ d, incierto | **Juego** |

Total del núcleo (pasos 1–5): unos 5–7 días. Con generalización: unos 8–10.

---

## 7. Riesgos

- **Entradas ↑/↓ del BCM.** No se sabe si el lector de entradas de B3 acepta w0 0x10/0x20, porque ningún personaje B3 las usa. Se convierten a botones de B3, aunque el mapeo de los ataques normales con ↑ tiene poca evidencia.
- **Variantes con w6 0x8000 / w3 0x7530.** La semántica es probable pero no está confirmada ("tras combo" o "aura").
- **Escala de daño.** Varía por personaje (0,71–1,0). La vida máxima de SB no se ha comparado.
- **Definitivos sin cámara ni guion propio.** Lo mismo pasó con B1. Se verán como golpes con su animación, pero sin la cinemática de SB.
- **Agarre.** Mezclar la animación de SB con la víctima del donante puede desincronizarse; de serie va entero del donante.
- **Pose del select.** La de GHF cerraba el juego con `pose_select=false`. Sigue abierto; puede que se arregle al normalizar.
- **Retarget de animaciones del donante** sobre esqueletos de SB (XGHF de 44 huesos): altura de cadera; ver la memoria [[b3hd-port-height]].
- **`#RPT` (física del cinturón):** B3 no lo tiene; la tira de cinturón seguirá estática.

## 8. Qué validar en el juego (cuando el usuario pueda)

1. El port actual sin cambios (como referencia): ¿los golpes de GHF conectan, quitan vida normal y tienen sus efectos?
2. Tras el paso 3: los combos P/K, las ráfagas de ki, las 4 especiales y el definitivo, el agarre (P+G), el modo híper con su Dragon Rush, y el daño frente a Gohan adulto.
3. Los sonidos de impacto y los gritos.
4. La transformación SSJ.
5. La pose del select con la animación propia.

## 9. Preguntas abiertas

- ¿Qué traje o forma va con `BCGHFM1.amb`? No está localizada la tabla de personajes del ELF de SB2; las tablas candidatas están en `0x1a3ef8` y `0x1b9d54` de `sb2_boot.elf`.
- ¿Qué hacen `AC_<XXX>.spx` (24 ranuras, unos 7 KB) y `EV_AC<XXX>*.spx`? Probablemente sean eventos o cámaras de los definitivos de SB.
- Semántica exacta de w4 0x10/0x40 y w6 0x100 en SB (¿estado "aura"?).
- ¿Merece la pena el traductor de nativas SPX? Recuperaría los guiones de SB, incluidos los definitivos cinemáticos.
- Super Dragon Ball Heroes World Mission incluye `BCGHF.bsk`, `BCGHFM1.bsk` y `BCGHFM3.bsk` (misma familia `#BSK` v4). Podría servir de oráculo adicional (no analizado).

---

## Anexo: scripts y datos (en esta carpeta)

Ninguno escribe en el proyecto.

| Fichero | Uso |
|---|---|
| `sbafs.py` | Lector de los AFS de PSP (con nombres) dentro de la ISO. `python sbafs.py sb2 data_btl_cmn.afs [dump i out]` |
| `ambtree.py` | Árbol de un `#AMB` LE |
| `src.py` | Carga los movesets de SB (`sb_char`) y de B3 GH (`b3_char`, data_cmn + `roster_db.json`) |
| `corpus.py` | Caché de todos los movesets (AMM de SB ya descomprimidos) en `D:\DBZ3HD\explore\01_moveset\corpus2.pkl`. `corpus.pkl` en esa misma carpeta es una caché antigua sin descomprimir, ya sin uso. |
| `oracle_ghf.py` | Prueba de que `ghf_365/367` son el reempaquetado byte a byte de `BCGHF.amb` |
| `posematch.py`, `animmatch.py` (+ `animmatch.log`, `code_votes.json`) | Casado de animaciones por pose y votos de códigos SB → B3 |
| `globalmap2.py` (+ `global_map_sb1/2.json`) | Almacén global SB → B3 |
| `enginemap.py` (+ `engine_map.json`) | Tabla estable de códigos de motor |
| `apstats.py`, `apdump.py`, `t1hit.py`, `subblk.py`, `hrcols.py` | Formato de las líneas AP, HR y sub-bloques (20 / 16 B) |
| `pairhits.py`, `dmgscale.py` | Golpes casados y escala de daño |
| `bcmstats.py`, `bcmpairs.py` | Campos del BCM SB frente a B3 |
| `spxslots.py`, `spxbuiltins.py` (+ `spx_builtins.txt`), `spxalign.py`, `spxmap.py` | Ranuras SPX y renumeración de nativas |
| `t7pairs.py` (+ `t7_maps.json`) | Tablas de efectos, sonidos y gritos SB → B3 |
| `*.amb`, `*.spx`, `b3_bsp_*.bin`, `sb2_boot.elf` | Copias de trabajo extraídas para inspección (12 MB) |
