# mi_primer_paquete — Práctica P1

Práctica P1 individual de **Arquitecturas Software para Robótica** (Tema 1).
Autor: **Joel Cardenas** · ROS 2 Jazzy · Ubuntu 24.04 (WSL2)

Sistema de dos nodos en un único paquete `ament_python`. Parte del publicador `/saludo` de la
Práctica Guiada de la Sesión 3 (`mi_nodo`) y lo amplía con un segundo nodo, `contador_nodo`:

```
mi_nodo --/saludo (String)--> contador_nodo --/contador (Int32, RELIABLE + TRANSIENT_LOCAL)-->
                                   ^  servicio  /reiniciar_contador (std_srvs/Trigger)
                                   ^  parámetro umbral (entero, por defecto 10)
```

| Requisito | Dónde se cumple | Evidencia |
|---|---|---|
| R1 · Paquete compilable, nodos en `entry_points` | `setup.py` | `evidencias/01_build_ejecutables.txt` |
| R2 · `/saludo` + contador que publica `/contador` (Int32) | `mi_nodo.py`, `ContadorNodo.cb_saludo` | `02_nodos_topics.txt`, `03_echo_contador.txt` |
| R3 · Servicio `reiniciar_contador` (Trigger) | `ContadorNodo.cb_reiniciar` | `04_servicio.txt` |
| R4 · Parámetro `umbral` con WARN, cambiable en caliente | `ContadorNodo.comprobar_umbral`, `cb_parametros` | `05_parametro.txt` |
| R5 · QoS RELIABLE + TRANSIENT_LOCAL, depth 10, suscriptor tardío | `qos_contador` en `ContadorNodo.__init__` | `06_suscriptor_tardio.txt`, `07_topic_info_qos.txt` |

## Requisitos previos

- Ubuntu 24.04 (nativo o WSL2) con ROS 2 Jazzy: `sudo apt install ros-jazzy-desktop`
- colcon: `sudo apt install python3-colcon-common-extensions`
- Paquetes de ROS usados: `rclpy`, `std_msgs`, `std_srvs`, `rcl_interfaces` (incluidos en `ros-jazzy-desktop`)

## Compilación

```bash
source /opt/ros/jazzy/setup.bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone https://github.com/Jasov/mi_primer_paquete.git
cd ~/ros2_ws
colcon build --packages-select mi_primer_paquete
source install/setup.bash
ros2 pkg executables mi_primer_paquete
```

Salida esperada del último comando:

```
mi_primer_paquete contador_nodo
mi_primer_paquete mi_nodo
```

También se puede descomprimir el ZIP de la entrega dentro de `~/ros2_ws` (crea `src/mi_primer_paquete`)
y compilar igual.

> En **cada terminal nueva** hay que hacer `source /opt/ros/jazzy/setup.bash` y
> `source ~/ros2_ws/install/setup.bash`. Sin el segundo, `ros2 run` responde
> `Package 'mi_primer_paquete' not found`.

## Ejecución

```bash
# Terminal 1
ros2 run mi_primer_paquete mi_nodo

# Terminal 2
ros2 run mi_primer_paquete contador_nodo
# o con otro umbral desde el arranque:
ros2 run mi_primer_paquete contador_nodo --ros-args -p umbral:=5
```

## Qué hace cada nodo

### `mi_nodo` (Práctica Guiada, Sesión 3)

Publica cada segundo un `std_msgs/msg/String` en `/saludo` con el texto
`"Hola desde ROS2, numero N"`, donde N es un contador que empieza en 0.

### `contador_nodo`

| Interfaz | Nombre | Tipo | Función |
|---|---|---|---|
| Suscripción | `/saludo` | `std_msgs/msg/String` | Cada mensaje recibido suma 1 al contador |
| Publicación | `/contador` | `std_msgs/msg/Int32` | Total de mensajes recibidos; QoS RELIABLE + TRANSIENT_LOCAL + KEEP_LAST(10) |
| Servicio | `/reiniciar_contador` | `std_srvs/srv/Trigger` | Pone el contador a 0 y responde `success=True` y un mensaje |
| Parámetro | `umbral` | entero (por defecto 10, mayor que 0) | Al alcanzarlo se escribe un `WARN` en el log |

## Pruebas

Con los dos nodos en marcha, en otra terminal:

