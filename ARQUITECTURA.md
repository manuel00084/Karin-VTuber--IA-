# Karin Nova Engine 3D - Smart Avatar System

## Arquitectura del Sistema y Especificación Técnica

**Versión:** 1.0.0
**Estado:** Diseño / Pre-desarrollo
**Licencia:** Privada — Karin VTuber Project

---

## 1. Visión General

Karin Nova Engine 3D es un motor de avatares inteligentes diseñado como alternativa
moderna a Live2D y sistemas similares. A diferencia de enfoques tradicionales que
requieren rigs manuales, artwork por capas y configuración artesanal, este sistema
toma una **única imagen PNG o JPG** de un personaje y genera automáticamente un
avatar tridimensional completely funcional.

El usuario abre una imagen, espera el procesamiento, y obtiene un avatar listo para
ser controlado por voz, tracking facial, expresiones manuales o scripts. No hay
 vértices que ajustar, no hay huesos que posicionar, no hay pesos que pintar.

**Propuesta de valor:**
- **Entrada:** Una imagen 2D de personaje (PNG/JPG con fondo transparente preferido).
- **Salida:** Avatar 3D renderizado en tiempo real, expresivo, con física y tracking.
- **Proceso:** Automático. Sin intervención manual obligatoria.
- **Alternativa a:** Live2D, VTube Studio, PRPR Live, FaceRig.

---

## 2. Filosofía de Diseño

### Principio Fundamental

> **La IA trabaja una vez. El runtime es puro OpenGL.**

Todo el procesamiento pesado (análisis de imagen, generación de malla, esqueleto,
blend shapes, física) ocurre **una sola vez** durante la fase de importación. Una
vez que el archivo `.kar` está generado, el runtime no necesita modelos de IA,
redes neuronales ni inferencia. Es código nativo ejecutando matemáficas puras.

### Pilares

| Pilar | Descripción |
|---|---|
| **Automatización total** | El usuario no necesita conocimientos técnicos. Abre imagen → obtiene avatar. |
| **Rendimiento** | 60 FPS estables en hardware moderado. Uso mínimo de CPU/GPU. |
| **Modularidad** | Cada componente es independiente, reemplazable y testeable. |
| **Extensibilidad** | Nuevos trackings, shaders, efectos y formatos se agregan sin modificar el core. |
| **Bajo consumo** | El avatar no debe consumir más recursos que un sprite 2D estático en idle. |

### Separación de Responsabilidades

```
[ Fase de Importación ]          [ Fase de Runtime ]
         │                                │
    IA / Análisis                    OpenGL puro
    Generación pesada                Física por resortes
    CPU intensiva                    Interpolación de ejes
         │                                │
         ▼                                ▼
    Archivo .kar                  Pantalla / Stream
```

---

## 3. Flujo del Usuario

```
┌─────────────────────────────────────────────────────────┐
│  1. El usuario abre Karin Nova Engine                   │
│  2. Selecciona "Nuevo Avatar"                           │
│  3. Elige una imagen PNG o JPG                          │
│  4. El sistema muestra barra de progreso:               │
│     ├── Analizando estructura del personaje...          │
│     ├── Generando malla deformable...                   │
│     ├── Construyendo esqueleto lógico...                │
│     ├── Creando blend shapes (ojos, boca, cejas)...     │
│     ├── Simulando física del cabello y ropa...          │
│     └── Empaquetando en formato .kar...                 │
│  5. El avatar aparece en la vista previa                │
│  6. El usuario puede ajustar parámetros (opcional)     │
│  7. El avatar está listo para usar                      │
└─────────────────────────────────────────────────────────┘
```

**Tiempo estimado de procesamiento:**
- Imagen simple (256×256): 3-8 segundos
- Imagen detallada (1024×1024): 10-30 segundos
- Imagen compleja (2048×2048): 20-60 segundos

**Tiempo de carga del avatar generado:**
- Menos de 500ms desde la selección del archivo `.kar`

---

## 4. Arquitectura Modular

