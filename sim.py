import numpy as np
from scipy.stats import poisson
from typing import List, Tuple, Optional, Dict
import matplotlib.pyplot as plt
from scipy.linalg import block_diag

class QuantumState:
    """Enhanced quantum state representation with density matrix support"""
    def __init__(self, num_modes: int, max_photons: int = 3):
        self.num_modes = num_modes
        self.max_photons = max_photons
        self.dimension = (max_photons + 1) ** num_modes
        # Initialize pure vacuum state
        self.density_matrix = np.zeros((self.dimension, self.dimension), dtype=complex)
        self.density_matrix[0, 0] = 1.0
    
    def apply_phase_shift(self, mode: int, phase: float):
        """Apply phase shift to specified mode"""
        phase_op = self._create_phase_operator(mode, phase)
        self.density_matrix = phase_op @ self.density_matrix @ phase_op.conj().T
    
    def _create_phase_operator(self, mode: int, phase: float) -> np.ndarray:
        """Create phase shift operator for specified mode"""
        single_mode_op = np.diag([np.exp(1j * phase * n) for n in range(self.max_photons + 1)])
        ops = [np.eye(self.max_photons + 1)] * self.num_modes
        ops[mode] = single_mode_op
        return block_diag(*ops)

class PhaseShifter:
    """Implements a phase shifter"""
    def __init__(self, phase: float):
        self.phase = phase
    
    def transform(self, state: QuantumState, mode: int):
        """Apply phase shift to specified mode"""
        state.apply_phase_shift(mode, self.phase)
        return state

class NoiseChannel:
    """Models various noise processes in the circuit"""
    def __init__(self, loss_rate: float = 0.1, dephasing_rate: float = 0.05):
        self.loss_rate = loss_rate
        self.dephasing_rate = dephasing_rate
    
    def apply(self, state: QuantumState, mode: int):
        """Apply noise effects to specified mode"""
        # Implement loss
        if np.random.random() < self.loss_rate:
            # Simulate photon loss
            state.density_matrix *= (1 - self.loss_rate)
        
        # Implement dephasing
        if np.random.random() < self.dephasing_rate:
            # Add random phase noise
            random_phase = np.random.uniform(0, 2 * np.pi)
            state.apply_phase_shift(mode, random_phase)
        
        return state

