import random
import ipaddress
from scapy.all import IP, TCP, UDP, Raw, RandShort, send
import numpy as np

class TCPIPPacketGenerator:
    def __init__(self, 
                 src_ip_range=('192.168.0.0', '192.168.255.255'),
                 dst_ip_range=('10.0.0.0', '10.255.255.255'),
                 min_packet_size=64,
                 max_packet_size=1500):
        """
        Initialize packet generator with configurable parameters
        
        Args:
            src_ip_range (tuple): Range of possible source IP addresses
            dst_ip_range (tuple): Range of possible destination IP addresses
            min_packet_size (int): Minimum packet payload size
            max_packet_size (int): Maximum packet payload size
        """
        self.src_ip_range = src_ip_range
        self.dst_ip_range = dst_ip_range
        self.min_packet_size = min_packet_size
        self.max_packet_size = max_packet_size
    
    def _generate_ip(self, ip_range):
        """Generate a random IP address within specified range"""
        start_ip = ipaddress.IPv4Address(ip_range[0])
        end_ip = ipaddress.IPv4Address(ip_range[1])
        ip_int = random.randint(int(start_ip), int(end_ip))
        return str(ipaddress.IPv4Address(ip_int))
    
    def generate_tcp_packet(self, 
                             protocol='tcp', 
                             flags=None, 
                             payload_type='random'):
        """
        Generate a TCP/IP packet with configurable parameters
        
        Args:
            protocol (str): Transport layer protocol ('tcp' or 'udp')
            flags (str): TCP flags (e.g., 'S' for SYN, 'A' for ACK)
            payload_type (str): Type of payload generation
        
        Returns:
            Scapy packet object
        """
        # Generate source and destination IPs
        src_ip = self._generate_ip(self.src_ip_range)
        dst_ip = self._generate_ip(self.dst_ip_range)
        
        # Random port selection
        src_port = random.randint(1024, 65535)
        dst_port = random.randint(1, 1023)  # Common service ports
        
        # Payload generation
        payload_size = random.randint(self.min_packet_size, self.max_packet_size)
        
        if payload_type == 'random':
            payload = np.random.bytes(payload_size)
        elif payload_type == 'zero':
            payload = b'\x00' * payload_size
        elif payload_type == 'pattern':
            payload = bytes([i % 256 for i in range(payload_size)])
        else:
            payload = b''
        
        # Default TCP flags handling
        if flags is None:
            flags_options = ['', 'S', 'A', 'SA', 'F', 'R']
            flags = random.choice(flags_options)
        
        if protocol.lower() == 'tcp':
            packet = (
                IP(src=src_ip, dst=dst_ip)/
                TCP(sport=src_port, dport=dst_port, flags=flags)/
                Raw(load=payload)
            )
        elif protocol.lower() == 'udp':
            packet = (
                IP(src=src_ip, dst=dst_ip)/
                UDP(sport=src_port, dport=dst_port)/
                Raw(load=payload)
            )
        else:
            raise ValueError("Unsupported protocol. Use 'tcp' or 'udp'.")
        
        return packet
    
    def generate_packet_sequence(self, num_packets=100):
        """
        Generate a sequence of packets with variation
        
        Args:
            num_packets (int): Number of packets to generate
        
        Returns:
            List of generated packets
        """
        packets = []
        protocols = ['tcp', 'udp']
        payload_types = ['random', 'zero', 'pattern']
        
        for _ in range(num_packets):
            packet = self.generate_tcp_packet(
                protocol=random.choice(protocols),
                payload_type=random.choice(payload_types)
            )
            packets.append(packet)
        
        return packets
    
    def save_pcap(self, packets, filename='generated_packets.pcap'):
        """
        Save generated packets to a PCAP file
        
        Args:
            packets (list): List of packets to save
            filename (str): Output PCAP filename
        """
        from scapy.all import wrpcap
        wrpcap(filename, packets)
    
    def send_packets(self, packets, interface='eth0'):
        """
        Send packets on a specified network interface
        
        Args:
            packets (list): Packets to send
            interface (str): Network interface name
        """
        for packet in packets:
            send(packet, iface=interface)

# Example usage
if __name__ == '__main__':
    generator = TCPIPPacketGenerator()
    
    # Generate packet sequence
    packets = generator.generate_packet_sequence(num_packets=50)
    
    # Save to PCAP for training dataset
    generator.save_pcap(packets)
    
    # Optional: Send packets (use with caution)
    # generator.send_packets(packets)
