from mininet.topo import Topo
from mininet.link import TCLink


HOST_AMOUNT = 2
LINK_LOSS = 10


class CustomTopo(Topo):
    def __init__(self, hosts):
        # Initialize topology
        Topo.__init__(self, hosts)
        server = self.addHost("server")
        switch = self.addSwitch("s1")

        self.addLink(server, switch, loss=LINK_LOSS)

        for i in range(0, hosts):
            host = self.addHost("host_" + str(i+1))
            self.addLink(host, switch, cls=TCLink, loss=LINK_LOSS)


topos = {"customTopo": lambda: CustomTopo(HOST_AMOUNT)}