```
karin_nova_engine/
│
├── core/
│   ├── types.py              # Tipos base: Vector2, Vector3, Matrix, Color, Rect
│   ├── interfaces.py         # Interfaces abstractas para todos los módulos
│   ├── body_graph.py         # Grafo de relaciones del cuerpo
│   ├── exceptions.py         # Excepciones del dominio
│   └── constants.py          # Constantes del sistema
│
├── analyzer/
│   ├── __init__.py
│   ├── character_analyzer.py # Analizador principal de imágenes
│   ├── color_detector.py     # Detección de regiones por color
│   ├── symmetry_detector.py  # Detección de simetría del personaje
│   ├── part_mapper.py        # Mapeo de partes del cuerpo
│   └── segmenter.py          # Segmentación semántica de la imagen
│
├── mesh/
│   ├── __init__.py
│   ├── auto_mesh_generator.py # Generación automática de malla
│   ├── delaunay.py           # Triangulación de Delaunay adaptativa
│   ├── density_calculator.py # Cálculo de densidad de vértices por zona
│   ├── contour_detector.py   # Detección de contornos del personaje
│   ├── uv_mapper.py          # Mapeo UV automático
│   └── mesh_simplifier.py    # Reducción de polígonos por zona
│
├── skeleton/
│   ├── __init__.py
│   ├── skeleton_generator.py # Generación del esqueleto lógico
│   ├── bone.py               # Clase Bone con jerarquía y constraints
│   ├── rig_builder.py        # Construcción del rig automático
│   ├── ik_solver.py          # Resolvedor de cinematica inversa
│   └── constraints.py        # Limitaciones articulares por tipo de hueso
│
├── blendshapes/
│   ├── __init__.py
│   ├── blendshape_generator.py  # Generador de blend shapes
│   ├── eye_shapes.py            # Parpadeo, mirada, sorpresa
│   ├── mouth_shapes.py          # Vocales, sonrisa, tristeza
│   ├── eyebrow_shapes.py        # Cejas: angry, sad, surprise, neutral
│   ├── emotion_composer.py      # Combinación de shapes por emoción
│   └── phoneme_mapper.py        # Mapa fonema → shape de boca
│
├── physics/
│   ├── __init__.py
│   ├── physics_generator.py    # Generador de parámetros de física
│   ├── spring_engine.py        # Motor de resortes para simulación
│   ├── spring.py               # Clase Spring individual
│   ├── hair_simulator.py       # Simulación de cabello por segmentos
│   ├── cloth_simulator.py      # Simulación de ropa suelta
│   ├── breathing.py            # Simulación de respiración
│   └── collision.py            # Detección de colisiones básicas
│
├── runtime/
│   ├── __init__.py
│   ├── renderer.py             # Renderizador principal OpenGL
│   ├── avatar_controller.py    # Controlador del avatar en tiempo real
│   ├── animation_mixer.py      # Mezclador de animaciones y poses
│   ├── interpolation.py        # Interpolación suave (ease-in, spring, etc.)
│   ├── render_pass.py          # Pipeline de render passes
│   ├── camera.py               # Cámara 3D virtual
│   └── display.py              # Gestión de ventana/output
│
├── tracking/
│   ├── __init__.py
│   ├── tracking_provider.py    # Interface abstracta de tracking
│   ├── tracking_hub.py         # Multiplexor de providers activos
│   ├── mediapipe_provider.py   # MediaPipe Face Mesh
│   ├── openseeface_provider.py # OpenSeeFace
│   ├── arkit_provider.py       # ARKit blend shapes (iPhone)
│   ├── hotkey_provider.py      # Control por teclado/mouse
│   └── idle_provider.py        # Animación idle automática
│
├── shaders/
│   ├── __init__.py
│   ├── shader_compiler.py     # Compilador y cache de shaders
│   ├── shader_pass.py         # Clase base para cada efecto
│   ├── cel_shader.py          # Cel shading / toon rendering
│   ├── outline_shader.py      # Outline / edge detection
│   ├── bloom_shader.py        # Bloom post-processing
│   ├── color_grading.py       # Ajuste de color global
│   ├── shadow_shader.py       # Sombras suaves
│   └── glow_shader.py         # Efecto de brillo selectivo
│
├── editor/
│   ├── __init__.py
│   ├── editor_ui.py           # Interfaz del editor de avatares
│   ├── slider_panel.py        # Paneles de parámetros deslizantes
│   ├── preview_viewport.py    # Vista previa en tiempo real
│   ├── expression_editor.py   # Editor de expresiones faciales
│   ├── physics_editor.py      # Editor de parámetros de física
│   └── export_panel.py        # Panel de exportación a .kar
│
├── format/
│   ├── __init__.py
│   ├── kar_package.py         # Lector/Escritor del formato .kar
│   ├── kar_manifest.py        # Estructura del manifiesto .kar
│   └── kar_validator.py       # Validación de integridad del archivo
│
└── utils/
    ├── __init__.py
    ├── image_utils.py         # Carga, redimensionamiento, conversión
    ├── math_utils.py          # Funciones matemáticas auxiliares
    ├── geometry.py            # Operaciones geométricas
    └── logger.py              # Sistema de logging del motor
```

