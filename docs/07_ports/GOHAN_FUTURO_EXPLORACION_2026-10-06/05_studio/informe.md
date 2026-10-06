# Studio de animación y cinemáticas: viabilidad y diseño

Fecha: 2026-10-06. Solo exploración y diseño: no se ha tocado ningún archivo del proyecto ni se ha abierto el juego.
Todo lo producido está en esta carpeta (`scratchpad/explore/05_studio/`).

## 0. Veredicto

**Es viable, y la parte de cámara está más cerca de lo que parecía.**

- **Cámaras de técnicas.** El formato #ACC/#AMC está descifrado por completo:
  - 4 pistas por clip: ojo, objetivo, roll y fov.
  - Los 633 clips de los 38 personajes de B3 cumplen el formato.
  - El prototipo decodifica y vuelve a codificar todos los clips de un personaje byte a byte.
  - Ida y vuelta por Blender 5.2 (ya instalado): error ≤ 0,00002 unidades, roll y fov animados incluidos.
- **Animaciones.** El formato #ACM está descifrado:
  - Euler u16 por hueso y posiciones como desplazamiento, ya validado en juego por `b1port`/`altura`.
  - Ida y vuelta por Blender: error ≤ 0,004° tras volver a Euler u16.
- **Guion de la cinemática (#SPX).** Se entiende su estructura, pero editarlo libremente aún no es seguro.
  - Es una VM de pila.
  - Se identifica el builtin **0xA7 = "reproducir clip de cámara"** y el patrón "clip → esperar N frames".
  - Sin el intérprete completo, solo se pueden cambiar valores **en su sitio** (índice de clip, frames de espera, floats).
  - Añadir o quitar órdenes es una fase posterior.
- **Recarga en el juego sin reiniciar.** Funciona por diseño del runtime:
  - El override de una entrada se lee del disco en cada carga.
  - Basta reescribir el archivo y "Reelegir personajes".
  - Hay una condición: el tamaño no puede crecer durante la sesión (ver §4.3).

**Recomendación:** un núcleo propio en Python con un **puente glTF** (Blender o cualquier programa 3D, sin add-on obligatorio), más una ventana **Studio** en tkinter dentro del Mod Kit.

- **MVP:** un editor de cámara de técnicas con línea de tiempo, vista previa toon y prueba en el juego.
- **Fases siguientes:** retiming y edición de poses vía Blender, y la pista de eventos SPX.

---

## 1. Cómo están codificados los datos

### 1.1 Dónde vive cada cosa (por personaje, `roster_db.json`)

| Bin (data_cmn) | Contenido HD (PS2) | Uso |
|---|---|---|
| `anm[forma]` (Goku 292) | `#AMB[#CSK, #ACM, #ACM, #ACM]` (BSK, AMM×3) | propiedades de ataque + 3 bancos de animación |
| `cam` (Goku 288) | `#AMB[#ACC(tipo 5), #ACL(6), #CCM(BCM), #SPX(8)]` | **cámaras**, stub, tabla de combos, **guiones** |
| `bsp` (Goku 533) | efectos de técnicas | rayos, auras de técnica (fuera del alcance del MVP) |

- PS2 GH y HD tienen la misma numeración y el mismo contenido. HD = big-endian con los magics renombrados (`ps2hd.MAGIC`).
- El #ACC pasa de la PS2 a la HD con un simple giro de palabras de 32 bits (`ps2hd.conv_u32`).
- El #SPX se copia tal cual: es **little-endian también en la HD**.
- Bancos de animación de Goku (HD 292):
  - #ACM 1: 142 animaciones, 53 huesos, hasta 190 frames.
  - #ACM 2: animaciones de la víctima en agarres, esqueleto genérico GOK_.
  - #ACM 3: 71 animaciones.

### 1.2 Animación #ACM (= AMM PS2)

```
+0x10 n_anim  +0x14 tabla(0x20)  +0x18 n_huesos  +0x1C tabla de nombres (32 B/hueso)
tabla: n_anim × [flags, variante, n_frames, off]      flags 9 normal, 0x19 con escala
bloque (off): n_huesos × per punteros  (per 2 = giro+pos, 3 = +escala)
pista: [u32 0][u32 tipo][u32 n_claves] + claves
   giro : [u16 frame][u16 x][u16 y][u16 z]      65536 = 360°
   pos  : [u32 frame][f32 x][f32 y][f32 z]      desplazamiento SOBRE la posición de reposo
```

Reglas de pose validadas en el juego (`altura.py`, `b1port.py`):
- **Giro.** `q = qz·qy·qx` (Euler u16) y **sustituye** al giro de reposo del hueso.
- **Posición.** Se **suma** a la de reposo.
- **Emparejamiento.** El motor casa las pistas **por nombre de hueso** (sufijo), así que una animación sirve a cualquier esqueleto con los mismos sufijos.
- **Interpolación.** Lineal por componente, con la vuelta más corta. `b1port.reduce_track` quita las claves que la interpolación reproduce y los ports de Zarbon y Dodoria se ven bien en el juego.
- **Tipo de pista.** El campo `tipo` vale 1 en 5387 pistas y 0 en 185. Las de tipo 0 tienen una clave por frame (probablemente "sin interpolar", sin efecto práctico).
- **Unidad de tiempo.** Frame del juego, **60 fps**: es la convención del motor; queda confirmarlo midiendo un clip en el juego.
- **Root motion.**
  - No existe como tal: la cadera (WAIST) se mueve en el marco local del personaje.
  - El desplazamiento en el mundo parece venir de las líneas AP del #CSK (tipo 4 = velocidad, tipo 2 = aéreo) y del motor. Es una inferencia por verificar.

### 1.3 Cámara #ACC (= AMC PS2): formato completo

```
misma cabecera que el AMM: +0x10 n_clips, +0x14 tabla, +0x18 n_huesos = 1, +0x1C 0
tabla: n_clips × [0x1D, 0, n_frames, off]
bloque del clip: 4 punteros → pistas  ojo | objetivo | roll | fov
  ojo, objetivo : [u32 frame][f32 x][f32 y][f32 z]   (vec3)
  roll, fov     : [u32 frame][f32 valor]             (escalar, radianes)
la última clave siempre está en n_frames-1 (633/633)
```

**Evidencia de la semántica** (`cam_stats.py`: 38 CAM bins, 633 clips, 2532 pistas):
- **fov.** Va de 0,066 a 1,306 rad (3,8° a 74,8°) y la mediana es 37,8°.
- **roll.** Está entre −π y π, con mediana 0.
- **Objetivo, no giro.** La guía de la comunidad (`AMC_Guide.zip`, SamuelDBZMA&M) llama a la 2.ª pista "rotación", pero es un **punto de mira**:
  - La distancia ojo-objetivo va de 3,5 a 1058 (mediana 32,7).
  - El objetivo de Goku en el clip 0 es (0; 10,5; 0), la altura del pecho.
  - El render con esa interpretación encuadra al personaje (`render/goku_clip0_f*.png` en Blender y `render/tira_goku_clip0.png` con el render toon del kit).
- **Densidad de claves.** Lo normal es 1 clave por frame (mediana 0,77 claves/frame). Algunos clips son dispersos: Zarbon (HD) usa 46 claves para 80 frames y mantiene la última. Por eso se asume interpolación lineal.
- **Clips por personaje.** Van de 2 a 69 (Goku 36).
- **Gohan del Futuro:** su #ACC está **vacío** (0 clips). Sus cinemáticas no tienen cámara propia, así que es un caso de uso directo del Studio.

**Por verificar en el juego (hito M0):**
- Espacio de referencia: parece local al atacante, con Y arriba y unidades del modelo. Falta saber hacia qué eje está el rival.
- Si hay espejo izquierda/derecha.
- Qué hacen los 3 floats extra de la llamada 0xA7: (0, 140, 0), (0, 140, −150) y (0, 200, 0) parecen un desplazamiento o giro del encuadre.

### 1.4 Cadena de una cinemática (de la entrada a la cámara)

```
mando ──► #CCM (BCM, tabla de combos) ──► código de ataque (p. ej. 0x259)
          └─► #CSK: list[código] → sub-bloques 48 B [anim u16][banco u16] + params
                 └─► líneas AP (por frame): tipo 1 golpes (HR), 2 aéreo, 4 velocidad, 7 efectos (BSP)...
                       └─► bloque HR con stun_type 3 ("con guion") + stun_code = RANURA del #SPX
                             └─► #SPX: tabla de ranuras → subrutinas (VM de pila)
                                   ├─ CAMARA_CLIP (builtin 0xA7): clip del #ACC del MISMO CAM bin
                                   ├─ esperar N frames  (push N; call sub 0)
                                   ├─ empuja códigos de ataque (anims de atacante/víctima)
                                   └─ otros builtins (efectos, sonido, posiciones...)
```

- **Ranuras de Goku.** HR tipo 3 solo en 0x259/0x359 (ranura 0, la embestida del modo hiper) y 0x257/0x357 (ranura 20, el agarre). La ranura 10 existe en 5 personajes.
- **Contradicción en la memoria del proyecto.** El docstring de `b1port` dice "ranura 20 = definitivas", pero los datos dicen agarre.
- **Pendiente para M0:** cómo arrancan las definitivas (Kamehameha...). Quizá vía SCM/cápsulas o por la ruta común de la ranura 20.
- **Censo de ranuras** (38 CAM): ranura 20 ×38, 0 ×32, 10 ×5, 1/30/31 ×2, 2/32 ×1.

### 1.5 #SPX: lo que se sabe de la VM

Opcodes seguros:
- `08 10/20/30` push inmediato de 8/16/32 bits.
- `09 30` push float.
- `01 10/20/30` carga el acumulador.
- `02 80 02` llamada a builtin.
- `02 73 02` llamada a subrutina (dirección = base 0x74 + valor).
- `12 10 n` desapila.
- `0b` fin de sentencia.

Hay más opcodes de 1 byte y de saltos (`02 72 00 02`, `76`, `0a`, `5c`...) sin tabla todavía.

**Builtin 0xA7 = reproducir clip de cámara.**
- Su 2.º argumento entero recorre 0..n_clips−1: cubre de media el 59 % de los índices de cada personaje en 30 personajes y solo 6 valores caen fuera de rango.
- El documento de stages ya sospechaba de `01 20 a7 00`.
- Ejemplo real (Goku, `spx_dis.py spx_288.bin 3440 3740`):

```
CAMARA_CLIP(0, g[0x60]+0, 0, 0.5, 0, 0, 0) ; esperar 0x2e
CAMARA_CLIP(0, g[0x60]+1, 0, 0.5, 0, 0, 0) ; esperar 0x3a ; ...  (clips +0..+7)
```

- `spx_graph.py` agrupa las llamadas por subrutina. En Goku, la ranura 0 usa los clips 0–19 y la ranura 10 los clips 0–7, con un índice relativo a una variable base.

---

## 2. Prototipos (en esta carpeta) y resultados

| Archivo | Qué prueba | Resultado |
|---|---|---|
| `anim_cam_decode.py` | decodifica y vuelve a codificar #ACC (PS2/HD) y vuelca 1 animación y 1 clip a JSON | 36 clips de Goku (PS2) y 25 de Zarbon (HD) **idénticos byte a byte**; JSON en `out_ps2/`, `out_hd/` |
| `cam_stats.py` | semántica de las pistas sobre todo el corpus | ver §1.3 |
| `spx_calls.py`, `spx_dis.py`, `spx_graph.py` | censo de builtins, desensamblado aproximado, grafo clip↔ranura | 0xA7 = cámara; patrón clip + espera |
| `to_gltf.py` | B3 HD → `.glb`: malla con piel (Goku 264), animación del moveset (292) y cámara (288) a 60 fps; fov animado con `KHR_animation_pointer` | 46 huesos, 2455 vértices, 28 canales; unos segundos (la mayoría, descomprimir LZX) |
| `blender_check.py` | Blender 5.2 headless importa el .glb y renderiza desde la cámara del clip | `render/goku_clip0_f000/045/089.png`: Goku animado y encuadrado |
| `blender_roundtrip.py` + `gltf_to_cam.py` | importar → exportar en Blender (con y sin edición) → nuevo #ACC dentro de una **copia** del CAM bin | error ojo 0,0, objetivo 1e‑5, roll 0, fov 0; la edición "+5 en X" llega exacta; el resto de clips y los hijos #ACL/#CCM/#SPX quedan intactos (HD y PS2) |
| `gltf_to_anim_check.py` | animación tras pasar por Blender → Euler u16 | 1350 muestras, error ≤ 0,0039° tras cuantizar (el 0,056° bruto es redondeo de float32 en acos) |
| `preview_strip.py` | vista previa sin Blender con el render toon del kit (`model_render.py`) | **0,066 s/frame a 320×180** (~15 fps), `render/tira_goku_clip0.png` y `.gif` |

Comandos de verificación (desde esta carpeta, con `TMP`/`TEMP` apuntando a `cache/` para que la caché de `afs_pair` no salga de aquí):
```
python anim_cam_decode.py --cam 288 --clip 0 --anm 292 --anim 0 --out out_ps2
python cam_stats.py
python to_gltf.py --modelo 264 --anm 292 --anim 0 --cam 288 --clip 24 --out goku_clip24.glb
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --factory-startup --python blender_roundtrip.py -- <abs>\goku_clip24.glb <abs>\goku_clip24_blender.glb 5
python gltf_to_cam.py goku_clip24_blender.glb --cam 288 --clip 24 --out cam288_rt.bin
python gltf_to_anim_check.py goku_clip24_blender.glb --anm 292 --anim 0
python preview_strip.py --modelo 264 --anm 292 --anim 0 --cam 288 --clip 0 --frames 0 45 89 --out render/tira.png --gif
```

Límites de los prototipos:
- **Sin texturas en el glTF**: el decodificador DXT3 ya existe en `model_render._textures`.
- **Sin escala de huesos** ni el banco de la víctima.
- **Claves horneadas** (1 por frame): falta reducir claves como `reduce_track`.
- **Animación de la vista previa en bucle** (`f % n_frames`). La del juego depende del guion.

---

## 3. Arquitecturas comparadas

| | (a) Blender vía glTF | (b) Studio propio en el Mod Kit | (c) Vista previa en el juego |
|---|---|---|---|
| **Qué es** | Exportar a .glb (modelo + anim + cámara), editar en Blender u otro programa, importar | Ventana tkinter: línea de tiempo, editor 2D de la trayectoria, vista toon con `model_render` | Escribir el override y verlo en el juego real |
| **Estado** | Probado ida y vuelta (§2); Blender 5.2.1 instalado; `KHR_animation_pointer` soportado | Render 0,066 s/frame; tkinter + Pillow + numpy (ya son requisitos del kit) | El runtime lee el override en cada carga (§4.3) |
| **Fuerte** | Herramientas de animación de verdad (curvas, IK, cámara con objetivo); la comunidad ya usa Blender (retopología) | Sin instalar nada; sabe qué clip es de qué técnica; valida y guarda el mod con seguridad | Única fuente de verdad: efectos, tiempos del guion, sombreado real |
| **Débil** | Ni efectos ni guion; el modder ve "un clip suelto"; depende de una app externa | Edición 3D limitada (vistas 2D + valores); sin efectos | Ciclo lento (~30–60 s); sin teclas de depuración hace falta jugar hasta la técnica |
| **Esfuerzo** | Bajo-medio (2–3 jornadas: núcleo + texturas + doc) | Medio (5–8 jornadas el MVP) | Bajo para el ciclo manual (1–2); alto para una recarga en caliente con tecla (RE + C++) |
| **Riesgo** | Bajo (formato abierto; no hace falta add-on, así se evitan las obligaciones GPL de `bpy`) | Bajo | Medio-alto si se toca memoria del guest |

**Add-on de Blender o puente glTF.** Mejor el puente glTF.
- Sirve igual en Blender, Maya, 3ds Max o Cascadeur.
- No se rompe con cada versión de Blender.
- No obliga a distribuir código GPL.
- Un add-on fino ("Enviar al juego" = llamar a nuestro CLI) puede venir después.

---

## 4. Recomendación: diseño por capas

### 4.1 Piezas

1. **`studio_core.py`** (en `awo_tools/`, sin interfaz):
   - Lectura y escritura de #ACC/#ACM y de las líneas AP del #CSK.
   - Validación.
   - Catálogo de clips por técnica.
   - Reducción de claves.
   - glTF de ida y vuelta.
   - Se apoya en lo que ya existe: `altura.py` (FK), `b1port.Amm` (reconstruir bancos), `ps2hd` (PS2→HD), `afs_pair`, `model_render.Model`.
2. **CLI `studio.py`**, con los mismos verbos que use la ventana: `exportar-glb`, `importar-glb`, `vista`, `validar`, `guardar`, `probar`.
3. **Ventana Studio.** Una ventana tkinter aparte, lanzada desde el Mod Kit: botón "Studio" en Herramientas y en la ficha del personaje. Así no se infla `modkit_gui.py` (ya tiene 5300 líneas).
4. **Ciclo de prueba en el juego.** Una ranura `_studio` reservada, escritura atómica, y una guía de "Reelegir personajes".

### 4.2 MVP: "Editor de cámara de técnicas"

1. **Elegir personaje y técnica.**
   - La lista sale del catálogo: ranura/subrutina del SPX → clips en orden con su espera (`spx_graph`) + un nombre (tabla curada en M0).
   - Cada clip lleva miniaturas: primer, medio y último frame renderizados.
2. **Línea de tiempo de la toma.**
   - Bloques de clip con su duración real (la espera del guion).
   - Marcas de los frames de golpe y efecto de las líneas AP del código de ataque.
3. **Editor del clip.**
   - Vistas cenital y lateral (canvas): curvas de ojo y objetivo arrastrables.
   - Esqueleto en alambre del personaje en el frame actual.
   - Campos numéricos.
   - Roll y fov como curvas.
4. **Operaciones.**
   - Mover, añadir y borrar clave; suavizar.
   - Re-temporizar (estirar o encoger sin cambiar el total del guion).
   - Copiar un clip de otro personaje.
   - Plantillas: órbita, travelling, acercamiento, temblor, giro de cámara.
5. **Vista previa.**
   - Render toon de 15 fps al arrastrar el cursor.
   - "Reproducir": hornea en segundo plano y guarda un GIF para compartir.
6. **Blender (opcional).** "Abrir en Blender" exporta un .glb (y abre Blender si está instalado); "Traer de Blender" importa la cámara.
7. **Guardar como mod** con validación y respaldo, y **"Probar en el juego"** con instrucciones (§4.3).

Fuera del MVP:
- Editar poses.
- Añadir animaciones.
- Editar el guion (salvo números en su sitio).
- Efectos BSP.

### 4.3 Integración con el Mod Kit y roster_build (salidas, validación, seguridad)

**Salidas:**
- **Personaje nativo:**
  - Ruta: `mods/studio_<personaje>_<tecnica>/us/data_cmn.afs/<fid CAM>/geom.bin`.
  - Comprimido con LZX `xbcompress /N:2048` y rellenado con ceros.
  - Lleva `manifest.txt` (`type=studio`, `source=CAM 288`) y un **proyecto editable** `studio.json` con las claves y el origen. Es la fuente de la verdad: el bin se puede regenerar.
- **Personaje nuevo o port** (Zarbon, Gohan del Futuro...):
  - El Studio edita el `moveset/camara.bin` (o el `anm*.bin`) **del mod fuente**.
  - Después lanza `roster_build.py construir`, como hoy.
  - No se escribe nunca en `_roster` a mano.
- **Animaciones (fase 2):**
  - Se reconstruye el #ACM con `b1port.Amm.build`.
  - Si cambia la duración, se desplazan los `frame` de las líneas AP del código.
  - El override va al `anm` del personaje (o al mod fuente).

**Validación antes de escribir** (falla = no se escribe nada):
- **Ida y vuelta.** Decodificar lo codificado tiene que dar lo mismo. Los demás clips o animaciones y los otros hijos del #AMB quedan idénticos byte a byte (como `gltf_to_cam.py`).
- **Claves.**
  - Frames crecientes; la última clave en `n_frames−1`.
  - Floats finitos; fov entre 0,05 y 2,5 rad; roll entre −π y π.
  - Distancia ojo-objetivo > 0,1.
- **Índices.**
  - No se borran clips: el guion los pide por número.
  - Solo se añaden clips al final.
  - Si se añade un clip, se avisa de que el guion no lo usará sin editar el SPX.
- **Animación.** Las líneas AP tienen que caer dentro de la duración.
- **Tamaño.**
  - Override ≤ tamaño reservado (ver recarga).
  - Si no cabe, el aviso dice "reinicia el juego para aplicar".
  - Nunca se trunca nada.
- **Conflictos.** Otro mod activo que sobreescriba la misma entrada (gana el primero alfabético) genera un aviso, como hace `roster_build estado`.

**Seguridad de los datos del usuario:**
- **Nunca se toca** `us/*.afs` ni los archivos originales: solo se escribe en `mods/`.
- **Respaldos.** Antes de reescribir un archivo de mod, la versión anterior se mueve a `mods/<mod>/respaldo/<fecha>/`. Nunca se borra (regla del usuario).
- **Escritura atómica.** Se escribe a un temporal y luego `os.replace`, con reintentos si el juego tiene el archivo abierto.
- El proyecto `studio.json` permite deshacer y regenerar.

**Recarga en el juego sin reiniciar** (comprobado leyendo el runtime, `afs.cpp` / `host_path_file.cpp`):
- `AfsFindModOverride` abre y lee el archivo override **en cada lectura**; solo la lista de carpetas de mods se cachea al arrancar.
- **Consecuencia 1:** la carpeta `mods/_studio` (o la del mod) tiene que existir **antes** de abrir el juego.
- **Consecuencia 2:** la tabla AFS virtual (`GetOrLoadVirtualAfs`, `g_vafs_cache`) se calcula **una vez** con el tamaño del override en ese momento. Por eso el Studio reserva tamaño al crear el override (original + margen, p. ej. +25 % o +64 KB) y siempre escribe exactamente ese tamaño, rellenando con ceros.
- **Ciclo:** guardar → en el juego Pausa → "Reelegir personajes" → mismos personajes → Entrenamiento → lanzar la técnica. Falta confirmar en M0 que la entrada se relee al recargar el combate.
- **Automatización.** Existen `dbz3_input.req` y `dbz3_shot.req` (SDK). Valen para pruebas de desarrollo (y con permiso del usuario), no para el usuario final.

### 4.4 Fases posteriores

- **F2 Animación:**
  - Re-temporizar códigos de ataque: deformar el tiempo de las pistas y desplazar los frames AP.
  - Retocar poses en Blender vía glTF: cuaternión → Euler u16 (`quat_to_u16`) y reducción de claves.
  - Añadir animaciones al banco y apuntar el sub-bloque del #CSK.
  - Importar animaciones de otros juegos o esqueletos: ya existen `b1port.retarget`, `sb_amm` y `altura.correccion`.
- **F3 Pista de eventos SPX:**
  - Desensamblador completo: tabla de opcodes y aridad de los builtins, sacada del intérprete en `generated/` o con una sonda en el runtime.
  - Primero, línea de tiempo de solo lectura.
  - Después, edición en su sitio: índice de clip, espera, floats de 0xA7.
  - Por último, insertar o borrar sentencias con recolocación de saltos y de la tabla de ranuras.
- **F4 Runtime (C++, opcional):**
  - Tecla de desarrollo "repetir la última cinemática".
  - Recarga en caliente del CAM bin en memoria del guest.
  - Cámara libre o modo foto: Burst Limit lo tiene en su rama del SDK.
  - Exige RE de dónde se carga el CAM bin y cómo se lanza una ranura del SPX. Tras cada build hay que recopiar las DLL canónicas.
- **F5 Efectos BSP en la vista previa:** RE del formato BSP. Largo; solo si hay demanda.

---

## 5. Plan, esfuerzo y riesgos

Esfuerzo en jornadas de agente, más las pruebas en el juego que haga el usuario.

| Hito | Contenido | Esfuerzo | Criterio de "hecho" |
|---|---|---|---|
| **M0 Verificación** | 1 sesión de capturas: marco y espejo de la cámara, fps, espera ↔ duración del clip, floats de 0xA7; relectura del override al reelegir personajes; catálogo técnica → clips de 2–3 personajes (Goku, Vegeta, Cell) | 2–3 | Render del Studio ≈ captura del juego (mismo encuadre); un cambio de clip visible sin reiniciar |
| **M1 Núcleo** | `studio_core.py` (lectura/escritura, validación, reducción de claves, catálogo); prueba = ida y vuelta byte a byte de los 633 clips y de todos los #ACM del corpus | 2–3 | `python studio_core.py --selftest` en verde |
| **M2 Puente glTF** | exportar/importar con texturas, banco de la víctima, rival en su sitio; botones en el Mod Kit; guía "Editar una cámara en Blender" | 2–3 | Editar en Blender → mod → visto en el juego |
| **M3 Studio MVP** | ventana tkinter de §4.2 + guardar como mod con respaldo y validación + ranura reservada | 5–8 | Un usuario no técnico rehace la cámara de una definitiva sin consola |
| **M4 Animación (F2)** | re-temporizar + poses vía Blender + añadir animaciones | 5–10 | Una técnica re-temporizada con los golpes en su frame |
| **M5 SPX (F3)** | desensamblador completo → línea de tiempo → edición en su sitio → inserciones | 10–20 | Lectura verificada con 38 guiones; ediciones sin cuelgues |

**Riesgos y mitigaciones:**
- **Opcodes SPX incompletos → cuelgues.** Hasta tener el intérprete, solo lectura y cambios en su sitio.
- **Marco o espejo de la cámara mal supuesto.** Lo cierra M0 con 1–2 capturas; el Studio dibuja con lo verificado.
- **Clip más largo que la espera del guion.** Se corta.
  - La línea de tiempo muestra la espera.
  - Para alargar habrá que editar la espera (cambio en su sitio, F3).
- **El override crece con el juego abierto → lectura truncada o cuelgue.** Tamaño reservado y relleno fijo; si no cabe, se pide reiniciar.
- **Versiones de Blender.** El puente usa glTF estándar. El fov animado depende de `KHR_animation_pointer` (Blender ≥ 4.2; probado en 5.2); como respaldo, el fov va en `extras`.
- **Animaciones re-temporizadas desincronizan golpes o efectos.** Desplazar los frames AP con la misma función de tiempo y validar.
- **Datos del usuario.** Solo se escribe en `mods/`, con respaldos y proyecto regenerable; nunca en los AFS originales.

## 6. Preguntas abiertas para el usuario

1. **Prioridad del MVP:**
   - ¿rehacer cámaras de técnicas de personajes **nativos** (override de su CAM bin)?
   - ¿o dar cámara propia a los **ports**? Gohan del Futuro no tiene ninguna y Zarbon usa la de su donante.
2. **Blender:** ¿lo recomendamos como opción para la comunidad, con el Studio funcionando también sin él? ¿O todo tiene que ir solo con el kit?
3. **Herramientas de desarrollo en el runtime:** ¿se puede añadir más adelante una tecla de "repetir cinemática" o una recarga en caliente? Exige cambios en C++, recompilar y recopiar las DLL.
4. **Alcance:** ¿basta con cámara y animación, o se esperan también **efectos** (rayos, auras de técnica)? Eso es otro formato (BSP) y mucho más trabajo.
5. **Forma del Studio:** ¿pestaña dentro del Mod Kit o ventana propia lanzada desde él? (Recomendado: ventana propia.)
6. **Sesión de capturas de M0:** ¿cuándo puede ser? El juego no se abre mientras usas el PC.

## Anexo: archivos de esta carpeta

- **Guía de la comunidad:** `amc_guide.txt` (extracto de `AMC_Guide.zip`).
- **Editor de la comunidad:** `anim_editor_community.py` (`Animation_Editor.zip`: solo intercambia animaciones, sin visor).
- **Copias de trabajo:** `amc_288_ps2.bin`, `spx_288.bin`, `zarbon_camara_hd_copia.bin`, `cam288_rt_*.bin`, `zarbon_cam_rt_hd.bin`.
- **Exportaciones glTF:** `goku_idle_clip0.glb`, `goku_clip24*.glb`, `zarbon_clip3.glb`.
- **Renders:** `render/`.
- **JSON:** `out_ps2/`, `out_hd/`.
- **Caché de afs_pair:** `cache/`.
