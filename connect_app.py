import socketio
import time

class socket_traffic(socketio.Client):

    sio = socketio.Client(reconnection=True, 
                          reconnection_attempts=5, 
                          reconnection_delay=1, 
                          reconnection_delay_max=5, 
                          randomization_factor=0.5, 
                          logger=False)

    def __init__(self):
        print("INIT Traffic SOCKET CONNECTION")
        self.call_backs()  # Make sure callbacks are set up
        self.connected()    # Connect immediately when the object is created

    def call_backs(self):
        @self.sio.event
        def connect():
            print('\nConnection established using SID', self.sio.sid)
            self.sio.emit('connect', 'connect')
            print('Connection established')

        @self.sio.event
        def disconnect():
            print('Disconnected from server')

        @self.sio.event
        def reconnect():
            print('Reconnected to server')

        @self.sio.event
        def reconnect_error(data):
            print('Reconnection error:', data)

    def disconnected(self):
        print("Disconnecting from server...")
        self.sio.disconnect()

    def connected(self):
        while not self.sio.connected:
            try:
                # Make sure the server is running at this address.
                print("Attempting to connect to server at http://localhost:5055")
                self.sio.connect('http://localhost:5055', transports=["websocket"])
            except Exception as e:
                print(f"Connection failed: {e}. Retrying in 5 seconds...")
                time.sleep(5)

# Initialize and start the connection
socket_sio_traffic = socket_traffic()
socket_sio_traffic.sio.wait()
# while(True):
#     pass