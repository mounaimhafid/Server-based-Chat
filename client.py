import time
import socket
import select
import sys
import time
import re
import threading
from authenticate import *

global k_a, randno, CK_A

def GETSESSIONID(id1,id2):
    
    if int(id1) < int(id2):
        return str(id1) + '-' + str(id2)

    return str(id2) + '-' + str(id1)

class CLIENTCHAT:
    
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

def CONNECTED():

    global client
    client.send('HELLO {0}'.format(clientID))
    print('Connecting to Server...')
    message = client.receive()
    
    if message == 'CONNECTED':
        print('Client was able to connect\n')
        return True
            
    elif message == 'NOT CONNECTED' or message == 'AUTH_FAIL':
        sys.stdout.write('Client was NOT able to connect')
        sys.stdout.flush()
        return False

    elif message.startswith('CHALLENGE'):
        list = message.split()
        randno = list[1]
        k_a = list[2]
        sendResponse(randno, k_a)
        return False

    elif message == "AUTH_SUCCESS":
        # GENERATE CIPHER KEY ON CLIENT SIDE (SHOULD BE SAME AS SERVER)
        CK_A = generateKey(randno, k_a)
        print("Cipher key generated")

def sendResponse(rand, secretKey):
    RES = authenticate(rand, secretKey)
    print("Sending RESPONSE")
    client.send("RESPONSE {0}".format(RES))

#PRINTS MESSAGES RECIEVED
def MESSAGELISTENER(client,destID):
    
    global receivedEndChat, chatMode
    
    while True:
        #KEEP RECEIVING MESSAGES
        receivedMessage = client.receive()
        
        #PRINT MESSAGES TO CLIENT
        if receivedMessage != '' and 'END_NOTIF' not in receivedMessage.split()[0]:
            print('', end='\r')
            print('Client {0}: {1}'.format(destID,receivedMessage))
            print('Client {0}: '.format(clientID), end='')
            sys.stdout.flush()

#ALLOWS CLIENT TO SEND MESSAGES TO ANOTHER CLIENT
def CHATMODE(client,destID,sessionID):
    
    global chatMode, receivedEndChat

    print('', end='\r')
    sys.stdout.flush()

    messageListenThread = threading.Thread(target=MESSAGELISTENER, args=(client,destID))
    messageListenThread.start()

    print('\nEntered chat session with client ' + destID + '! Input command END CHAT to exit session.')
    while chatMode:
        messageToSend = input('Client {0}: '.format(clientID))

        if receivedEndChat == True:
            receivedEndChat = False
            break

        if messageToSend.upper().strip() == 'END CHAT'.lower().strip():
            client.send('END_REQUEST ' + sessionID)
            chatMode = False
            receivedEndChat = False  # This client caused the chat to end
            break
        
        #SEND MESSAGE TO SERVER SO THAT IT CAN BE FORWARDED TO CLIENT
        client.send('CHAT ({0},{1})'.format(sessionID,messageToSend))
        
global client, message
clientID = 0
destID = 0
receivedEndChat = None

if __name__ == '__main__':
    
    global chatMode
    global client
    waiting = False
    chatMode = False
    
    while True:
        
        #ASK FOR COMMAND
        commands = str(input('Enter a command: '))
        
        #COMMAND FOR LOGGING IN
        if commands.upper() == 'LOGIN':
            clientID = str(input('Enter your desired login ID:'))
        
        #CONNECT CLIENT TO SERVER ** THIS NEEDS INPUT VALIDATION
        client = CLIENTCHAT();        
        isConnected = CONNECTED()
        
        #IF THEY ARE CONNECTED BEGIN ASKING FOR MORE COMMANDS
        while isConnected:
            
            if waiting == False and chatMode == False:
                connectedCommand = str(input('Enter a command:'))

                #IF USER WANTS TO CHAT REQUEST
                if connectedCommand.upper() == 'CHAT REQUEST':
                    #GET DESTINATION ID AND SEND A REQUEST TO THE SERVER
                    destID = str(input('Enter the client ID you want to connect with: '))
                    client.send('CHAT-REQUEST ' + destID + ' from ' + clientID)
                    #TELL THE USER THAT THEY HAVE TO WAIT FOR RESPONSE
                    print('Wait 10 seconds for client ' + destID + ' to accept chat request.')
                    time.sleep(10)
                    print('Done waiting')
                    #GET CLIENT RESPONSE FROM SERVER
                    destClientResponse = client.receive()
                    #IF THEY APPROVE THEN SEND A RESPONSE THAT THIS CLIENT HAS READ THE APPROVED AND BEGIN CHAT MODE
                    #NEED A CASE FOR IF THE USER DECLINES
                    if destClientResponse == 'CHAT_STARTED':
                        print('Chat request approved! Chat between client ' + str(clientID) + ' (you) and client ' + str(destID) )
                        client.send('CHAT_STARTED RECV')
                        chatMode = True
                    elif destClientResponse == 'DENIED':
                        print('Chat request has been denied')
                #EXITS PROGRAM
                elif connectedCommand.upper() == 'EXIT':
                    exit()
                #WAITS FOR A RESPONSE FROM A DIFFERENT CLIENT
                elif connectedCommand.upper() == 'WAIT' or connectedCommand.upper() == 'LISTEN':
                    waiting = True
                    #SEND A WAITING MESSAGE TO SERVER
                    client.send('WAITING')
                    print('Listening for 10 seconds...')
                    time.sleep(10)
                    print('Done listening')
                    #RECIEVE ANY INCOMING CHAT REQUEST
                    msg1 = client.receive()
                    if re.match(r'CHAT-REQUESTED from [0-9]+', msg1):
                        #ASK THE USER IF THEY WANT TO ACCEPT THE CHAT REQUEST
                        #NEED A CASE FOR WHEN THEY SAY NO
                        chatReqAns = str(input(msg1 + '. Do you accept? '))
                        #IF YES. SEND AN APPROVE MESSAGE TO THE OTHER CLIENT AND BEGIN CHATMODE
                        if chatReqAns.upper() == 'YES':
                            destID = msg1[20]
                            print('Chat request approved! Chat between client ' + str(clientID) + ' (you) and client ' + str(destID))
                            client.send('ACCEPTED')
                            chatMode = True
                        elif chatReqAns.upper() == 'NO':
                            print('Chat request denied')
                            client.send('DENIED')
                    #AFTER WAITING FOR A PERIOD OF TIME STOP WAITING
                    elif msg1 == '':
                        waiting = False
                #FOR BAD COMMANDS
                else:
                    print('INVALID COMMAND. TRY AGAIN')
                
                #IF USERS CHOOSE TO CHAT BEGIN CHAT THREAD
                if chatMode == True:
                    print('Please wait for connection to client.')
                    time.sleep(5)
                    sID = GETSESSIONID(clientID, destID)
                    chatModeThread = threading.Thread(target=CHATMODE, args=(client,destID, sID))
                    chatModeThread.start()
