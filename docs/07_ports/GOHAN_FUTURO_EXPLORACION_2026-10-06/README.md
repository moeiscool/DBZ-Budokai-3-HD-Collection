# Gohan del Futuro al 100 %: exploración (2026-10-06)

Hecho por 5 agentes en paralelo. Ninguno abrió el juego ni tocó el proyecto. Cada
carpeta tiene su `informe.md` completo, los scripts y las imágenes de evidencia.
Las extracciones grandes (ISO, ELF, caches) están en `D:\DBZ3HD\explore\` y la copia
íntegra de las 5 carpetas en `D:\DBZ3HD\explore\informes_2026-10-06\`.

## Estado real del port actual (`mods/port_gohan_futuro`)

- **Modelos** (`traje1-4.bin`): salen de nuestro `awo_tools/psp_amo.py` aplicado a
  `BCGHFB00-03.amb` (Another Road, `data_btl_cmn.afs` 71-74).
  - B00 = Normal, B01 = SSJ, B02 = SSJ2 (pelo algo distinto), B03 = Potencial
    liberado (lleva la Espada Z).
  - Hoy están como 4 **trajes**: siempre pelea en forma normal (`formas = 1`).
- **Moveset y cámara**: el "port comunitario" `ghf_365/367` es una copia byte a byte de
  `BCGHF.amb` de Shin Budokai 2, sin convertir.
  - SB usa líneas AP de 20 B y bloques HR de 160 B; B3 los lee de 16 B y 128 B. Por
    eso golpes, daño, efectos y voces se leen desalineados desde la 2.ª línea.
  - No tiene modo hiper (sin definitivo) y su `#ACC` (cámaras) está vacío.
  - En SB, cond 0x0004 es un especial; en B3 es "transformar".
- **Técnicas**: `tecnicas.bin` es el BSP de SB2 pasado por `ps2hd` (está comentado
  con razón). `#AME` es otro sistema de partículas, `#ASE` tiene bloques de 0xB0
  (B3: 0xD0) y usa los AST 0x15E/0x15F, que B3 reserva para las ráfagas de ki.
- **Sombreado**: todas sus texturas tienen alfa 255, que en el shader significa
  "sin sombrear". Sale plano, solo con el brillo HD de borde, y sus normales malas
  hacen manchas.
- **Tira del cinturón**: las colas del cinturón y el pelo de B3 se mueven con física
  por cadenas (tabla del XEX por modelo). `roster_ext.cpp` pone a 0 la física de los
  modelos nuevos y su pose de reposo deja las colas horizontales.

## Hechos nuevos que corrigen notas anteriores

- **Shader toon**: el PS `5F27AACEB38B1088` **resta** la rampa (`color = base − rampa`)
  y el alfa alto de la base significa "sin sombrear". "base × (1 − rampa)" solo es
  exacto con bases blancas.
- **Definitivos**: son P+K+G+E en modo hiper → HR tipo 3 → SPX ranura 0, con sus
  animaciones en 0x4A0+. La ranura 20 del SPX es el agarre (en los 38 personajes).
  Contradice parte de la nota de `b1port` (0x4A0 = lanzamientos): hay que
  confirmarlo en el juego antes de reescribir esa nota.
- **Cápsulas `#SKC`**: +15 = ki en décimas de barra (encaja en 169 de 191); +14 =
  formas.
- **Transformarse no gasta ki**: exige tener N barras (1 barra = 1000; máx. 7).
  P+K+G salta a la forma más alta posible; con menos de 1 barra, un golpe te devuelve
  a la forma normal.
- **Beam struggle**: bit 0x2000 del BCM + línea `c0=0x68`; la respuesta va con
  cond2 0x4000 y `c0=0x69` (35 de 38 personajes). Base para el interruptor que pidió
  Discord.
- **SB → B3**: daño B3 = 0,85 × SB (mediana de 8 847 golpes).
  - Códigos de ataque: 0x4xx/0x6xx → 0x2xx/0x3xx, transformación 0x500 → 0x2E0,
    agarre 0x800 → 0x480.
  - Almacén común de animaciones: 206 de 265 casan (tablas en
    `01_moveset/engine_map.json`, `global_map_sb*.json`, `t7_maps.json`).

