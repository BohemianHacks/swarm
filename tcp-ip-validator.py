import tensorflow as tf
import numpy as np
import ipaddress
from scapy.all import rdpcap, IP, TCP, Raw, HTTP
import sklearn.model_selection
import sklearn.preprocessing
import re
import hashlib
import logging

class TCPIPValidatorModel:
    def __init__(self, packet_generator, pcap_file='generated_packets.pcap'):
        """
        Initialize validator model with advanced feature engineering
        
        Args:
            packet_generator: Packet generation utility
            pcap_file (str): Path to PCAP file for initial dataset
        """
        self.packet_generator = packet_generator
        self.pcap_file = pcap_file
        self.model = None
        self.scaler = sklearn.preprocessing.StandardScaler()
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _extract_advanced_features(self, packet):
        """
        Extract comprehensive, protocol-aware features
        
        Args:
            packet (Scapy Packet): Packet to extract features from
        
        Returns:
            list: Advanced feature vector
        """
        features = []
        
        # IP Layer Features
        if packet.haslayer(IP):
            # IP Reputation-like Features
            try:
                src_ip = ipaddress.ip_address(packet[IP].src)
                dst_ip = ipaddress.ip_address(packet[IP].dst)
                
                # IP Type Encoding
                features.extend([
                    int(src_ip.is_private),     # Source IP type
                    int(dst_ip.is_private),     # Destination IP type
                    int(src_ip.is_loopback),    # Source is loopback
                    int(dst_ip.is_loopback)     # Destination is loopback
                ])
            except Exception:
                features.extend([0, 0, 0, 0])
        else:
            features.extend([0, 0, 0, 0])
        
        # Transport Layer Features
        if packet.haslayer(TCP):
            # Advanced TCP Feature Engineering
            features.extend([
                packet[TCP].sport,              # Source Port
                packet[TCP].dport,              # Destination Port
                packet[TCP].flags,              # TCP Flags
                int(packet[TCP].seq),           # Sequence Number
                int(packet[TCP].ack)            # Acknowledgement Number
            ])
        else:
            features.extend([0, 0, 0, 0, 0])
        
        # Payload Features with Protocol Insights
        if packet.haslayer(Raw):
            payload = packet[Raw].load
            payload_str = payload.decode('utf-8', errors='ignore')
            
            # HTTP-Specific Feature Engineering
            http_methods = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'OPTIONS']
            http_method_present = any(method in payload_str for method in http_methods)
            
            features.extend([
                len(payload),                   # Payload Length
                sum(payload),                   # Payload Checksum
                int(http_method_present),       # HTTP Method Presence
                
                # Entropy as feature for anomaly detection
                self._calculate_entropy(payload),
                
                # Payload pattern matching
                int(bool(re.search(r'HTTP/\d\.\d', payload_str))),  # HTTP Version Presence
                int(bool(re.search(r'Host:', payload_str))),        # Host Header Presence
            ])
        else:
            features.extend([0, 0, 0, 0, 0, 0])
        
        return features
    
    def _calculate_entropy(self, payload):
        """
        Calculate payload entropy as anomaly detection feature
        
        Args:
            payload (bytes): Raw packet payload
        
        Returns:
            float: Entropy value
        """
        try:
            # Count byte frequencies
            byte_counts = {}
            for byte in payload:
                byte_counts[byte] = byte_counts.get(byte, 0) + 1
            
            # Calculate entropy
            total_bytes = len(payload)
            entropy = 0
            for count in byte_counts.values():
                prob = count / total_bytes
                entropy -= prob * np.log2(prob)
            
            return entropy
        except Exception:
            return 0
    
    def load_packets(self, max_packets=None):
        """
        Load packets and extract advanced features
        
        Args:
            max_packets (int, optional): Limit number of packets processed
        
        Returns:
            X (np.array): Feature matrix
            y (np.array): Labels
        """
        try:
            packets = rdpcap(self.pcap_file)
            
            if max_packets:
                packets = packets[:max_packets]
            
            # Feature matrix and labels
            X = []
            y = []
            
            for packet in packets:
                # Basic validation
                if packet.haslayer(IP) and packet.haslayer(TCP):
                    features = self._extract_advanced_features(packet)
                    X.append(features)
                    
                    # Simple validation: consider packets with clear protocol markers as valid
                    label = int(packet.haslayer(HTTP) or 
                                any(method.encode() in packet[Raw].load for method in ['GET', 'POST']))
                    y.append(label)
            
            return np.array(X), np.array(y)
        
        except Exception as e:
            self.logger.error(f"Packet loading error: {e}")
            raise
    
    def prepare_model(self, input_shape):
        """
        Create neural network with focus on feature importance
        
        Args:
            input_shape (tuple): Shape of input features
        """
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', input_shape=input_shape),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        self.model = model
    
    def train(self, test_size=0.2, random_state=42):
        """
        Train the model with stratified sampling
        
        Args:
            test_size (float): Proportion of dataset for testing
            random_state (int): Reproducibility seed
        """
        X, y = self.load_packets()
        
        # Normalize features
        X_scaled = self.scaler.fit_transform(X)
        
        # Stratified split
        X_train, X_test, y_train, y_test = sklearn.model_selection.train_test_split(
            X_scaled, y, 
            test_size=test_size, 
            random_state=random_state,
            stratify=y
        )
        
        # Prepare model architecture
        self.prepare_model(input_shape=(X.shape[1],))
        
        # Train with early stopping
        early_stop = tf.keras.callbacks.EarlyStopping(
            monitor='val_loss', 
            patience=10, 
            restore_best_weights=True
        )
        
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_test, y_test),
            epochs=50,
            batch_size=64,
            callbacks=[early_stop],
            verbose=1
        )
        
        return history
    
    def convert_to_tflite(self, output_file='tcp_ip_validator.tflite'):
        """
        Convert to TensorFlow Lite with quantization
        
        Args:
            output_file (str): Path for TensorFlow Lite model
        """
        converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.target_spec.supported_types = [tf.float16]
        
        try:
            tflite_model = converter.convert()
            
            with open(output_file, 'wb') as f:
                f.write(tflite_model)
            
            self.logger.info(f"TensorFlow Lite model saved to {output_file}")
        
        except Exception as e:
            self.logger.error(f"TensorFlow Lite conversion failed: {e}")
