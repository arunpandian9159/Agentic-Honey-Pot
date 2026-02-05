from app.detection.analyzers.linguistic import LinguisticAnalyzer

message = "You've won ₹25 Lakhs in International Lottery! Claim by paying ₹5,000 tax to lottery.claim@ybl"

linguistic = LinguisticAnalyzer()
result = linguistic.analyze(message)

print("Full result:", result)

# Let's check the manipulation patterns manually
import re
manipulation_patterns = [
    r"congratulations|you (won|win|are selected|qualified)",
    r"exclusive|special|limited|selected (customers|users)",
    r"free|bonus|reward|prize|gift",
    r"guaranteed|assured|confirmed|approved"
]

message_lower = message.lower()
print("Message:", message_lower)
for i, pattern in enumerate(manipulation_patterns):
    matches = re.findall(pattern, message_lower, re.IGNORECASE)
    print(f"Pattern {i}: {pattern} -> matches: {matches}")