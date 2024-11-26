import tensorflow as tf
import numpy as np
import ipaddress
from scapy.all import rdpcap, IP, TCP, Raw
import sklearn.model_selection
import sklearn.preprocessing
import logging

class TCPIPValidatorModel:
    def __init__(self, packet_generator, pcap_file='generated_packets.pcap'):
        """
        Initialize validator model with packet generation and training capabilities
        
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
    
    def load_packets(self, max_packets=None):
        """
        Load packets from PCAP file and extract features with robust error handling
        
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
            
            features = []
            labels = []
            
            for packet in packets:
                try:
                    # Robust feature extraction with default values
                    feature_vector = self._extract_packet_features(packet)
                    features.append(feature_vector)
                    
                    # Labeling strategy with more nuanced evaluation
                    label = self._evaluate_packet_validity(packet)
                    labels.append(label)
                
                except Exception as e:
                    self.logger.warning(f"Skipping packet due to error: {e}")
            
            return np.array(features), np.array(labels)
        
        except FileNotFoundError:
            self.logger.error(f"PCAP file not found: {self.pcap_file}")
            raise
    
    def _extract_packet_features(self, packet):
        """
        Extract robust features from packet with safe defaults
        
        Args:
            packet (Scapy Packet): Packet to extract features from
        
        Returns:
            list: Feature vector
        """
        # Safe attribute extraction with default values
        ip_src_last_octet = int(packet[IP].src.split('.')[-1]) if packet.haslayer(IP) else 0
        ip_dst_last_octet = int(packet[IP].dst.split('.')[-1]) if packet.haslayer(IP) else 0
        ip_len = packet[IP].len if packet.haslayer(IP) else 0
        
        tcp_sport = packet[TCP].sport if packet.haslayer(TCP) else 0
        tcp_dport = packet[TCP].dport if packet.haslayer(TCP) else 0
        tcp_flags = packet[TCP].flags if packet.haslayer(TCP) else 0
        
        payload_len = len(packet[Raw].load) if packet.haslayer(Raw) else 0
        payload_sum = sum(packet[Raw].load) if packet.haslayer(Raw) else 0
        
        return [
            ip_src_last_octet,
            ip_dst_last_octet,
            ip_len,
            tcp_sport,
            tcp_dport,
            tcp_flags,
            payload_len,
            payload_sum
        ]
    
    def _evaluate_packet_validity(self, packet):
        """
        Determine packet validity with comprehensive checks
        
        Args:
            packet (Scapy Packet): Packet to evaluate
        
        Returns:
            int: Validity label (0 or 1)
        """
        try:
            checks = [
                # Valid IP range check
                packet.haslayer(IP) and all([
                    ipaddress.ip_address(packet[IP].src).is_private,
                    ipaddress.ip_address(packet[IP].dst).is_private
                ]),
                
                # Reasonable port numbers
                packet.haslayer(TCP) and (
                    1024 <= packet[TCP].sport <= 65535 and 
                    1 <= packet[TCP].dport <= 1023
                ),
                
                # Valid TCP flags
                packet.haslayer(TCP) and 
                packet[TCP].flags in [0x02, 0x10, 0x12, 0x18],
                
                # Payload sanity check
                packet.haslayer(Raw) and 
                (0 < len(packet[Raw].load) <= 1500)
            ]
            
            return int(all(checks))
        
        except Exception as e:
            self.logger.warning(f"Validity evaluation error: {e}")
            return 0  # Conservative default
    
    def prepare_model(self, input_shape):
        """
        Create TensorFlow neural network with flexible architecture
        
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
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', tf.keras.metrics.Precision(), tf.keras.metrics.Recall()]
        )
        
        self.model = model
        self.logger.info("Model architecture prepared successfully")
    
    def train(self, test_size=0.2, random_state=42, max_packets=10000):
        """
        Train the TCP/IP validator model with improved training strategy
        
        Args:
            test_size (float): Proportion of dataset for testing
            random_state (int): Reproducibility seed
            max_packets (int): Maximum number of packets to process
        """
        X, y = self.load_packets(max_packets)
        
        # Normalize features
        X_scaled = self.scaler.fit_transform(X)
        
        # Stratified split to maintain label distribution
        X_train, X_test, y_train, y_test = sklearn.model_selection.train_test_split(
            X_scaled, y, 
            test_size=test_size, 
            random_state=random_state,
            stratify=y
        )
        
        # Prepare model architecture
        self.prepare_model(input_shape=(X.shape[1],))
        
        # Early stopping and model checkpointing
        early_stop = tf.keras.callbacks.EarlyStopping(
            monitor='val_loss', 
            patience=10, 
            restore_best_weights=True
        )
        
        # Train model
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_test, y_test),
            epochs=100,
            batch_size=64,
            callbacks=[early_stop],
            verbose=1
        )
        
        return history
    
    def convert_to_tflite(self, output_file='tcp_ip_validator.tflite'):
        """
        Convert trained model to TensorFlow Lite format with quantization
        
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
