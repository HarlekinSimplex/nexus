from distutils.core import setup

setup(
    name='nexus',
    version='1.0',
    packages=['nexus_server', 'nexus_server.vendor'],
    package_dir={'': 'bsbdock.nexus_context'},
    url='',
    license='',
    author='Stephan Becker',
    author_email='stephan.becker@becker-systemberatung.de',
    description='Messenger for Reticulum based Mesh Networks'
)