---

## 5. Grafo de Relaciones del Cuerpo (Body Relationship Graph)

El grafo de relaciones del cuerpo es la estructura central que define cómo cada
parte del avatar interactúa con las demás. Cada nodo representa una parte del
cuerpo y contiene información sobre sus dependencias, restricciones y cómo
transmite movimiento.

### Estructura del Nodo

```python
class BodyNode:
    id: str                    # "head", "left_upper_arm", "hair_tip_03"
    parent: Optional[str]      # Nodo padre en la jerarquía
    children: List[str]        # Nodos hijos directos
    depends_on: List[str]      # Nodos que afectan a este (para actualización)
    influences: List[str]      # Nodos que este afecta (propagación)
    transform: Transform3D     # Transformación local actual
    constraints: Constraints   # Límites de rotación/escala/traslación
    weight: float              # Qué tanto influye el tracking en este nodo
    blend_group: str           # Grupo de blend shapes al que pertenece
    physics_type: str          # "rigid", "spring", "cloth", "none"
```

### Grafo de Ejemplo

```
                    [root]
                      │
            ┌─────────┼─────────┐
         [torso]   [hips]    [hair_root]
            │        │           │
       ┌────┼────┐   │      ┌───┼───┐
   [neck] [l_arm] [r_arm] [hair_1] [hair_2] ...
      │      │
   [head] [l_forearm]
      │      │
  ┌───┼───┐ [l_hand]
 [l_eye] [r_eye] [mouth]
    │
 [l_eyelid]
```

### Propagación de Movimiento

Cuando un nodo cambia su transformación, la actualización se propaga así:

1. **Hacia abajo (forward):** El nodo padre actualiza a todos sus hijos.
2. **Hacia los dependientes (lateral):** Si la cabeza gira, los ojos, cejas
   y boca se ajustan según el `depends_on`.
3. **Hacia los influidos (cascade):** El cabello responde al movimiento de
   la cabeza, la ropa al movimiento de los brazos, etc.

```python
def propagate_update(graph: BodyGraph, changed_node: str):
    """Propaga el cambio de un nodo a todos sus dependientes."""
    node = graph.get(changed_node)

    # 1. Actualizar hijos directos
    for child_id in node.children:
        child = graph.get(child_id)
        child.transform.update_from_parent(node.transform)

    # 2. Actualizar nodos dependientes (laterales)
    for dep_id in node.depends_on:
        dep = graph.get(dep_id)
        dep.apply_external_influence(node)

    # 3. Propagar a influidos (recursivo)
    for inf_id in node.influences:
        inf = graph.get(inf_id)
        inf.react_to_change(node)
        propagate_update(graph, inf_id)  # En cadena
```

### Tipos de Relaciones

| Tipo | Descripción | Ejemplo |
|---|---|---|
| **jerárquica** | Padre → hijo directo | Brazo superior → antebrazo |
| **dependencia** | Un nodo necesita datos de otro | Ojos dependen de cabeza |
| **influencia** | Un nodo afecta a otro sin jerarquía | Cabeza influye en cabello |
| **física** | Respuesta por resortes/cloth | Mechones de cabello |
| **blend** | Comparten grupo de deformación | Cejas izq/der comparten grupo |

---

## 6. Pipeline de Procesamiento

### Fase 1: Análisis de Imagen

```
Imagen de entrada (PNG/JPG)
        │
        ▼
┌─────────────────────────┐
│   CharacterAnalyzer     │
│                         │
│  1. Preprocesamiento:   │
│     - Escala a 512x512  │
│     - Elimina ruido     │
│     - Detecta fondo     │
│                         │
│  2. Segmentación:       │
│     - Regiones por color│
│     - Contornos         │
│     - Simetría          │
│                         │
│  3. Clasificación:      │
│     - Cabeza            │
│     - Torso             │
│     - Brazos            │
│     - Piernas           │
│     - Cabello           │
│     - Accesorios        │
│                         │
│  Salida: CharacterJSON  │
└─────────────────────────┘
```

