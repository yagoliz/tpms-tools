#!/usr/bin/env python3
"""
Comprehensive fuzz testing framework for TPMS protocols.
Focuses on semantic fuzzing rather than pure bit-level randomization.
"""

import random
from typing import List, Dict, Any, Optional, Iterator

from tpms_tools.encoders.devices.renault import RenaultTPMSEncoder
from tpms_tools.fuzzing.base_fuzzer import TPMSFuzzer, FuzzStrategy


class RenaultTPMSFuzzer(TPMSFuzzer):
    """Specialized fuzzer for Renault TPMS protocol."""
    
    def __init__(self, target_sensor_ids: Optional[List[int]] = None):
        super().__init__(RenaultTPMSEncoder, target_sensor_ids)
        
        # Protocol-specific constraints (excluding sensor_id since it's fixed)
        self.valid_ranges = {
            'pressure_kpa': (0, 400),  # Reasonable tire pressure range
            'temperature_c': (-40, 125),  # Automotive temperature range
            'flags': (0, 0x3F),  # 6-bit flags
            'extra': (0, 0xFFFF),  # 16-bit unknown field
        }
    
    def _get_sensor_id(self) -> int:
        """Get a sensor ID for testing. Use target ID if specified, otherwise random."""
        if self.target_sensor_ids:
            return random.choice(self.target_sensor_ids)
        return random.randint(0x000000, 0xFFFFFF)
    
    def generate_boundary_values(self, count: int) -> Iterator[Dict[str, Any]]:
        """Generate boundary value test cases."""
        boundaries = []
        
        # Test minimum/maximum values for each field (excluding sensor_id)
        for field, (min_val, max_val) in self.valid_ranges.items():
            boundaries.extend([
                {field: min_val},
                {field: max_val},
                {field: min_val + 1},
                {field: max_val - 1},
            ])
        
        # Test zero values for non-sensor fields
        boundaries.append({field: 0 for field in self.valid_ranges.keys()})
        
        # Test maximum values for non-sensor fields
        boundaries.append({field: max_val for field, (_, max_val) in self.valid_ranges.items()})
        
        # Fill remaining count with random selections
        while len(boundaries) < count:
            boundaries.append(random.choice(boundaries))
        
        for boundary in boundaries[:count]:
            # Fill missing fields with default values, use target sensor ID
            test_case = {
                'sensor_id': self._get_sensor_id(),
                'pressure_kpa': boundary.get('pressure_kpa', 220.0),
                'temperature_c': boundary.get('temperature_c', 25),
                'flags': boundary.get('flags', 54),
                'extra': boundary.get('extra', 48153),
            }
            yield test_case
    
    def generate_random_semantic(self, count: int) -> Iterator[Dict[str, Any]]:
        """Generate semantically valid random test cases."""
        for _ in range(count):
            yield {
                'sensor_id': self._get_sensor_id(),
                'pressure_kpa': random.uniform(*self.valid_ranges['pressure_kpa']),
                'temperature_c': random.randint(*self.valid_ranges['temperature_c']),
                'flags': random.randint(*self.valid_ranges['flags']),
                'extra': random.randint(*self.valid_ranges['extra']),
            }
    
    def generate_protocol_aware(self, count: int) -> Iterator[Dict[str, Any]]:
        """Generate protocol-aware test cases targeting specific vulnerabilities."""
        test_cases = []
        
        # Test CRC collision scenarios
        for _ in range(count // 4):
            base_case = {
                'sensor_id': self._get_sensor_id(),
                'pressure_kpa': random.uniform(*self.valid_ranges['pressure_kpa']),
                'temperature_c': random.randint(*self.valid_ranges['temperature_c']),
                'flags': random.randint(*self.valid_ranges['flags']),
                'extra': random.randint(*self.valid_ranges['extra']),
            }
            test_cases.append(base_case)
        
        # Test pressure conversion edge cases (division by 0.75)
        for _ in range(count // 4):
            # Test values that might cause precision issues
            test_cases.append({
                'sensor_id': self._get_sensor_id(),
                'pressure_kpa': random.choice([0.75, 1.5, 2.25, 765.0]),  # Multiples of 0.75
                'temperature_c': random.randint(*self.valid_ranges['temperature_c']),
                'flags': random.randint(*self.valid_ranges['flags']),
                'extra': random.randint(*self.valid_ranges['extra']),
            })
        
        # Test temperature offset edge cases (+30 offset)
        for _ in range(count // 4):
            test_cases.append({
                'sensor_id': self._get_sensor_id(),
                'pressure_kpa': random.uniform(*self.valid_ranges['pressure_kpa']),
                'temperature_c': random.choice([-30, -29, 225, 226]),  # Around offset boundaries
                'flags': random.randint(*self.valid_ranges['flags']),
                'extra': random.randint(*self.valid_ranges['extra']),
            })
        
        # Test bit manipulation edge cases (focus on non-ID fields)
        for _ in range(count // 4):
            test_cases.append({
                'sensor_id': self._get_sensor_id(),
                'pressure_kpa': random.uniform(*self.valid_ranges['pressure_kpa']),
                'temperature_c': random.randint(*self.valid_ranges['temperature_c']),
                'flags': random.choice([0, 0x3F, 0x15, 0x2A]),  # Bit patterns
                'extra': random.choice([0, 0xFFFF, 0x5555, 0xAAAA]),
            })
        
        for case in test_cases[:count]:
            yield case
    
    def generate_mutation_based(self, count: int) -> Iterator[Dict[str, Any]]:
        """Generate test cases by mutating known good cases."""
        base_cases = [
            {'pressure_kpa': 220.0, 'temperature_c': 25, 'flags': 54, 'extra': 48153},
            {'pressure_kpa': 180.0, 'temperature_c': -10, 'flags': 32, 'extra': 12345},
            {'pressure_kpa': 300.0, 'temperature_c': 80, 'flags': 16, 'extra': 65535},
        ]
        
        for _ in range(count):
            base_case = random.choice(base_cases).copy()
            base_case['sensor_id'] = self._get_sensor_id()
            
            # Apply random mutations (excluding sensor_id)
            mutation_type = random.choice(['bit_flip', 'byte_add', 'byte_sub', 'field_swap'])
            mutable_fields = ['pressure_kpa', 'temperature_c', 'flags', 'extra']
            
            if mutation_type == 'bit_flip':
                field = random.choice(mutable_fields)
                if isinstance(base_case[field], int):
                    bit_pos = random.randint(0, 15)
                    base_case[field] ^= (1 << bit_pos)
            
            elif mutation_type == 'byte_add':
                field = random.choice(mutable_fields)
                base_case[field] += random.randint(1, 255)
            
            elif mutation_type == 'byte_sub':
                field = random.choice(mutable_fields)
                base_case[field] -= random.randint(1, 255)
            
            elif mutation_type == 'field_swap':
                field1, field2 = random.sample(mutable_fields, 2)
                base_case[field1], base_case[field2] = base_case[field2], base_case[field1]
            
            yield base_case
    
    def generate_edge_cases(self, count: int) -> Iterator[Dict[str, Any]]:
        """Generate edge cases specific to the protocol implementation."""
        edge_cases = []
        
        # Test Manchester encoding edge cases (focus on data fields)
        for _ in range(count // 3):
            edge_cases.append({
                'sensor_id': self._get_sensor_id(),
                'pressure_kpa': random.uniform(*self.valid_ranges['pressure_kpa']),
                'temperature_c': random.randint(*self.valid_ranges['temperature_c']),
                'flags': random.choice([0, 0x3F]),
                'extra': random.choice([0, 0xFFFF]),
            })
        
        # Test CRC polynomial edge cases
        for _ in range(count // 3):
            edge_cases.append({
                'sensor_id': self._get_sensor_id(),
                'pressure_kpa': random.uniform(*self.valid_ranges['pressure_kpa']),
                'temperature_c': random.randint(*self.valid_ranges['temperature_c']),
                'flags': random.randint(*self.valid_ranges['flags']),
                'extra': random.randint(*self.valid_ranges['extra']),
            })
        
        # Test inversion edge cases
        for _ in range(count // 3):
            edge_cases.append({
                'sensor_id': self._get_sensor_id(),
                'pressure_kpa': random.uniform(*self.valid_ranges['pressure_kpa']),
                'temperature_c': random.randint(*self.valid_ranges['temperature_c']),
                'flags': random.randint(*self.valid_ranges['flags']),
                'extra': random.randint(*self.valid_ranges['extra']),
            })
        
        for case in edge_cases[:count]:
            yield case
    
    def generate_test_cases(self, strategy: FuzzStrategy, count: int) -> Iterator[Dict[str, Any]]:
        """Generate test cases based on the specified strategy."""
        strategy_map = {
            FuzzStrategy.BOUNDARY_VALUES: self.generate_boundary_values,
            FuzzStrategy.RANDOM_SEMANTIC: self.generate_random_semantic,
            FuzzStrategy.PROTOCOL_AWARE: self.generate_protocol_aware,
            FuzzStrategy.MUTATION_BASED: self.generate_mutation_based,
            FuzzStrategy.EDGE_CASES: self.generate_edge_cases,
        }
        
        return strategy_map[strategy](count)

