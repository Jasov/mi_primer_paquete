from setuptools import find_packages, setup

package_name = 'mi_primer_paquete'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Joel Cardenas',
    maintainer_email='jaasovjoee@gmail.com',
    description='Práctica P1: publicador /saludo y nodo contador con servicio, parámetro y QoS',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'mi_nodo = mi_primer_paquete.mi_nodo:main',
            'contador_nodo = mi_primer_paquete.contador_nodo:main',
        ],
    },
)
