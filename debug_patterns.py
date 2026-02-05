import re

# Test the patterns manually
message = "You've won ₹25 Lakhs in International Lottery! Claim by paying ₹5,000 tax to lottery.claim@ybl"
message_lower = message.lower()

manipulation_patterns = [
    r"congratulations|you (won|win|are selected|qualified)",
    r"exclusive|special|limited|selected (customers|users)",
    r"free|bonus|reward|prize|gift",
    r"guaranteed|assured|confirmed|approved"
]

print("Message:", message_lower)
for i, pattern in enumerate(manipulation_patterns):
    matches = re.findall(pattern, message_lower, re.IGNORECASE)
    print(f"Pattern {i}: {pattern}")
    print(f"  Matches: {matches}")
    if matches:
        print(f"  Found: {matches}")
    print()

# Test individual words
print("Testing individual words:")
words = ["won", "win", "lottery", "prize"]
for word in words:
    if word in message_lower:
        print(f"Found '{word}' in message")
    else:
        print(f"'{word}' NOT found in message")