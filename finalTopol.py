"""Custom topology example

Two directly connected switches plus a host for each switch:

   host --- switch --- switch --- host

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""

from mininet.topo import Topo

class MyTopo( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches
        rightHost = self.addHost( 's1' )
        leftSwitch = self.addSwitch( 'sw1' )
        rightSwitch = self.addSwitch( 'sw2' )
        leftHost1 = self.addHost( 'c1' )
        leftHost2 = self.addHost( 'c2' )
        leftHost3 = self.addHost( 'c3' )

        # Add links
        self.addLink( rightSwitch, rightHost )
        self.addLink( leftSwitch, rightSwitch )
        self.addLink( leftHost1, leftSwitch )
        self.addLink( leftHost2, leftSwitch )
        self.addLink( leftHost3, leftSwitch )

topos = { 'mytopo': ( lambda: MyTopo() ) }