class EnhancedPhotonicCircuit:
    """Enhanced photonic circuit with noise modeling and analysis capabilities"""
    def __init__(self, num_modes: int, max_photons: int = 3):
        self.num_modes = num_modes
        self.max_photons = max_photons
        self.state = QuantumState(num_modes, max_photons)
        self.noise_channel = NoiseChannel()
    
    def add_phase_shifter(self, mode: int, phase: float):
        """Add a phase shifter to the circuit"""
        shifter = PhaseShifter(phase)
        self.state = shifter.transform(self.state, mode)
        # Apply noise after component
        self.state = self.noise_channel.apply(self.state, mode)
    
    def generate_random_number(self, num_bits: int = 1) -> List[int]:
        """Generate random bits using quantum measurement"""
        random_bits = []
        for _ in range(num_bits):
            # Measure photon number in random mode
            mode = np.random.randint(0, self.num_modes)
            detector = PhotonDetector(0.9)  # 90% efficiency
            result = detector.measure(self.state, mode)
            # Convert to bit based on even/odd photon number
            random_bits.append(result % 2)
        return random_bits

    def analyze_state(self) -> Dict:
        """Analyze current quantum state"""
        analysis = {}
        
        # Calculate purity
        analysis['purity'] = np.real(np.trace(self.state.density_matrix @ self.state.density_matrix))
        
        # Calculate photon number distribution
        diag = np.real(np.diag(self.state.density_matrix))
        analysis['photon_distribution'] = diag[:self.max_photons + 1]
        
        return analysis

    def visualize_state(self):
        """Create visualization of quantum state"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        
        # Plot photon number distribution
        photon_numbers = range(self.max_photons + 1)
        probabilities = np.real(np.diag(self.state.density_matrix))
        ax1.bar(photon_numbers, probabilities[:self.max_photons + 1])
        ax1.set_xlabel('Photon Number')
        ax1.set_ylabel('Probability')
        ax1.set_title('Photon Number Distribution')
        
        # Plot density matrix
        im = ax2.imshow(np.real(self.state.density_matrix), cmap='RdBu')
        ax2.set_title('Density Matrix (Real Part)')
        plt.colorbar(im, ax=ax2)
        
        plt.tight_layout()
        return fig

def demonstrate_qrng():
    """Demonstrate quantum random number generation"""
    circuit = EnhancedPhotonicCircuit(num_modes=2)
    
    # Add single photon and create superposition
    circuit.add_phase_shifter(0, np.pi/4)
    
    # Generate random bits
    random_bits = circuit.generate_random_number(num_bits=100)
    
    # Analyze randomness
    ones_count = sum(random_bits)
    bias = abs(0.5 - ones_count/len(random_bits))
    
    return random_bits, bias

# Example usage for quantum random number generation
random_bits, bias = demonstrate_qrng()
print(f"Generated random bits: {random_bits[:10]}...")
print(f"Bias: {bias:.3f}")


class WignerFunction:
    """Implements Wigner function calculation and visualization"""
    def __init__(self, resolution: int = 50):
        self.resolution = resolution
        self.x_range = np.linspace(-5, 5, resolution)
        self.p_range = np.linspace(-5, 5, resolution)
        
    def calculate(self, state: QuantumState, mode: int) -> np.ndarray:
        """Calculate Wigner function for specified mode"""
        wigner = np.zeros((self.resolution, self.resolution))
        
        for i, x in enumerate(self.x_range):
            for j, p in enumerate(self.p_range):
                wigner[i, j] = self._wigner_point(state, mode, x, p)
        
        return wigner
    
    def _wigner_point(self, state: QuantumState, mode: int, x: float, p: float) -> float:
        """Calculate Wigner function at point (x,p)"""
        alpha = (x + 1j*p)/np.sqrt(2)
        return np.real(self._displaced_parity(state, mode, alpha))
    
    def _displaced_parity(self, state: QuantumState, mode: int, alpha: complex) -> complex:
        """Calculate displaced parity operator expectation value"""
        # Simplified implementation for demonstration
        return np.trace(state.density_matrix)

class StateTomography:
    """Implements quantum state tomography"""
    def __init__(self, num_measurements: int = 1000):
        self.num_measurements = num_measurements
    
    def reconstruct_state(self, circuit: 'EnhancedPhotonicCircuit', mode: int) -> np.ndarray:
        """Perform quantum state tomography measurements"""
        measurements = []
        phases = [0, np.pi/4, np.pi/2, 3*np.pi/4]
        
        for phase in phases:
            circuit_copy = circuit.copy()
            circuit_copy.add_phase_shifter(mode, phase)
            results = [circuit_copy.measure_mode(mode) for _ in range(self.num_measurements)]
            measurements.append(np.mean(results))
        
        return self._reconstruct_density_matrix(measurements)
    
    def _reconstruct_density_matrix(self, measurements: List[float]) -> np.ndarray:
        """Reconstruct density matrix from measurements"""
        # Simplified implementation for small Hilbert space
        dim = 2  # For single-qubit like states
        rho = np.zeros((dim, dim), dtype=complex)
        # Basic reconstruction algorithm
        rho[0,0] = (measurements[0] + measurements[2])/2
        rho[0,1] = (measurements[1] + 1j*measurements[3])/2
        rho[1,0] = rho[0,1].conjugate()
        rho[1,1] = 1 - rho[0,0]
        return rho

class RandomnessTests:
    """Implements statistical tests for random number generation"""
    @staticmethod
    def run_tests(bits: List[int]) -> Dict:
        """Run suite of randomness tests"""
        results = {}
        
        # Frequency test
        ones_count = sum(bits)
        total = len(bits)
        expected = total/2
        chi_square = (ones_count - expected)**2/expected
        results['frequency_test_pvalue'] = 1 - chi2_contingency([ones_count, total-ones_count])[1]
        
        # Runs test
        runs = 1
        for i in range(1, len(bits)):
            if bits[i] != bits[i-1]:
                runs += 1
        results['runs_test'] = runs
        
        # Serial correlation
        correlation = np.corrcoef(bits[:-1], bits[1:])[0,1]
        results['serial_correlation'] = correlation
        
        return results

class DeutschJoszaCircuit:
    """Implements Deutsch-Josza algorithm using photonic components"""
    def __init__(self, oracle_function: callable):
        self.oracle = oracle_function
        self.circuit = EnhancedPhotonicCircuit(num_modes=3)  # Input, ancilla, and output modes
    
    def run(self) -> bool:
        """Run Deutsch-Josza algorithm and return whether function is constant"""
        # Prepare input state
        self.circuit.add_phase_shifter(0, np.pi/2)  # Create superposition
        self.circuit.add_phase_shifter(1, np.pi)    # Prepare ancilla
        
        # Apply oracle
        self._apply_oracle()
        
        # Measure result
        self.circuit.add_phase_shifter(0, -np.pi/2)  # Inverse Hadamard
        result = self.circuit.measure_mode(0)
        
        return result == 0  # Returns True if function is constant
    
    def _apply_oracle(self):
        """Apply oracle transformation"""
        # Simplified implementation using phase shifts
        phase = np.pi if self.oracle(0) else 0
        self.circuit.add_phase_shifter(2, phase)

# Example usage
def demonstrate_deutsch_josza():
    """Demonstrate Deutsch-Josza algorithm with simple constant and balanced functions"""
    # Constant function (always returns 0)
    constant_oracle = lambda x: 0
    constant_circuit = DeutschJoszaCircuit(constant_oracle)
    constant_result = constant_circuit.run()
    
    # Balanced function (returns input value)
    balanced_oracle = lambda x: x
    balanced_circuit = DeutschJoszaCircuit(balanced_oracle)
    balanced_result = balanced_circuit.run()
    
    return constant_result, balanced_result

# Example quantum random number generation with analysis
def analyze_qrng(num_bits: int = 1000):
    """Generate and analyze quantum random numbers"""
    circuit = EnhancedPhotonicCircuit(num_modes=2)
    random_bits = circuit.generate_random_number(num_bits)
    
    # Analyze randomness
    tests = RandomnessTests()
    results = tests.run_tests(random_bits)
    
    # Visualize distribution
    plt.figure(figsize=(10, 4))
    plt.hist(random_bits, bins=2, density=True)
    plt.title('QRNG Bit Distribution')
    plt.xlabel('Bit Value')
    plt.ylabel('Frequency')
    
    return results

# Example state visualization
def visualize_quantum_state(circuit: EnhancedPhotonicCircuit):
    """Create comprehensive visualization of quantum state"""
    fig = plt.figure(figsize=(15, 5))
    
    # Photon number distribution
    ax1 = fig.add_subplot(131)
    circuit.visualize_state()
    
    # Wigner function
    ax2 = fig.add_subplot(132)
    wigner = WignerFunction()
    W = wigner.calculate(circuit.state, 0)
    im = ax2.imshow(W, extent=[-5, 5, -5, 5])
    ax2.set_title('Wigner Function')
    plt.colorbar(im)
    
    # State tomography results
    ax3 = fig.add_subplot(133)
    tomography = StateTomography()
    rho = tomography.reconstruct_state(circuit, 0)
    im = ax3.imshow(np.real(rho))
    ax3.set_title('Reconstructed Density Matrix')
    plt.colorbar(im)
    
    plt.tight_layout()
    return fig