```bash
ros2 node list                                   # /contador_nodo  /mi_nodo
ros2 topic list -t                               # /contador [Int32]  /saludo [String]
ros2 topic echo /contador                        # data: N, aumentando cada segundo
ros2 service call /reiniciar_contador std_srvs/srv/Trigger
ros2 param get /contador_nodo umbral             # Integer value is: 10
ros2 param set /contador_nodo umbral 5           # Set parameter successful (WARN al llegar a 5)
ros2 param set /contador_nodo umbral -1          # rechazado: debe ser mayor que 0

# Suscriptor tardío (parar antes mi_nodo con Ctrl+C):
ros2 topic echo /contador --qos-durability transient_local --qos-reliability reliable
ros2 topic echo /contador --qos-durability volatile --qos-reliability reliable   # no recibe nada
ros2 topic info /contador --verbose              # RELIABLE + TRANSIENT_LOCAL
```

 

## Decisiones de diseño

- **Un nodo, una responsabilidad.** `mi_nodo` solo genera saludos (es el de la Sesión 3, sin cambios
  funcionales); toda la lógica de conteo (topic, servicio y parámetro) está en `contador_nodo`.
- **El umbral se lee en cada mensaje** con `get_parameter('umbral')`, dentro del callback, para que
  `ros2 param set` tenga efecto inmediato sin reiniciar el nodo.
- **Validación del parámetro** con `add_on_set_parameters_callback`: se rechazan umbrales menores que 1.
  El tipo entero lo garantiza ROS 2 al declarar el parámetro con el valor `10`, así que un texto o un
  decimal también se rechazan.
- **El WARN se emite una sola vez** al alcanzar el umbral, para no llenar el log. El aviso se rearma
  al reiniciar el contador o al cambiar el umbral. Se compara con `>=` para que también avise si se
  baja el umbral por debajo del valor actual.
- **Se publica el valor al arrancar (0) y tras cada reinicio**, para que un suscriptor tardío reciba
  siempre el estado actual, aunque todavía no haya llegado ningún saludo.
- **QoS de `/contador`: RELIABLE + TRANSIENT_LOCAL, depth 10.** Es un dato de estado: no debe perderse,
  y quien se conecta tarde necesita conocer el último valor sin esperar al siguiente cambio.
- **Cierre limpio:** `main()` captura `KeyboardInterrupt` y `ExternalShutdownException`, de modo que
  Ctrl+C para los nodos sin mostrar trazas de error.
- **Método `publicar_contador()`:** la publicación del total se hace en un único sitio, porque se usa
  al recibir un saludo, al reiniciar y al arrancar.

## Estructura del paquete

```
mi_primer_paquete/
├── package.xml                 # metadatos y dependencias
├── setup.py                    # instalación y entry_points (mi_nodo, contador_nodo)
├── setup.cfg
├── resource/mi_primer_paquete  # marcador del índice de ament
├── mi_primer_paquete/
│   ├── __init__.py
│   ├── mi_nodo.py              # publicador /saludo (Sesión 3)
│   └── contador_nodo.py        # suscriptor, contador, servicio y parámetro
├── test/                       # pruebas de estilo generadas por ros2 pkg create
├── evidencias/                 # salidas de las pruebas
└── README.md
```

## Evidencias

Todas están en [`evidencias/`](evidencias/) :

| Archivo | Qué demuestra |
|---|---|
| `01_build_ejecutables.txt` | R1: `colcon build` sin errores y `ros2 pkg executables` con los dos nodos |
| `02_nodos_topics.txt` | R2: `ros2 node list` y `ros2 topic list -t` |
| `03_echo_contador.txt` | R2: `ros2 topic echo` de `/saludo` y `/contador` |
| `04_servicio.txt` | R3: `ros2 service call /reiniciar_contador` y el reinicio en el log |
| `05_parametro.txt` | R4: `ros2 param get/set`, validación y los WARN en el log |
| `06_suscriptor_tardio.txt` | R5: suscriptor tardío TRANSIENT_LOCAL frente a VOLATILE |
| `07_topic_info_qos.txt` | R5: `ros2 topic info /contador --verbose` |
| `08_rqt_graph.png` | Grafo del sistema con `rqt_graph` |
| `09_M1_sin_spin.txt` | Memoria M1: programa sin `rclpy.spin()` |
| `10_M3_tipo_incorrecto.txt` | Memoria M3: suscriptor que espera `Float32` |
| `11_M4_errores.txt` | Memoria M4: `No executable found` frente a un fallo de comunicación |
| `12_colcon_test.txt` | Pruebas de estilo (flake8, pep257) con `colcon test`, si están instaladas las herramientas ament |
| `log_*.txt` | Log completo de los nodos durante las pruebas |

![Grafo del sistema](evidencias/08_rqt_graph.png)

## Documentación adicional de la entrega

- Memoria (M1–M4): `P1_Memoria_Cardenas_Joel.pdf`
- Extensión opcional C (matriz de decisión ponderada): `P1_ExtensionC_Cardenas_Joel.pdf`
