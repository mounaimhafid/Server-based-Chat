import socket
import select
import sys
import threading

# Object which represents a server
class ChatServer:
    def __init__(self):
        self.welcomingPort = 8888
        # These are the sockets that will be regulated to clients
        # UPDATE: onlineSockets holds a dictionary containing online sockets
        # This is also the valid clientIDs: 1-5 currently
        

        # Must change this line: if int(clientID) < 1 or int(clientID) > 5:
        # in connection() if we want to adjust the clientIDs
        # This line as well: for x in range(1,6)
        # A lot of other lines..... It's probably best if we don't change this
        self.onlineSockets = {'1':None, '2':None, '3':None, '4':None, '5':None,
                              '6':None, '7':None, '8':None, '9':None, '10':None}
        # Initialize dictionary of online sessions to a nonexistent session
        self.onlineSessions = {'4444'}
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_socket.bind((socket.gethostname(), self.welcomingPort))
        self.listen_socket.listen(5)
    print ('initialized')
            
    #manage data that is sent back to client
    def send(self,data,clientSocket):
        print("going to send some data")
        clientSocket.send(data.encode())
        print('Connected ACK sent')
    def receive(self, clientSocket):
        return clientSocket.recv(2048).decode()

    #acceptConnection
    def acceptConnection(self):
        clientSocket, client_address = self.listen_socket.accept()
        return clientSocket

        #share same listening socket
def initiate(server, clientSocket):
    print(clientSocket)
    acceptMessage = server.receive(clientSocket)
    print(acceptMessage)
    print('client accepted!')
    server.send('CONNECTED',clientSocket)
    return clientSocket

        
#allow client to log in
if __name__ == "__main__":
    print ('server is running')
    server = ChatServer()
    while True:
        clientSocket = server.acceptConnection()
        thread = threading.Thread(target=initiate, args=(server,clientSocket))
        thread.start()
        
