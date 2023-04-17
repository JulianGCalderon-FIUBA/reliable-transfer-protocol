import argparse
from mininet.topo import Topo
from mininet.link import TCLink
from lib.constants import MIN_HOST_AMOUNT, LINK_LOSS


class Topo ( Topo ) :
    def __init__ ( self, hosts) :
        # Initialize topology
        Topo.__init__ ( self )
        server = self.addHost("server")
        for i in range(1, hosts+1):
                next_client = self.addHost('host_'+str(i+1))
                self.addLink ( server , next_client , cls = TCLink , loss = loss)


parser = argparse.ArgumentParser(
    prog="Topology",
    description="Amount of hosts for the server topology"
)
parser.add_argument("amount",default=MIN_HOST_AMOUNT, type=int, nargs=1)
parser.add_argument("-l", "--loss", default=LINK_LOSS, type=int, nargs=1)
hosts = parser.amount
loss = parser.loss

topos = {'customTopo': Topo(hosts) }
