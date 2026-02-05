from app.detection.analyzers.linguistic import LinguisticAnalyzer
from app.detection.analyzers.behavioral import BehavioralAnalyzer

message = "You've won ₹25 Lakhs in International Lottery! Claim by paying ₹5,000 tax to lottery.claim@ybl"

linguistic = LinguisticAnalyzer()
behavioral = BehavioralAnalyzer()

ling_result = linguistic.analyze(message)
behav_result = behavioral.analyze(message)

print("Linguistic result:", ling_result)
print("Behavioral result:", behav_result)
print("Combined:", ling_result["overall_linguistic_score"] + behav_result["overall_behavioral_score"])