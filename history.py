'''
History class to track history of chat between clients
'''


class Record:
    def __init__(self):
        self.chatHistory = {}

    def addMessage(self, client_id, message):
        self.chatHistory[str(client_id)] = str(message)

    def removeKeyValue(self, key):
        del self.chatHistory[key]

    def replaceKeyValue(self, oldKey, newKey, newValue):
        self.removeKeyValue(oldKey)
        self.addMessage(client_id = newKey, message = newValue)

    def print(self):
        for k, v in self.chatHistory.items():
            print(k,v)



#diction = ChatHistory()

#diction.addMessage('41234', 'hello')

#diction.addMessage('465634', 'bye')

#diction.addMessage('sadfwe', 'This is a message')

#diction.print()