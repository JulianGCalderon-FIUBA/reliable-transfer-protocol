from mininet.topo import Topo
from mininet.link import TCLink


HOST_AMOUNT = 2
LINK_LOSS = 10


class CustomTopo(Topo):
    def __init__(self, size, loss):
        Topo.__init__(self, size)
        server = self.addHost("server")
        switch = self.addSwitch("switch")

        self.addLink(server, switch, loss=loss)

        for i in range(1, size + 1):
            host = self.addHost(f"host_{i}")
            self.addLink(host, switch, cls=TCLink, loss=loss)


topos = {"customTopo": lambda: CustomTopo(HOST_AMOUNT, LINK_LOSS)}
