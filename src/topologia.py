import argparse
from mininet.topo import Topo
from mininet.link import TCLink
from lib.constants import MIN_HOST_AMOUNT, LINK_LOSS


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


parser = argparse.ArgumentParser(
    prog="Topology", description="Amount of hosts for the server topology"
)
parser.add_argument(
    '-a', '--amount', default=MIN_HOST_AMOUNT, type=int, nargs=1)
args = parser.parse_args()
hosts = args.amount

topos = {"customTopo": CustomTopo(hosts)}
