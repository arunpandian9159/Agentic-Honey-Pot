from app.detection.analyzers.linguistic import LinguisticAnalyzer

# Test the specific message
message = "You've won ₹25 Lakhs in International Lottery! Claim by paying ₹5,000 tax to lottery.claim@ybl"

# Create analyzer
analyzer = LinguisticAnalyzer()

# Test manipulation patterns manually
manipulation_patterns = [
    r"congratulations|you (won|win|are selected|qualified)",
    r"exclusive|special|limited|selected (customers|users)",
    r"free|bonus|reward|prize|gift",
    r"guaranteed|assured|confirmed|approved"
]

message_lower = message.lower()
print("Message:", message_lower)

# Test each pattern individually
for i, pattern in enumerate(manipulation_patterns):
    import re
    match = re.search(pattern, message_lower)
    print(f"Pattern {i}: {pattern}")
    print(f"  Match: {match}")
    if match:
        print(f"  Matched text: '{match.group()}'")
    print()

# Test the full analysis
result = analyzer.analyze(message)
print("Full result:", result)