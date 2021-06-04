#This class will take care of client 
#transportation between the client and the server


import socket

#refer class to self to use own address and port number
class ChatServices:
    def __init__(self):
        #create a socket to maintain connection 
        #between client and server
        
        #create a socket through network with message as a stream
        self.clientSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

        #set a welcoming port number
        self.serverPort = 8888

        #create an address for server to use 
        self.serverAddress = socket.gethostname()

        #connect ot the network to maintain connetion
        self.clientSocket.connect((self.serverAddress,self.serverPort))



    #encode data as bytes to be sent
    print("I am on send method")
    def send(self,data):
        self.clientSocket.send(data.encode())
        return

    #decode data from server using the client socket from
    #w/2048 max bytes for sent message
    def receive(self):
        return self.clientSocket.recv(2048).decode()

    #close socket once terminated
    def close(self):
        self.clientSocket.close()
