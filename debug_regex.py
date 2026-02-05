import re

message = "you've won ₹25 lakhs in international lottery! claim by paying ₹5,000 tax to lottery.claim@ybl"

# Test the problematic pattern
pattern0 = r"congratulations|you (won|win|are selected|qualified)"
matches0 = re.findall(pattern0, message, re.IGNORECASE)
print("Pattern 0 matches:", matches0)

# Test without capturing group
pattern0_fixed = r"congratulations|you (?:won|win|are selected|qualified)"
matches0_fixed = re.findall(pattern0_fixed, message, re.IGNORECASE)
print("Pattern 0 fixed matches:", matches0_fixed)

# Test simpler pattern
pattern0_simple = r"won|win|congratulations"
matches0_simple = re.findall(pattern0_simple, message, re.IGNORECASE)
print("Pattern 0 simple matches:", matches0_simple)

# Test pattern 2
pattern2 = r"free|bonus|reward|prize|gift"
matches2 = re.findall(pattern2, message, re.IGNORECASE)
print("Pattern 2 matches:", matches2)