### Fase 2: Generación de Malla

```
CharacterJSON
        │
        ▼
┌─────────────────────────┐
│   AutoMeshGenerator     │
│                         │
│  1. Contorno:           │
│     - Extracción de     │
│       bordes externos   │
│     - Suavizado         │
│                         │
│  2. Triangulación:      │
│     - Delaunay adaptat. │
│     - Densidad variable │
│       (cara = alta,     │
│        torso = baja)    │
│                         │
│  3. UV Mapping:         │
│     - Proyección por    │
│       región            │
│     - Optimización de   │
│       espacio de textura│
│                         │
│  Salida: AvatarMesh     │
└─────────────────────────┘
```

### Fase 3: Generación de Esqueleto

```
AvatarMesh + CharacterJSON
        │
        ▼
┌─────────────────────────┐
│   SkeletonGenerator     │
│                         │
│  1. Centros de masa:    │
│     - Cabeza            │
│     - Torso             │
│     - Articulaciones    │
│                         │
│  2. Construcción:       │
│     - Huesos jerárquicos│
│     - IK targets        │
│     - Constraints       │
│                         │
│  3. Skin weights:       │
│     - Auto-painting     │
│     - Smooth blending   │
│                         │
│  Salida: AvatarSkeleton │
└─────────────────────────┘
```

### Fase 4: Blend Shapes

```
AvatarMesh + CharacterJSON + AvatarSkeleton
        │
        ▼
┌─────────────────────────┐
│  BlendShapeGenerator    │
│                         │
│  1. Morfología facial:  │
│     - 12 formas de boca │
│     - 8 formas de ojos  │
│     - 6 formas de cejas │
│     - 4 expresiones base│
│                         │
│  2. Deformación:        │
│     - Delta vectors     │
│     - Suavizado         │
│     - Sin intersección  │
│                         │
│  Salida: BlendShapes[]  │
└─────────────────────────┘
```

### Fase 5: Física

```
AvatarMesh + AvatarSkeleton + BlendShapes
        │
        ▼
┌─────────────────────────┐
│   PhysicsGenerator      │
│                         │
│  1. Detección:          │
│     - Zonas de cabello  │
│     - Zonas de ropa     │
│     - Zonas de respirac.│
│                         │
│  2. Configuración:      │
│     - Resortes por nodo │
│     - Masa, rigidez,    │
│       amortiguación     │
│     - Gravedad          │
│                         │
│  3. Colisiones:         │
│     - Bounding shapes   │
│     - Respuesta básica  │
│                         │
│  Salida: PhysicsConfig  │
└─────────────────────────┘
```

### Fase 6: Empaquetado

```
Todo lo generado
        │
        ▼
┌─────────────────────────┐
│   kar_package.py        │
│                         │
│  1. Serialización:      │
│     - Mesh → binario    │
│     - Skeleton → JSON   │
│     - BlendShapes → JSON│
│     - Physics → JSON    │
│     - Textura → PNG     │
│                         │
│  2. Compresión:         │
│     - ZIP level 6       │
│     - Texturas optimiz. │
│                         │
│  3. Validación:         │
│     - Integridad        │
│     - Versionado        │
│                         │
│  Salida: avatar.kar     │
└─────────────────────────┘
```

---

## 7. Arquitectura del Runtime

El runtime es la fase que se ejecuta durante la sesión del usuario. **No contiene
IA, ni modelos de inferencia, ni procesamiento de imágenes.** Solo OpenGL puro,
matemáficas y tablas de valores precomputados.

### Ciclo de Renderizado (cada frame)

```
┌──────────────────────────────────────────────────┐
│                  FRAME LOOP                       │
│                                                  │
│  1. Input                                        │
│     ├── Tracking provider → raw pose             │
│     ├── Hotkeys → manual expressions             │
│     └── Script engine → scripted animations      │
│                                                  │
│  2. Update (60 Hz)                               │
│     ├── AvatarController                         │
│     │   ├── Mapear input → blend shape weights   │
│     │   ├── Mapear input → bone rotations        │
│     │   └── Interpolación suave entre poses      │
│     ├── SpringEngine                             │
│     │   ├── Calcular fuerzas                     │
│     │   ├── Resolver resortes                     │
│     │   ├── Aplicar colisiones                   │
│     │   └── Actualizar posiciones de mesh         │
│     └── AnimationMixer                           │
│         ├── Mezclar idle + tracking + manual     │
│         └── Aplicar prioridades                   │
│                                                  │
│  3. Render (GPU)                                 │
│     ├── Pass 1: Shadow map                       │
│     ├── Pass 2: Main render (cel shading)        │
│     ├── Pass 3: Outline                          │
│     ├── Pass 4: Bloom                            │
│     ├── Pass 5: Color grading                    │
│     └── Pass 6: Composite → Output               │
│                                                  │
│  4. Swap buffers → Display                       │
└──────────────────────────────────────────────────┘
```

