import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import String


class MiNodo(Node):
    def __init__(self):
        super().__init__('mi_nodo')
        self.publisher_ = self.create_publisher(String, 'saludo', 10)
        self.timer = self.create_timer(1.0, self.timer_callback)
        self.contador = 0

    def timer_callback(self):
        msg = String()
        msg.data = f'Hola desde ROS2, numero {self.contador}'
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publicando: "{msg.data}"')
        self.contador += 1


def main(args=None):
    rclpy.init(args=args)
    nodo = MiNodo()
    try:
        rclpy.spin(nodo)  # aquí el nodo queda "vivo", escuchando
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        nodo.destroy_node()
        rclpy.try_shutdown()
