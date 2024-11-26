import tensorflow as tf
import numpy as np
from scapy.all import rdpcap
import sklearn.model_selection
import sklearn.preprocessing

class TCPIPValidatorModel:
    def __init__(self, packet_generator, pcap_file='generated_packets.pcap'):
        """
        Initialize validator model with packet generation and training capabilities
        
        Args:
            packet_generator (TCPIPPacketGenerator): Packet generation utility
            pcap_file (str): Path to PCAP file for initial dataset
        """
        self.packet_generator = packet_generator
        self.pcap_file = pcap_file
        self.model = None
        
    def load_packets(self):
        """
        Load packets from PCAP file and extract features
        
        Returns:
            X (np.array): Feature matrix
            y (np.array): Labels
        """
        packets = rdpcap(self.pcap_file)
        
        features = []
        labels = []
        
        for packet in packets:
            # Feature extraction
            feature_vector = [
                # IP Layer Features
                int(packet[IP].src.split('.')[-1]) if packet.haslayer(IP) else 0,
                int(packet[IP].dst.split('.')[-1]) if packet.haslayer(IP) else 0,
                packet[IP].len if packet.haslayer(IP) else 0,
                
                # Transport Layer Features
                packet[TCP].sport if packet.haslayer(TCP) else 0,
                packet[TCP].dport if packet.haslayer(TCP) else 0,
                packet[TCP].flags if packet.haslayer(TCP) else 0,
                
                # Payload Features
                len(packet[Raw].load) if packet.haslayer(Raw) else 0,
                sum(packet[Raw].load) if packet.haslayer(Raw) else 0
            ]
            
            features.append(feature_vector)
            
            # Labeling strategy
            # 0: Potentially invalid/suspicious
            # 1: Valid packet
            label = self._evaluate_packet_validity(packet)
            labels.append(label)
        
        return np.array(features), np.array(labels)
    
    def _evaluate_packet_validity(self, packet):
        """
        Determine packet validity based on multiple criteria
        
        Args:
            packet (Scapy Packet): Packet to evaluate
        
        Returns:
            int: Validity label (0 or 1)
        """
        # Sophisticated packet validity checks
        checks = [
            # Valid IP range
            packet.haslayer(IP) and 
            (ipaddress.ip_address(packet[IP].src).is_private or 
             ipaddress.ip_address(packet[IP].dst).is_private),
            
            # Reasonable port numbers
            packet.haslayer(TCP) and 
            (1024 <= packet[TCP].sport <= 65535) and 
            (1 <= packet[TCP].dport <= 1023),
            
            # Valid TCP flags
            packet.haslayer(TCP) and 
            packet[TCP].flags in [0x02, 0x10, 0x12, 0x18],  # Common flag combinations
            
            # Payload sanity
            packet.haslayer(Raw) and 
            (0 < len(packet[Raw].load) <= 1500)
        ]
        
        return int(all(checks))
    
    def prepare_model(self, input_shape):
        """
        Create TensorFlow Lite compatible neural network
        
        Args:
            input_shape (tuple): Shape of input features
        """
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', input_shape=input_shape),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(1, activation='sigmoid')  # Binary classification
        ])
        
        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        self.model = model
    
    def train(self, test_size=0.2, random_state=42):
        """
        Train the TCP/IP validator model
        
        Args:
            test_size (float): Proportion of dataset for testing
            random_state (int): Reproducibility seed
        """
        X, y = self.load_packets()
        
        # Normalize features
        scaler = sklearn.preprocessing.StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = sklearn.model_selection.train_test_split(
            X_scaled, y, 
            test_size=test_size, 
            random_state=random_state
        )
        
        # Prepare model architecture
        self.prepare_model(input_shape=(X.shape[1],))
        
        # Train model
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_test, y_test),
            epochs=50,
            batch_size=32,
            verbose=1
        )
        
        return history
    
    def convert_to_tflite(self, output_file='tcp_ip_validator.tflite'):
        """
        Convert trained model to TensorFlow Lite format
        
        Args:
            output_file (str): Path for TensorFlow Lite model
        """
        converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        tflite_model = converter.convert()
        
        with open(output_file, 'wb') as f:
            f.write(tflite_model)
        
        print(f"TensorFlow Lite model saved to {output_file}")

# Example Usage
if __name__ == '__main__':
    from tcp_ip_packet_generator import TCPIPPacketGenerator
    
    # Initialize packet generator
    generator = TCPIPPacketGenerator()
    
    # Generate training packets
    packets = generator.generate_packet_sequence(num_packets=10000)
    generator.save_pcap(packets)
    
    # Initialize and train validator model
    validator = TCPIPValidatorModel(generator)
    training_history = validator.train()
    
    # Convert to TensorFlow Lite
    validator.convert_to_tflite()
