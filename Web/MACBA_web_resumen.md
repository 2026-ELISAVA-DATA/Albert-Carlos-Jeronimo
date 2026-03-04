# MACBA x SKATE — Cómo funciona la web (resumen técnico)

> Web **estática** (sin backend / sin build). Corre 100% en el navegador con **Three.js** + **PapaParse**.  
> Idea central: **cada fila de un CSV = 1 punto**, y esos puntos se “pegan” a la **superficie** del modelo 3D del MACBA.

---

## Estructura del proyecto

- **`index.html`**  
  Contiene TODO: HTML + CSS + JS + shaders + UI.  
  Además incluye embebido:
  - **MACBA GLB** en Base64
  - **Tweets CSV** en Base64

- **`macba_env.glb`**  
  Entorno urbano (plaza) en el **mismo sistema de coordenadas** que el MACBA, pero **sin el edificio** (queda el “agujero”).

- **`Scrapduck_multiquery_MACBA_masclicks.csv`**  
  Artículos web (se carga con `fetch()`).

---

## Flujo general

1. **Intro** (frases) → **#SAVEMACBA** → **video**
2. Termina el video (o **SKIP**) → entra a la **app**
3. `init()`:
   - carga datasets (tweets base64 + artículos CSV)
   - arma UI (layers + filtros)
   - carga el **MACBA GLB** (base64)
4. Cuando el MACBA carga:
   - se **centra** y se “apoya” en el suelo (bounding box)
   - se ajusta la **cámara**
   - se calcula cuántos puntos hay que dibujar (**N = total filas visibles**)
5. Se **samplea la superficie** del modelo para generar N posiciones
6. Cada dataset se renderiza como su **capa de puntos** (`THREE.Points`)
7. Los puntos aparecen con **build progresivo** (de a tandas)
8. Se genera el look **holographic wire/halo** del MACBA
9. Se carga el **entorno** (`macba_env.glb`) y se alinea con el mismo offset
10. Interacción: hover/click, filtros, sentimiento, constellations, record, export/import

---

## Datos → Puntos (pipeline)

### Carga y parseo de CSV
- Se parsea con **PapaParse** (`header: true`)
- Cada fila queda como un objeto con:
  - `label/title`
  - `url/link`
  - `desc/description`
  - `fields` (todas las columnas originales)

### Surface Sampling (pegar puntos al MACBA)
La app genera posiciones sobre la piel del modelo:

- recorre triángulos de la geometría
- calcula área por triángulo
- elige triángulos proporcionalmente al área
- coloca puntos uniformes dentro del triángulo (barycentric)

Resultado: un `Float32Array(N*3)` con XYZ sobre la superficie.

---

## Render 3D (qué se dibuja)

### 1) MACBA (ghost / halo)
- Wireframe con `EdgesGeometry` (líneas cian con blending aditivo)
- Un mesh suave casi invisible para dar volumen
- Pequeña animación “respiración” de opacidad

### 2) Capas de datos (Points)
Cada dataset = una capa `THREE.Points` con shader custom:

Atributos por punto:
- posición
- tamaño
- opacidad
- brillo  
(+ un micro “jitter” para que no quede perfecto)

---

## Build progresivo (efecto “se construye”)

En vez de mostrar todo de una:
- se arma una cola de puntos visibles
- cada frame se “encienden” opacidades en batches
- la UI muestra progreso (barra + contador)

---

## Entorno (plaza) y alineación del “agujero”

> **Clave del proyecto**: el entorno fue exportado en el **mismo espacio** que el MACBA, pero con el edificio removido.

Por eso el alineado funciona así:
- al MACBA se le aplica un `mWorldOffset` (centrar + suelo)
- al entorno se le aplica **el mismo offset**
- el slider **Offset Y** ajusta altura sin romper X/Z

---

## Interacción (hover / click)

### Hover
- Raycasting sobre `THREE.Points`
- Si pega en un punto:
  - lo agranda
  - muestra **card** con info (título, url, descripción)
  - muestra ring en el cursor

### Click
- abre panel **DETAIL** con todos los campos (`fields`) + botón para abrir URL

---

## Filtros principales

### ALL vs capa
- Botones: `ALL`, `TWEETS`, `ARTICULOS`, etc.
- Cuando cambiás filtro: **rebuild**
  - recalcula N (solo visibles)
  - vuelve a samplear superficie
  - reconstruye buffers de las capas visibles
  - reinicia build progresivo

> Esto evita “huecos raros” al apagar capas.

---

## Sentimiento (POS / NEG)

- Si el CSV trae `sentiment/sentimiento`, lo usa.
- Si no, infiere por keywords (fine/ban/restriction/noise/multa/daño/etc.) en título/desc/url.
- Al activar:
  - colorea puntos (por vértice) y baja opacidad de los que no matchean.

---

## Constellations + tiempo (año/mes)

- Agrupa por `date` (ideal: `YYYY-MM-DD`)
- Conecta cada punto con sus vecinos más cercanos dentro del grupo → `LineSegments`
- Filtro por año/mes:
  - los que quedan fuera se “empujan” hacia afuera y se desvanecen

---

## Recording + Export/Import

### REC
- `canvas.captureStream(30)` + `MediaRecorder`
- Descarga `.webm`

### Export/Import
- Exporta un JSON con:
  - sources + settings + datos
- Import lo reinyecta y reconstruye la escena

---

## Ajustes rápidos (tuning)

- **Densidad / look de puntos**
  - `spread` (jitter)
  - tamaño base global + tamaño por layer
  - batch del build (velocidad de aparición)

- **Alineación entorno**
  - mismo offset del MACBA
  - `Offset Y` para subir/bajar entorno (sin tocar X/Z)

- **Sentimiento**
  - lista de keywords negativas (si querés hacerlo más estricto o más sensible)

---

## TL;DR

- Carga datos → calcula N puntos
- Samplea superficie del MACBA → genera posiciones
- Dibuja capas como Points con shaders (neón)
- Build progresivo + wireframe ghost
- Carga entorno y lo alinea con el mismo offset (agujero calza)
- Hover/click + filtros + sentimiento + constellations + grabación