### Rendimiento Objetivo

| Métrica | Objetivo |
|---|---|
| FPS | 60 estables (30 mínimo aceptable) |
| CPU (idle) | < 5% en un Ryzen 5 3600 |
| CPU (tracking) | < 15% con MediaPipe activo |
| RAM (avatar) | < 200 MB con textura de 2K |
| VRAM | < 100 MB |
| Latencia input→render | < 16ms (1 frame) |

### Componentes del Runtime

**Renderer (OpenGL 4.5+):**
- VAO/VBO dinámicos para malla deformable
- Textura array para atlas de blend shapes
- Framebuffer objects para post-processing
- Shader compilation con cache en disco

**AvatarController:**
- Recibe pose del tracking provider
- Convierte ángulos del tracking a pesos de blend shapes
- Gestiona prioridades: manual > tracking > idle
- Interpolación configurable (lineal, ease, spring)

**SpringEngine:**
- Simulación de resortes damped
- Paso variable con acumulador de tiempo
- Límite de 50 resortes por avatar (rendimiento)
- Actualización en CPU, Upload a GPU por VBO

---

## 8. Abstracción de Tracking

El sistema de tracking está diseñado para ser **completamente agnóstico al proveedor**.
Cualquier fuente de datos de tracking se adapta mediante una interface común.

### Interface Base

```python
class TrackingProvider(ABC):
    """Interface que todo proveedor de tracking debe implementar."""

    @abstractmethod
    def start(self) -> bool:
        """Inicializa el proveedor. Retorna True si éxito."""

    @abstractmethod
    def stop(self):
        """Detiene el proveedor y libera recursos."""

    @abstractmethod
    def get_pose(self) -> TrackingPose:
        """Retorna la pose actual del usuario detectada."""

    @abstractmethod
    def is_active(self) -> bool:
        """Indica si el proveedor está activo y detectando."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Nombre legible del proveedor."""

    @property
    @abstractmethod
    def supported_blend_shapes(self) -> List[str]:
        """Lista de blend shapes que este proveedor puede alimentar."""
```

### TrackingPose (datos estándar de salida)

```python
@dataclass
class TrackingPose:
    timestamp: float
    head_rotation: Vector3      # Pitch, Yaw, Roll en grados
    eye_left: Vector2           # Dirección del ojo izquierdo
    eye_right: Vector2          # Dirección del ojo derecho
    mouth_open: float           # 0.0 (cerrado) a 1.0 (abierto)
    eyebrow_left: float         # -1.0 (fruncido) a 1.0 (levantado)
    eyebrow_right: float
    jaw_open: float             # Apertura de mandíbula
    blend_shapes: Dict[str, float]  # Pesos adicionales del proveedor
    confidence: float           # Nivel de confianza 0.0 a 1.0
```

### Providers Implementados

| Provider | Fuente | Requisitos | Blend Shapes |
|---|---|---|---|
| **MediaPipe** | Webcam | `mediapipe` | 468 landmarks → 30+ shapes |
| **OpenSeeFace** | Webcam | `openseeface-py` | 68 puntos → 20+ shapes |
| **ARKit** | iPhone | `arkit_bridge` | 52 blend shapes nativos |
| **Hotkey** | Teclado/Mouse | Nada | Todos (manual) |
| **Idle** | Automático | Nada | Básicos (respiración, parpadeo) |

### TrackingHub (Multiplexor)

```python
class TrackingHub:
    """Combina datos de múltiples proveedores con prioridades."""

    providers: List[Tuple[TrackingProvider, float]]  # (provider, weight)

    def get_blended_pose(self) -> TrackingPose:
        """
        Mezcla las poses de todos los proveedores activos.
        El peso define cuánto influye cada uno.
        Si un proveedor no tiene un blend shape, se ignora.
        """
        ...
```

---

## 9. Sistema de Shaders

