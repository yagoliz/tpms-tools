from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Iterator


class FuzzStrategy(Enum):
    """Different fuzzing strategies to employ."""

    BOUNDARY_VALUES = "boundary"
    RANDOM_SEMANTIC = "random_semantic"
    PROTOCOL_AWARE = "protocol_aware"
    MUTATION_BASED = "mutation_based"
    EDGE_CASES = "edge_cases"
    PACKET_LENGTH_FUZZING = "packet_length"


@dataclass
class FuzzResult:
    """Result of a fuzz test case."""
    test_case: Dict[str, Any]
    encoded_bits: Optional[str]
    packet_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TPMSFuzzer(ABC):
    """Base class for TPMS protocol fuzzers."""

    def __init__(self, encoder_class, target_sensor_ids: Optional[List[int]] = None):
        self.encoder = encoder_class()
        self.target_sensor_ids = target_sensor_ids or []
        self.results: List[FuzzResult] = []

    @abstractmethod
    def generate_test_cases(
        self, strategy: FuzzStrategy, count: int
    ) -> Iterator[Dict[str, Any]]:
        """Generate test cases based on the specified strategy."""
        pass

    def run_test_case(self, test_case: Dict[str, Any]) -> FuzzResult:
        """Execute a single test case and return result."""
        # Make a copy to avoid modifying the original
        test_case_copy = test_case.copy()
        
        try:
            # Extract packet length fuzzing parameters if present
            fuzzing_params = {}
            if 'target_length' in test_case_copy:
                fuzzing_params['target_length'] = test_case_copy.pop('target_length')
            if 'padding_method' in test_case_copy:
                fuzzing_params['padding_method'] = test_case_copy.pop('padding_method')
            if 'padding_data' in test_case_copy:
                fuzzing_params['padding_data'] = test_case_copy.pop('padding_data')
            
            # Try to encode with packet length parameters if supported
            if fuzzing_params and hasattr(self.encoder, 'encode_message_with_length'):
                encoded_bits = self.encoder.encode_message_with_length(**test_case_copy, **fuzzing_params)
            else:
                encoded_bits = self.encoder.encode_message(**test_case_copy)
            
            # Get packet info if encoder supports it
            packet_info = None
            if encoded_bits:
                if hasattr(self.encoder, 'get_packet_length_info'):
                    try:
                        packet_info = self.encoder.get_packet_length_info(encoded_bits)
                    except Exception as e:
                        # If encoder doesn't support packet info, calculate basic info
                        packet_info = {
                            'length': len(encoded_bits),
                            'duration': len(encoded_bits) * getattr(self.encoder, 'BIT_DURATION', 50) / 1000.0,
                            'error': f"Packet info calculation failed: {str(e)}"
                        }
                else:
                    # Calculate basic packet info for encoders without support
                    packet_info = {
                        'length': len(encoded_bits),
                        'duration': len(encoded_bits) * getattr(self.encoder, 'BIT_DURATION', 50) / 1000.0
                    }
            
            return FuzzResult(
                test_case=test_case,  # Return original test case with all parameters
                encoded_bits=encoded_bits,
                packet_info=packet_info
            )
        except Exception as e:
            return FuzzResult(
                test_case=test_case,  # Return original test case with all parameters
                encoded_bits=None,
                error=str(e)
            )

    def run_fuzz_campaign(self, strategy: FuzzStrategy, count: int) -> List[FuzzResult]:
        """Run a complete fuzz testing campaign."""
        results = []
        for test_case in self.generate_test_cases(strategy, count):
            result = self.run_test_case(test_case)
            results.append(result)
            self.results.append(result)
        return results
