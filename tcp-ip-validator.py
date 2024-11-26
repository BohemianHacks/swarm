import tensorflow as tf
import numpy as np
import ipaddress
import logging
from typing import List, Tuple, Optional

class TCPIPPacketValidator:
    """
    Robust TCP/IP packet validation system with machine learning classification
    """
    
    def __init__(self, 
                 feature_config: Optional[dict] = None, 
                 log_level: int = logging.INFO):
        """
        Initialize validator with configurable feature extraction
        
        Args:
            feature_config (dict, optional): Custom feature extraction configuration
            log_level (int): Logging verbosity level
        """
        # Logging setup
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Default feature configuration
        self.feature_config = feature_config or {
            'ip_features': ['type', 'network'],
            'tcp_features': ['ports', 'flags'],
            'payload_features': ['length', 'entropy']
        }
        
        # Model and preprocessing components
        self.model = None
        self.feature_scaler = None
    
    def extract_features(self, packet: dict) -> List[float]:
        """
        Extract standardized features from packet dictionary
        
        Args:
            packet (dict): Preprocessed packet data
        
        Returns:
            List[float]: Extracted features
        """
        features = []
        
        try:
            # IP Feature Extraction
            if 'type' in self.feature_config['ip_features']:
                features.extend([
                    float(packet.get('ip_src_private', 0)),
                    float(packet.get('ip_dst_private', 0))
                ])
            
            if 'network' in self.feature_config['ip_features']:
                # Network-level indicators
                features.extend([
                    float(packet.get('ip_src_network_score', 0)),
                    float(packet.get('ip_dst_network_score', 0))
                ])
            
            # TCP Feature Extraction
            if 'ports' in self.feature_config['tcp_features']:
                features.extend([
                    float(packet.get('tcp_sport', 0)),
                    float(packet.get('tcp_dport', 0))
                ])
            
            if 'flags' in self.feature_config['tcp_features']:
                features.append(float(packet.get('tcp_flags', 0)))
            
            # Payload Feature Extraction
            if 'length' in self.feature_config['payload_features']:
                features.append(float(packet.get('payload_length', 0)))
            
            if 'entropy' in self.feature_config['payload_features']:
                features.append(float(packet.get('payload_entropy', 0)))
        
        except Exception as e:
            self.logger.error(f"Feature extraction error: {e}")
            return [0.0] * 8  # Consistent default return
        
        return features
    
    def preprocess_data(self, packets: List[dict]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Preprocess packet data for model training/inference
        
        Args:
            packets (List[dict]): List of preprocessed packet dictionaries
        
        Returns:
            Tuple of feature matrix and labels
        """
        try:
            # Extract features
            X = np.array([self.extract_features(packet) for packet in packets])
            
            # Generate labels (simplified validation)
            y = np.array([
                1 if (
                    packet.get('tcp_sport', 0) > 1024 and 
                    packet.get('tcp_dport', 0) < 1024 and 
                    packet.get('payload_length', 0) > 0
                ) else 0 
                for packet in packets
            ])
            
            return X, y
        
        except Exception as e:
            self.logger.error(f"Data preprocessing error: {e}")
            raise
    
    def create_model(self, input_shape: Tuple[int]) -> tf.keras.Model:
        """
        Create standardized neural network model
        
        Args:
            input_shape (Tuple[int]): Shape of input features
        
        Returns:
            Compiled TensorFlow model
        """
        model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=input_shape),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train(self, 
              training_data: List[dict], 
              validation_split: float = 0.2,
              epochs: int = 50) -> dict:
        """
        Train packet validation model
        
        Args:
            training_data (List[dict]): Preprocessed packet data
            validation_split (float): Proportion of data for validation
            epochs (int): Number of training epochs
        
        Returns:
            Training history dictionary
        """
        try:
            # Preprocess data
            X, y = self.preprocess_data(training_data)
            
            # Normalize features
            self.feature_scaler = tf.keras.preprocessing.sequence.pad_sequences(
                X, padding='post', dtype='float32'
            )
            
            # Create and train model
            self.model = self.create_model(input_shape=(X.shape[1],))
            
            history = self.model.fit(
                X, y,
                validation_split=validation_split,
                epochs=epochs,
                callbacks=[
                    tf.keras.callbacks.EarlyStopping(
                        monitor='val_loss', 
                        patience=5, 
                        restore_best_weights=True
                    )
                ]
            )
            
            return history.history
        
        except Exception as e:
            self.logger.error(f"Model training failed: {e}")
            raise
    
    def evaluate(self, test_data: List[dict]) -> dict:
        """
        Evaluate model performance
        
        Args:
            test_data (List[dict]): Test packet data
        
        Returns:
            Evaluation metrics
        """
        if self.model is None:
            raise ValueError("Model must be trained before evaluation")
        
        try:
            X_test, y_test = self.preprocess_data(test_data)
            
            evaluation = self.model.evaluate(X_test, y_test, verbose=0)
            
            return {
                'loss': evaluation[0],
                'accuracy': evaluation[1]
            }
        
        except Exception as e:
            self.logger.error(f"Model evaluation failed: {e}")
            raise
    
    def predict(self, packets: List[dict]) -> np.ndarray:
        """
        Predict packet validity
        
        Args:
            packets (List[dict]): Packets to validate
        
        Returns:
            Numpy array of predictions (0 or 1)
        """
        if self.model is None:
            raise ValueError("Model must be trained before prediction")
        
        try:
            X, _ = self.preprocess_data(packets)
            predictions = self.model.predict(X)
            return (predictions > 0.5).astype(int).flatten()
        
        except Exception as e:
            self.logger.error(f"Prediction failed: {e}")
            raise
