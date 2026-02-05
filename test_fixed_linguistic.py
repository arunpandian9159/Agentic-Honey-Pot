from app.detectors.linguistic_analyzer_fixed import LinguisticAnalyzer

message = "You've won ₹25 Lakhs in International Lottery! Claim by paying ₹5,000 tax to lottery.claim@ybl"

analyzer = LinguisticAnalyzer()
result = analyzer.analyze(message)

print("Result:", result)

# Test the specific patterns
import re
message_lower = message.lower()

# Test the fixed pattern
pattern = r"congratulations|you('ve)? (won|win|are selected|qualified)"
match = re.search(pattern, message_lower, re.IGNORECASE)
print(f"Fixed pattern match: {match}")
if match:
    print(f"Matched: '{match.group()}'")

# Test pattern 2
pattern2 = r"free|bonus|reward|prize|gift"
match2 = re.search(pattern2, message_lower, re.IGNORECASE)
print(f"Pattern 2 match: {match2}")
if match2:
    print(f"Matched: '{match2.group()}'")