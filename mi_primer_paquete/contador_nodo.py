"""Nodo contador_nodo: cuenta los mensajes de /saludo y publica el total en /contador."""

from rcl_interfaces.msg import SetParametersResult
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import Int32, String
from std_srvs.srv import Trigger


class ContadorNodo(Node):

    def __init__(self):
        super().__init__('contador_nodo')
        self.contador = 0
        self.aviso_emitido = False

        # R4: parámetro umbral (entero, valor por defecto 10)
        self.declare_parameter('umbral', 10)
        self.add_on_set_parameters_callback(self.cb_parametros)

        # R5: QoS del publicador de /contador
        qos_contador = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL)

        # R2: publicador de /contador y suscriptor de /saludo
        self.pub_contador = self.create_publisher(Int32, 'contador', qos_contador)
        self.sub_saludo = self.create_subscription(String, 'saludo', self.cb_saludo, 10)

        # R3: servicio para reiniciar el contador
        self.srv_reiniciar = self.create_service(
            Trigger, 'reiniciar_contador', self.cb_reiniciar)

        self.publicar_contador()
        self.get_logger().info('contador_nodo listo')

    def cb_saludo(self, msg):
        self.contador += 1
        self.publicar_contador()
        self.get_logger().info(f'Recibido "{msg.data}" -> contador = {self.contador}')
        self.comprobar_umbral()

    def cb_reiniciar(self, request, response):
        valor_anterior = self.contador
        self.contador = 0
        self.aviso_emitido = False
        self.publicar_contador()
        response.success = True
        response.message = f'Contador reiniciado a 0 (valor anterior: {valor_anterior})'
        self.get_logger().info(response.message)
        return response

    def cb_parametros(self, parametros):
        for parametro in parametros:
            if parametro.name == 'umbral':
                if parametro.value < 1:
                    return SetParametersResult(
                        successful=False, reason='umbral debe ser un entero mayor que 0')
                self.aviso_emitido = False
                self.get_logger().info(f'umbral cambiado en caliente a {parametro.value}')
        return SetParametersResult(successful=True)

    def comprobar_umbral(self):
        umbral = self.get_parameter('umbral').value
        if self.contador >= umbral and not self.aviso_emitido:
            self.get_logger().warn(
                f'Contador = {self.contador}: se ha alcanzado el umbral ({umbral})')
            self.aviso_emitido = True

    def publicar_contador(self):
        msg = Int32()
        msg.data = self.contador
        self.pub_contador.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    nodo = ContadorNodo()
    try:
        rclpy.spin(nodo)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        nodo.destroy_node()
        rclpy.try_shutdown()
