from app.detection.analyzers.technical import TechnicalAnalyzer

message = "Click to verify your WhatsApp: http://wa-verify.online/confirm?user=91987654"

technical = TechnicalAnalyzer()
tech_result = technical.analyze(message)

print("Technical result:", tech_result)