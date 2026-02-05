import re

message = "you've won ₹25 lakhs in international lottery! claim by paying ₹5,000 tax to lottery.claim@ybl"
message_lower = message.lower()

# Test the specific pattern
pattern = r"you (won|win|are selected|qualified)"
match = re.search(pattern, message_lower)
print(f"Pattern: {pattern}")
print(f"Message: {message_lower}")
print(f"Match: {match}")

# Test simpler pattern
simple_pattern = r"won"
simple_match = re.search(simple_pattern, message_lower)
print(f"Simple pattern 'won': {simple_match}")

# Test the full pattern
full_pattern = r"congratulations|you (won|win|are selected|qualified)"
full_match = re.search(full_pattern, message_lower)
print(f"Full pattern: {full_pattern}")
print(f"Full match: {full_match}")

# Test with word boundaries
word_pattern = r"\bwon\b"
word_match = re.search(word_pattern, message_lower)
print(f"Word boundary pattern: {word_pattern}")
print(f"Word match: {word_match}")