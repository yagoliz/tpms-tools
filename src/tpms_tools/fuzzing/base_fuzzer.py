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


@dataclass
class FuzzResult:
    """Result of a fuzz test case."""
    test_case: Dict[str, Any]
    encoded_bits: Optional[str]


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
        try:
            encoded_bits = self.encoder.encode_message(**test_case)
            return FuzzResult(
                test_case=test_case, encoded_bits=encoded_bits
            )
        except Exception as e:
            return FuzzResult(
                test_case=test_case, encoded_bits=None
            )

    def run_fuzz_campaign(self, strategy: FuzzStrategy, count: int) -> List[FuzzResult]:
        """Run a complete fuzz testing campaign."""
        results = []
        for test_case in self.generate_test_cases(strategy, count):
            result = self.run_test_case(test_case)
            results.append(result)
            self.results.append(result)
        return results
