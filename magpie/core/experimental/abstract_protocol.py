import abc

class AbstractProtocol(metaclass= abc.ABCMeta):

    #allows protocol to receive data from any tool they manipulate,
    #in an observer-like fashion
    #Each class implementing AbstractProtocol decides on how to handle the received data
    @abc.abstractmethod
    def receive(self, data):
        pass