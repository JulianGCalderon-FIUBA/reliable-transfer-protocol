import argparse
from mininet.topo import Topo
from mininet.link import TCLink

DEFAULT_HOST_AMOUNT = 1
DEFAULT_LINK_LOSS = 10


class CustomTopo(Topo):
    def __init__(self, size, loss):
        Topo.__init__(self, size)
        server = self.addHost("server")
        switch = self.addSwitch("switch")

        self.addLink(server, switch, loss=loss)

        for i in range(1, size + 1):
            host = self.addHost(f"host_{i}")
            self.addLink(host, switch, cls=TCLink, loss=loss)


parser = argparse.ArgumentParser(
    prog="Topology", description="Amount of hosts for the server topology"
)

parser.add_argument("-s", "--size", default=DEFAULT_HOST_AMOUNT, type=int, nargs=1)
parser.add_argument("-l", "--loss", default=DEFAULT_LINK_LOSS, type=int, nargs=1)
args = parser.parse_args()
size = args.size
loss = args.loss

topos = {"customTopo": (lambda: CustomTopo(size, loss))}