## Decisiones tomadas (se pueden cambiar)

| Tema | Decisión | Motivo |
|---|---|---|
| Formas | 4 (Normal, SSJ, SSJ2, Potencial liberado), cada una con su modelo de Another Road | El juego original las tiene; el usuario las pidió |
| Ki | SSJ ≥4 barras, SSJ2 ≥5 (exige SSJ), Potencial ≥6 (exige SSJ2); nivel base 4/4/5 | Las mismas reglas que Gohan adulto en B3 |
| Nombre de la 3.ª cápsula | "Potential Unleashed" | En su futuro no hay Kaioshin anciano |
| Definitivo | Rayo gigante = Super Kamehameha, con la cinemática de Gohan adulto | En SB2 es gemelo exacto del de Gohan adulto |
| Onda magenta | Especial potente | Una segunda cinemática no compensa |
| Beam struggle | Sí, en el Kamehameha | Como Gohan adulto |
| Nombres de técnicas | Descifrarlos de las texturas del menú de SB2 | Son oficiales |
| Studio | Ventana propia lanzada desde el Mod Kit; Blender opcional vía glTF | Blender 5.2.1 ya está instalado; glTF no exige add-on |

## Plan por fases

1. **`sbport.py`** (conversor genérico de movesets de Shin Budokai 1/2):
   - AP 20 → 16 B y HR 160 → 128 B; daño × 0,85;
   - remapeo de códigos y del almacén común;
   - injertar del donante el modo hiper, el Dragon Rush, el agarre y los lanzamientos.

   Se valida fuera del juego con la pareja Gohan adulto SB2/B3, que comparte golpes.
2. **Formas**:
   - `formas = 4`;
   - clave `ki` por cápsula en `roster_build`;
   - P+K+G e injerto de 0x2E0/0x3E0 del donante con `csk_graft`;
   - `modelo_forma` en `roster_ext.cpp` para el SSJ2 propio.
3. **Pulir el modelo**:
   - física del cinturón: copiar la del donante o colgar las colas en reposo;
   - alfa 0 + rampa por material, para tener sombra toon;
   - normales suaves;
   - texturas IA ×2 con chaiNNer (ya instalado, modelo AnimeSharp), sin pasar de
     ~800 KB por traje.
4. **Técnicas**:
   - BSP híbrido: el del donante + AST/ASE de SB renumerados + texturas;
   - partículas recoloreadas;
   - hiper + definitivo cinemático;
   - beam struggle;
   - cápsulas con ki y formas.
5. **Studio, primera versión**: editor de cámaras de técnicas, con línea de tiempo,
   plantillas (órbita, travelling, temblor), vista previa toon e ida y vuelta a
   Blender. Antes hace falta una sesión de capturas en el juego (orientación y espejo
   de la cámara, relación espera/clip).
6. **Generalizar `sbport.py`** a Gogeta SSJ, Vegetto, Gotenks, Pikkon, etc.
7. **Opcional**: modelo nuevo desde Super Dragon Ball Heroes World Mission
   (`model/bcghf`). Tiene 3 449 triángulos, boca, 7 caras, rampas propias y el
   esqueleto de B3, pero no trae el SSJ2. Ver `03_modelo/sdbh_vs_psp.png`.

## Qué hay que probar en el juego (por fase)

- **Fases 1-2:**
  - los golpes conectan y quitan la vida normal;
  - con 3 barras no se transforma; con 4 pasa a SSJ; con 5 desde normal salta a
    SSJ2; con 6 a Potencial;
  - un golpe con menos de 1 barra lo devuelve a normal;
  - la ficha de pausa dice 4/5/6;
  - la CPU se transforma.
- **Fase 3:**
  - el cinturón en reposo, andando y en agarres;
  - la sombra toon, y que el modelo no salga negro;
  - el contorno;
  - el brillo HD a 0 y a 1;
  - Gohan del Futuro contra sí mismo con texturas ×2 (memoria).
- **Fase 4:**
  - especiales S1-S6, el modo hiper y el definitivo;
  - el beam struggle;
  - que la ráfaga de ki siga normal;
  - Edit Skills.
