from mininet.topo import Topo
from mininet.link import TCLink


class CustomTopo(Topo):
    def __init__(self, size, loss):
        Topo.__init__(self)
        server = self.addHost("server")
        switch = self.addSwitch("s1")

        self.addLink(server, switch, loss=loss)

        for i in range(1, size + 1):
            host = self.addHost(f"host_{i}")
            self.addLink(host, switch, cls=TCLink, loss=loss)


topos = {"customTopo": (lambda size, loss: CustomTopo(size, loss))}
