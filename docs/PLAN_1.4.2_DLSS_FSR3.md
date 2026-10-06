# Plan 1.4.2: DLSS y FSR 3 (2026-10-05)

Objetivo pedido por el usuario: DLSS y FSR3 de verdad (escalado temporal y, si se
puede, generación de fotogramas), tomando como referencia Burst Limit, Blue Dragon
(reblue) y Lost Odyssey.

## 1. Qué hay en cada referencia (revisado hoy)

| Proyecto | Base GPU | DLSS | FSR3 | Cómo saca los vectores de movimiento |
|---|---|---|---|---|
| Burst Limit (iExplosiveRage) | rexglue `rexgpu-xenos` | No | Stub del SDK (sin movimiento) | No los saca |
| reblue (zolaware, BSD-3) | GPU propia sobre plume | No | No | No hay escalado temporal |
| Lost Odyssey (freefrank, **GPL-3.0**) | GPU propia sobre plume | Sí: SR, DLAA y FG (Streamline) | Sí: FSR 3.1 SR + FG | **Re-ejecuta cada draw** con las constantes del frame anterior y escribe la velocidad por píxel ("motion replay") |

- Lost Odyssey es la única referencia con DLSS/FSR3 funcionando. Su código es
  GPL-3.0 y el nuestro es MIT: **se estudia, no se copia**. Se reimplementa la idea.
- Cambio respecto al estudio del 2026-09-29 (`VIABILIDAD_UPSCALING_TEMPORAL`):
  entonces no compilábamos la capa GPU. **Ahora sí**: `rexgpu-xenos` sale de
  nuestro `rexglue-sdk-0.10` (rama `dbz3-burstlimit`), así que el bloqueo principal
  ha desaparecido.
- El FidelityFX SDK (FSR 3.1 upscaler) ya se compila y enlaza
  (`amd_fidelityfx_dx12.dll`). `D3D12Presenter::DispatchTemporalUpscaler` existe,
  pero le pasa el color como profundidad y como movimiento, con `reset=true` en
  cada frame. El generador de fotogramas está apagado en
  `cmake/rexglue_fidelityfx.cmake`.

## 2. Cómo dibuja un fotograma de combate (medido hoy)

Traza nueva: crear `dbz3_frame_trace.req` junto al exe vuelca 3 frames como líneas
`dbz3: ft ...` (draws, copias de EDRAM y swap). Captura:
`scratchpad/ft_battle.txt` (Goku vs Goku, Torneo).

- 1280x720 nativo, **sin MSAA** en la escena. Un color en EDRAM base 0 y la
  profundidad en base 1328.
- **d0-d383 = escena 3D:**
  - escenario;
  - personajes, con varios VS distintos;
  - unos 210 quads con z-test y sin z-write, y luego sin z: efectos y partículas.
- **copy#384:** el juego resuelve la **profundidad** a una textura 1280x720.
  Ya la tenemos gratis.
- **copy#385 a copy#405:** post-proceso.
  - Color a un buffer que alterna cada frame (1F35F000 / 1EFC7000).
  - Reducción a 320x180 y bloom.
  - Composición en 1D991000.
- **d406-d477:** vuelve la composición y encima **el HUD**: unos 70 quads de 6
  vértices, sin profundidad.
- **copy#478, d479 y copy#480:** pasada final al front buffer 1F6F8000 y swap.

Consecuencia:
- La **frontera escena/HUD es limpia y genérica**: la escena va desde el inicio
  del frame hasta la primera copia de profundidad a resolución completa.
- Los menús, el select y otras pantallas sin 3D no tienen esa copia. Ahí no se
  aplica jitter y el escalador recibe imágenes quietas.

## 3. Plan por fases (cada fase se compila y se prueba en el juego antes de seguir)

1. **Jitter y profundidad.**
   - Desplazamiento sub-píxel (Halton) en `ndc_offset`, solo para los draws de
     la fase de escena.
   - La profundidad real de esa fase se pasa al escalador.
   - FSR 3.1 se prueba con movimiento solo de cámara, con un interruptor oculto.
2. **Vectores de movimiento por re-ejecución (la pieza grande).**
   - Se registra cada draw de escena: VS, buffers, índices y una copia propia de
     sus constantes.
   - Se empareja con el mismo draw del frame anterior: hash de VS y PS, buffer
     de posiciones, índices, número de vértices y orden.
   - Al terminar la escena se vuelve a dibujar con una modificación del VS que
     ejecuta el cuerpo dos veces, con las constantes anteriores y las actuales,
     y escribe la diferencia en un RT R16G16. La prueba de profundidad usa la
     de la escena.
   - Es lo que hace Lost Odyssey. El cambio está en `dxbc_translator.cpp`: el
     cuerpo se traduce dos veces y se guarda la posición de la primera pasada.
3. **Máscara del HUD.**
   - Se compara la composición previa al HUD (1D991000) con la salida final.
   - Los píxeles que cambian forman la máscara reactiva para el escalador, y así
     el HUD no deja estela.
4. **FSR 3.1 real.** Escalado temporal con todo lo anterior y opción en
   Launcher → Vídeo y en el menú F4.
5. **DLSS (SR y DLAA).**
   - Usa el mismo contrato: NGX en D3D12.
   - Requiere descargar el SDK oficial de NVIDIA (código de terceros: **pedir
     permiso**) y redistribuir `nvngx_dlss.dll`. Su licencia lo permite;
     revisarla antes de publicar.
6. **Generación de fotogramas (opcional, si lo anterior queda bien).**
   - FSR 3.1 FG con el proveedor de frame gen del FFX SDK, hoy apagado.
   - DLSS FG requiere Streamline y es más trabajo.
   - El juego va fijo a 60, así que FG daría 120 en pantallas rápidas.
7. **Vulkan y Linux:** FSR 3.1 en Vulkan con el mismo contrato. DLSS en Linux es
   opcional.

## 4. Riesgos conocidos

- La re-ejecución duplica el coste de vértices de la escena. Son ~380 draws:
  asumible.
- Los draws con alpha-test (pelo, público) pueden dar velocidad donde el original
  descartó el píxel. Lost Odyssey reutiliza el PS original para la cobertura; lo
  copiaremos en la fase 2b si hace falta.
- Efectos que reutilizan direcciones de buffers cada frame. El emparejamiento debe
  rechazar lo dudoso y dejar velocidad cero con la máscara reactiva.
- La escala de dibujo del SDK es un entero (1x, 2x, 3x). La resolución interna de
  DLSS/FSR (Quality, Balanced, Performance) se obtiene renderizando a escala 1x o
  2x y escalando a la pantalla. No hace falta tocar la escala del guest.