Cada efecto visual es un **pass independiente** que se puede activar, desactivar
o reordenar sin afectar a los demás. El pipeline de shaders es configurable por
el usuario desde el editor.

### Arquitectura de Passes

```
┌─────────────────────────────────────────────┐
│              SHADER PIPELINE                │
│                                             │
│  [Input] ──→ [Pass Chain] ──→ [Output]     │
│                                             │
│  Pass Chain (configurable):                 │
│  ┌─────────────────────────────────────┐    │
│  │ 1. Cel Shader        (obligatorio) │    │
│  │ 2. Shadow Pass       (opcional)    │    │
│  │ 3. Outline Pass      (opcional)    │    │
│  │ 4. Bloom Pass        (opcional)    │    │
│  │ 5. Glow Pass         (opcional)    │    │
│  │ 6. Color Grading     (opcional)    │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  Cada pass usa su propio FBO (Framebuffer) │
│  Se pueden insertar/remover dinámicamente   │
└─────────────────────────────────────────────┘
```

### Shaders Disponibles

| Shader | Tipo | Descripción | Costo |
|---|---|---|---|
| `cel_shader` | Vertex+Fragment | Toon rendering con steps de color | Bajo |
| `outline_shader` | Fragment | Detecta bordes por diferencia de normales/depth | Bajo |
| `bloom_shader` | Fragment (2-pass) | Resplandor suave en zonas brillantes | Medio |
| `shadow_shader` | Fragment | Sombras proyectadas suaves | Bajo |
| `glow_shader` | Fragment | Brillo selectivo por máscara | Bajo |
| `color_grading` | Fragment | Ajuste de temperatura, contraste, saturación | Muy bajo |

### Compilación y Cache

```python
class ShaderCompiler:
    """Compila shaders GLSL con cache en disco."""

    def compile(self, shader_type: str, source: str) -> ShaderProgram:
        """
        Compila un shader. Si ya fue compilado y el source no cambió,
        retorna la versión en cache.
        """
        cache_key = self._hash(source, shader_type)
        if cache_key in self.disk_cache:
            return self.disk_cache.load(cache_key)
        program = self._compile_glsl(source)
        self.disk_cache.save(cache_key, program)
        return program
```

### Shader Base (GLSL ejemplo)

```glsl
// cel_shader.glsl — Fragment
#version 450 core

uniform sampler2D u_texture;
uniform sampler2D u_ramp;         // Textura rampa para cel shading
uniform int u_steps;              // Número de steps (3-8)
uniform vec3 u_light_dir;         // Dirección de luz

in vec2 v_texcoord;
in vec3 v_normal;
in vec3 v_world_pos;

out vec4 frag_color;

void main() {
    vec4 tex_color = texture(u_texture, v_texcoord);
    float NdotL = dot(normalize(v_normal), normalize(u_light_dir));

    // Cuantizar la iluminación
    float steps = float(u_steps);
    float quantized = floor(NdotL * steps) / steps;
    quantized = clamp(quantized, 0.1, 1.0);

    vec3 ramp_color = texture(u_ramp, vec2(quantized, 0.5)).rgb;
    frag_color = vec4(tex_color.rgb * ramp_color, tex_color.a);
}
```

---

## 10. Formato .kar

El formato `.kar` es un archivo **ZIP con extensión renombrada** que contiene
todos los datos necesarios para cargar y renderizar un avatar. Es autocontenido,
versionado y validado.

### Estructura Interna

```
avatar.kar (ZIP)
│
├── manifest.json              # Manifiesto del paquete
├── avatar.json                # Datos completos del avatar
│
├── textures/
│   ├── diffuse.png            # Textura base (RGBA)
│   ├── normal.png             # Mapa de normales (opcional)
│   └── emission.png           # Mapa de emisión (opcional)
│
├── mesh/
│   ├── vertices.bin           # Vértices empaquetados (float32)
│   ├── indices.bin            # Índices empaquetados (uint16)
│   └── uvs.bin                # Coordenadas UV (float32)
│
├── skeleton/
│   ├── bones.json             # Definición de huesos
│   ├── skin_weights.json      # Pesos de skinning
│   └── constraints.json      # Restricciones articulares
│
├── blendshapes/
│   ├── deltas.json            # Vectores delta por blend shape
│   └── groups.json            # Grupos y configuraciones
│
├── physics/
│   ├── springs.json           # Definición de resortes
│   ├── collisions.json        # Shapes de colisión
│   └── parameters.json        # Parámetros generales
│
├── expressions/
│   ├── happy.json             # Perfil de emoción
│   ├── sad.json
│   ├── angry.json
│   ├── surprised.json
│   └── custom/               # Expresiones personalizadas
│
└── metadata.json              # Versión, autor, fecha, tags
```

