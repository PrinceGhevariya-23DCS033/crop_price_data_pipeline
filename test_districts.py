"""
Test District Normalization
Gujarat Crop Price Forecasting System

Tests the district name normalization and coordinate mapping.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import DISTRICT_COORDS, normalize_district_name


def test_district_normalization():
    """Test district name normalization."""
    
    print("=" * 70)
    print("District Name Normalization Test")
    print("=" * 70)
    
    # Test cases from your merge notebook
    test_cases = [
        ("Ahmedabad", "Ahmadabad"),
        ("ahmedabad", "Ahmadabad"),
        ("Ahmadabad", "Ahmadabad"),
        ("Vadodara", "Vadodara"),
        ("Vadodara (Baroda)", "Vadodara"),
        ("vadodarabaroda", "Vadodara"),
        ("The Dangs", "TheDangs"),
        ("thedangs", "TheDangs"),
        ("Gir Somnath", "GirSomnath"),
        ("girsomnath", "GirSomnath"),
        ("Devbhumi Dwarka", "DevbhumiDwarka"),
        ("devbhumidwarka", "DevbhumiDwarka"),
        ("Chhota Udaipur", "ChhotaUdaipur"),
        ("chhotaudaipur", "ChhotaUdaipur"),
        ("BanasKantha", "BanasKantha"),
        ("banaskanth", "BanasKantha"),
        ("Junagadh", "Junagadh"),
        ("junagarh", "Junagadh"),
        ("Mehsana", "Mahesana"),
        ("mahesana", "Mahesana"),
    ]
    
    print("\nNormalization Results:")
    print("-" * 70)
    
    passed = 0
    failed = 0
    
    for input_name, expected in test_cases:
        normalized = normalize_district_name(input_name)
        
        # Check if normalized name has coordinates
        has_coords = normalized in DISTRICT_COORDS
        
        # Check if it matches expected
        matches = normalized == expected
        
        status = "✓" if matches and has_coords else "✗"
        
        if matches and has_coords:
            passed += 1
            lat, lon = DISTRICT_COORDS[normalized]
            print(f"{status} '{input_name}' → '{normalized}' (coords: {lat:.2f}, {lon:.2f})")
        else:
            failed += 1
            print(f"{status} '{input_name}' → '{normalized}' (expected: '{expected}', has_coords: {has_coords})")
    
    print("-" * 70)
    print(f"\nResults: {passed} passed, {failed} failed")
    
    return failed == 0


def test_all_districts_have_coords():
    """Test that all districts have coordinates."""
    
    print("\n" + "=" * 70)
    print("District Coordinates Verification")
    print("=" * 70)
    
    print(f"\nTotal districts with coordinates: {len(DISTRICT_COORDS)}")
    print("\nDistricts:")
    print("-" * 70)
    
    for district, (lat, lon) in sorted(DISTRICT_COORDS.items()):
        print(f"  {district:20s} → ({lat:.6f}, {lon:.6f})")
    
    return True


def test_mapping_completeness():
    """Test that all mapped names point to valid districts."""
    
    print("\n" + "=" * 70)
    print("District Mapping Completeness")
    print("=" * 70)
    
    print(f"\nTotal mappings: {len(DISTRICT_NAME_MAPPING)}")
    print("\nMapping verification:")
    print("-" * 70)
    
    all_valid = True
    
    for variant, canonical in sorted(DISTRICT_NAME_MAPPING.items()):
        if canonical in DISTRICT_COORDS:
            print(f"  ✓ '{variant}' → '{canonical}'")
        else:
            print(f"  ✗ '{variant}' → '{canonical}' (NOT IN COORDS)")
            all_valid = False
    
    print("-" * 70)
    
    if all_valid:
        print("\n✓ All mappings point to valid districts")
    else:
        print("\n✗ Some mappings point to invalid districts")
    
    return all_valid


def run_all_tests():
    """Run all district tests."""
    
    print("\n🧪 District Configuration Test Suite\n")
    
    results = []
    
    # Test 1: Normalization
    results.append(test_district_normalization())
    
    # Test 2: All districts have coords
    results.append(test_all_districts_have_coords())
    
    # Test 3: Mapping completeness
    results.append(test_mapping_completeness())
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed! District configuration is correct.")
    else:
        print("\n⚠ Some tests failed. Check errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
