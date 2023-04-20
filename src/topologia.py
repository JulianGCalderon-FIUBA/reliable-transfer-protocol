import argparse
from mininet.topo import Topo
from mininet.link import TCLink
from lib.constants import MIN_HOST_AMOUNT, LINK_LOSS


class Topo(Topo):
    def __init__(self, hosts):
        # Initialize topology
        Topo.__init__(self)
        server = self.addHost("server")
        switch = net.addSwitch("s1")

        self.addLink(server, switch, loss=LINK_LOSS)

        for i in range(1, hosts + 1):
            host = self.addHost("host_" + str(i))
            self.addLink(server, switch, cls=TCLink, loss=LINK_LOSS)


parser = argparse.ArgumentParser(
    prog="Topology", description="Amount of hosts for the server topology"
)
parser.add_argument("amount", default=MIN_HOST_AMOUNT, type=int, nargs=1)
hosts = parser.amount

topos = {"customTopo": Topo(hosts)}