### manifest.json

```json
{
    "format_version": "1.0.0",
    "engine_version": "1.0.0",
    "created": "2026-07-20T12:00:00Z",
    "modified": "2026-07-20T12:00:00Z",
    "author": "Karin Nova Engine",
    "description": "Avatar generado automáticamente",
    "avatar_name": "Karin Default",
    "source_image": "original.png",
    "checksum": "sha256:a1b2c3d4...",
    "file_count": 18,
    "total_size_bytes": 4194304
}
```

### avatar.json (simplificado)

```json
{
    "version": "1.0.0",
    "format": "karin_nova_3d",
    "statistics": {
        "vertex_count": 2400,
        "triangle_count": 4200,
        "bone_count": 32,
        "blendshape_count": 46,
        "spring_count": 24
    },
    "rendering": {
        "default_shader": "cel_shader",
        "outline_enabled": true,
        "outline_thickness": 1.5,
        "bloom_enabled": false
    },
    "physics": {
        "global_damping": 0.95,
        "gravity": -9.8,
        "max_springs_active": 50
    },
    "tracking": {
        "default_provider": "mediapipe",
        "sensitivity": 1.0,
        "smoothing": 0.3
    }
}
```

### Validación

```python
class KARValidator:
    """Valida la integridad y compatibilidad de un archivo .kar."""

    def validate(self, path: str) -> ValidationResult:
        errors = []
        warnings = []

        # 1. Verificar que es un ZIP válido
        # 2. Verificar manifest.json existe y es válido
        # 3. Verificar archivos obligatorios presentes
        # 4. Verificar checksum contra contenido
        # 5. Verificar versión del formato compatible
        # 6. Verificar que datos de mesh son consistentes
        # 7. Verificar que texturas existen y son válidas

        return ValidationResult(errors, warnings)
```

---

## 11. Requisitos Técnicos

### Entorno de Desarrollo

| Componente | Requisito |
|---|---|
| **Python** | 3.10 o superior |
| **OpenGL** | 4.5 core profile mínimo |
| **GLFW** | 3.3+ (ventana y contexto GL) |
| **PyOpenGL** | 2.0+ (bindings Python → OpenGL) |
| **NumPy** | 1.24+ (operaciones matemáticas) |
| **Pillow** | 10.0+ (carga de imágenes) |
| **pytest** | 8.0+ (testing) |

### Dependencias Opcionales (tracking)

| Proveedor | Paquete | Requisito adicional |
|---|---|---|
| MediaPipe | `mediapipe` | CPython 3.10-3.12 |
| OpenSeeFace | `openseeface-py` | Modelo descargado |
| ARKit | `arkit_bridge` | macOS + iPhone |
| TTS (voz) | `edge-tts` | Conexión a internet |

### Principios de Código

- **OOP modular:** Cada módulo es una clase o conjunto de clases con responsabilidad única.
- **Interfaces abstractas:** Todo componente expuesto se define con `ABC` y se implementa aparte.
- **Type hints:** Todos los parámetros y retornos tipados con `typing`.
- **Docstrings:** Mínimo en interfaces públicas. Explicación completa en módulos públicos.
- **Testing:** Cobertura mínima del 70% en módulos de `core/`, `analyzer/`, `mesh/`.
- **Logging:** Usar el sistema de logging del proyecto, nunca `print()` en código de producción.

### Testing

```
tests/
├── test_analyzer.py          # Tests del CharacterAnalyzer
├── test_mesh_generator.py    # Tests de generación de malla
├── test_skeleton.py          # Tests del esqueleto y constraints
├── test_blendshapes.py       # Tests de blend shapes
├── test_spring_engine.py     # Tests del motor de resortes
├── test_kar_format.py        # Tests de lectura/escritura .kar
├── test_tracking.py          # Tests del TrackingHub
├── test_shader_compiler.py   # Tests de compilación de shaders
├── test_body_graph.py        # Tests del grafo de relaciones
├── test_runtime.py           # Tests del renderer y controller
└── fixtures/
    ├── sample_character.png  # Imagen de prueba
    ├── sample_avatar.kar     # Avatar generado de prueba
    └── expected/             # Resultados esperados
```

---

## 12. Decisiones de Diseño

### ¿Por qué un solo archivo .kar en vez de múltiples archivos?

Un solo archivo es más fácil de compartir, copiar y versionar. El usuario no
necesita preocuparse por dependencias entre archivos. El formato ZIP ofrece
compresión automática sin herramientas externas.

### ¿Por qué OpenGL y no Vulkan/Metal/DirectX?

- **Portabilidad:** OpenGL funciona en Windows, Linux y macOS sin cambios.
- **Madurez:** La implementación de OpenGL es estable y bien documentada.
- **Complejidad:** Vulkan/Metal requieren mucho más código boilerplate para el
  mismo resultado visual en un avatar 2D/2.5D.
- **Rendimiento suficiente:** Para un avatar individual con post-processing,
  OpenGL 4.5 es más que suficiente.

### ¿Por qué resortes y no simulación física real?

La simulación física real (ragdoll, soft body) es innecesaria para un avatar
VTuber. Los resortes son computacionalmente baratos, predecibles y producen
resultados visualmente convincentes para cabello, ropa y movimiento natural.
Además, se pueden precomputar y limitar a 60 actualizaciones por segundo.

### ¿Por qué Python y no C++/Rust?

El motor está diseñado como parte del ecosistema Karin VTuber que ya usa Python.
PyOpenGL ofrece acceso completo a OpenGL. Para las partes críticas de rendimiento
(el loop de física), se pueden crear módulos Cython o usar NumPy vectorizado.
El beneficio de mantener un solo lenguaje en el proyecto supera el overhead de
Python en este caso de uso específico.

---

## 13. Roadmap

### Fase 1 — Core Foundation (Semanas 1-4)
- [ ] Definir tipos base y interfaces (`core/`)
- [ ] Implementar `CharacterAnalyzer` con detección básica
- [ ] Generador de malla con Delaunay adaptativo
- [ ] Formato `.kar` v0.1 (lectura/escritura)

### Fase 2 — Esqueleto y Blend Shapes (Semanas 5-8)
- [ ] Generador de esqueleto automático
- [ ] Auto-skinning con pesos suaves
- [ ] Blend shapes faciales (ojos, boca, cejas)
- [ ] Grafo de relaciones del cuerpo

### Fase 3 — Física (Semanas 9-10)
- [ ] Motor de resortes optimizado
- [ ] Simulación de cabello
- [ ] Simulación de ropa
- [ ] Respiración automática

### Fase 4 — Runtime y Tracking (Semanas 11-14)
- [ ] Renderer OpenGL con cel shading
- [ ] Pipeline de post-processing (outline, bloom)
- [ ] TrackingHub con MediaPipe
- [ ] AvatarController con interpolación

### Fase 5 — Editor y Pulido (Semanas 15-18)
- [ ] Editor de parámetros (sliders, preview)
- [ ] Exportación y validación de `.kar`
- [ ] Optimización de rendimiento
- [ ] Tests de cobertura > 70%

---

## 14. Glossario

| Término | Definición |
|---|---|
| **Avatar** | Representación visual 3D del personaje en tiempo real |
| **Blend Shape** | Deformación predefinida de la malla (ej: cerrar ojos) |
| **Body Graph** | Grafo que representa relaciones entre partes del cuerpo |
| **Cel Shading** | Técnica de renderizado que simula iluminación de dibujos animados |
| **Delaunay** | Algoritmo de triangulación que maximiza ángulos mínimos |
| **Delta Vectors** | Diferencias de posición de vértices entre pose base y blend shape |
| **IK (Inverse Kinematics)** | Calcular ángulos de articulaciones a partir de posición final |
| **Mesh** | Superficie 3D compuesta de vértices, aristas y triángulos |
| **Pose** | Estado completo del avatar en un momento dado |
| **Rig** | Estructura de huesos y restricciones que controla la malla |
| **Runtime** | Fase de ejecución en tiempo real (sin IA) |
| **Spring** | Elemento físico que simula elasticidad con masa y amortiguación |
| **Tracking** | Detección en tiempo real de movimiento del usuario |
| **UV Mapping** | Mapeo de coordenadas 2D de textura sobre superficie 3D |

---

*Documento generado como parte del diseño de Karin Nova Engine 3D.*
*Versión del documento: 1.0.0 — 20 de julio de 2026.*
