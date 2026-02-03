"""
Synthetic test data for AI Honeypot API testing.
Contains realistic scam message scenarios for various scam types.
"""

from typing import Dict, List

# Synthetic scam messages organized by type
SYNTHETIC_SCAM_MESSAGES: Dict[str, List[Dict]] = {
    "bank_fraud": [
        {
            "message": "URGENT: Your SBI account XXXX1234 will be blocked today due to KYC non-compliance. Update immediately by sending ₹1 to verify: 9876543210@paytm",
            "expected_intel": {"upi_ids": ["9876543210@paytm"], "phone_numbers": []},
            "urgency": "critical"
        },
        {
            "message": "Dear Customer, Your bank account has been suspended due to suspicious activity. Call immediately: 9988776655 to restore access.",
            "expected_intel": {"phone_numbers": ["9988776655"], "upi_ids": []},
            "urgency": "high"
        },
        {
            "message": "RBI Alert: Your account ending 4567 is flagged for verification. Transfer ₹10 to account 12345678901234 IFSC: SBIN0001234 to verify.",
            "expected_intel": {"bank_accounts": ["12345678901234"], "upi_ids": []},
            "urgency": "high"
        },
        {
            "message": "Important! Update PAN-Aadhaar link for your bank account. Click here: http://secure-bank-verify.xyz/update?id=x123",
            "expected_intel": {"phishing_links": ["http://secure-bank-verify.xyz/update?id=x123"]},
            "urgency": "medium"
        },
        {
            "message": "Your HDFC account will be deactivated in 24 hours. Verify now to avoid penalty. Contact: help@hdfc-support.in or call 8877665544",
            "expected_intel": {"phone_numbers": ["8877665544"]},
            "urgency": "high"
        }
    ],
    
    "upi_fraud": [
        {
            "message": "Congratulations! You've won ₹50,000 in our lucky draw! Claim now by sending ₹99 processing fee to winner2024@oksbi",
            "expected_intel": {"upi_ids": ["winner2024@oksbi"]},
            "urgency": "medium"
        },
        {
            "message": "Get ₹500 cashback instantly! Just send ₹1 to verify your account: cashback@ybl",
            "expected_intel": {"upi_ids": ["cashback@ybl"]},
            "urgency": "low"
        },
        {
            "message": "Your refund of ₹2,500 is pending. Pay ₹5 verification fee to refund.help@paytm to receive it now.",
            "expected_intel": {"upi_ids": ["refund.help@paytm"]},
            "urgency": "medium"
        },
        {
            "message": "Amazon Lucky Customer! Collect your ₹10,000 gift card. Processing fee: ₹149 to amazon.prize@axl",
            "expected_intel": {"upi_ids": ["amazon.prize@axl"]},
            "urgency": "medium"
        }
    ],
    
    "phishing": [
        {
            "message": "Your Netflix subscription expires today! Update payment: https://netflix-renewal.secure-pay.in/update",
            "expected_intel": {"phishing_links": ["https://netflix-renewal.secure-pay.in/update"]},
            "urgency": "high"
        },
        {
            "message": "Click to verify your WhatsApp: http://wa-verify.online/confirm?user=91987654",
            "expected_intel": {"phishing_links": ["http://wa-verify.online/confirm?user=91987654"]},
            "urgency": "medium"
        },
        {
            "message": "Your Gmail storage is full. Click to get 15GB free: https://google-storage-upgrade.tk/free",
            "expected_intel": {"phishing_links": ["https://google-storage-upgrade.tk/free"]},
            "urgency": "medium"
        },
        {
            "message": "IT Department Notice: Download your tax refund certificate: http://incometax-gov.online/refund/2024",
            "expected_intel": {"phishing_links": ["http://incometax-gov.online/refund/2024"]},
            "urgency": "high"
        }
    ],
    
    "tech_support": [
        {
            "message": "Microsoft Alert: Virus detected on your computer! Call immediately: +91-9988776655 for remote assistance.",
            "expected_intel": {"phone_numbers": ["9988776655"]},
            "urgency": "critical"
        },
        {
            "message": "Your Windows license has expired. Your PC will be blocked. Call our tech support: 7766554433",
            "expected_intel": {"phone_numbers": ["7766554433"]},
            "urgency": "high"
        },
        {
            "message": "Apple ID compromised! Contact Apple Security immediately: 8765432109 to secure your account.",
            "expected_intel": {"phone_numbers": ["8765432109"]},
            "urgency": "critical"
        }
    ],
    
    "job_scam": [
        {
            "message": "Congratulations! You're selected for Data Entry job at Google. Salary: ₹50,000/month. Pay ₹2,000 registration fee to jobs@secure-pay.in",
            "expected_intel": {"upi_ids": ["jobs@secure-pay.in"]},
            "urgency": "medium"
        },
        {
            "message": "Work from home opportunity! Earn ₹30,000/month. Training fee: ₹1,500. Contact HR: 9123456789",
            "expected_intel": {"phone_numbers": ["9123456789"]},
            "urgency": "low"
        },
        {
            "message": "Amazon hiring now! Part time job, ₹2000/day. Apply: https://amazon-jobs-apply.online/register",
            "expected_intel": {"phishing_links": ["https://amazon-jobs-apply.online/register"]},
            "urgency": "medium"
        }
    ],
    
    "investment": [
        {
            "message": "Double your money in 24 hours! Guaranteed 200% returns. Invest now: investment.guru@icici",
            "expected_intel": {"upi_ids": ["investment.guru@icici"]},
            "urgency": "medium"
        },
        {
            "message": "Exclusive crypto opportunity! Min investment ₹5,000. Returns: 500%. Contact: 9876501234",
            "expected_intel": {"phone_numbers": ["9876501234"]},
            "urgency": "medium"
        },
        {
            "message": "Stock tips with 100% accuracy! Join our premium group. Fee: ₹999 to stockexpert@upi",
            "expected_intel": {"upi_ids": ["stockexpert@upi"]},
            "urgency": "low"
        }
    ],
    
    "lottery": [
        {
            "message": "You've won ₹25 Lakhs in International Lottery! Claim by paying ₹5,000 tax to lottery.claim@ybl",
            "expected_intel": {"upi_ids": ["lottery.claim@ybl"]},
            "urgency": "high"
        },
        {
            "message": "KBC Lucky Draw Winner! Collect ₹10,00,000. Processing fee: ₹3,500. Call: 8800112233",
            "expected_intel": {"phone_numbers": ["8800112233"]},
            "urgency": "high"
        }
    ]
}

# Multi-turn conversation test scenarios
CONVERSATION_FLOW_TESTS: List[Dict] = [
    {
        "name": "Bank Fraud Flow",
        "messages": [
            {"sender": "scammer", "text": "Dear customer, your SBI account will be blocked. Verify immediately."},
            # AI response expected here
            {"sender": "scammer", "text": "This is SBI customer care. Share your details or account will be suspended today."},
            # AI response expected here
            {"sender": "scammer", "text": "Pay ₹10 verification fee to verify.sbi@ybl to unblock your account."},
            # AI response expected here - should ask for confirmation
            {"sender": "scammer", "text": "Yes, pay to verify.sbi@ybl. Do it now to avoid permanent block."},
            # AI should have extracted upi_id by now
        ],
        "expected_scam_type": "bank_fraud",
        "expected_intel": ["verify.sbi@ybl"]
    },
    {
        "name": "Job Scam Flow",
        "messages": [
            {"sender": "scammer", "text": "Hi, you're shortlisted for Amazon data entry job. Interested?"},
            # AI response
            {"sender": "scammer", "text": "Great! Salary is ₹45,000/month. Work from home. Just need to pay registration fee of ₹1,500."},
            # AI response
            {"sender": "scammer", "text": "Pay to amazon.hr@paytm. After payment, you'll receive joining letter."},
            # AI should extract upi_id
        ],
        "expected_scam_type": "job_scam",
        "expected_intel": ["amazon.hr@paytm"]
    },
    {
        "name": "Tech Support Flow",
        "messages": [
            {"sender": "scammer", "text": "Alert! Your computer has been hacked. Hackers accessing your bank details right now."},
            # AI response
            {"sender": "scammer", "text": "I am from Microsoft Security. Call us immediately at 9876540000 to secure your computer."},
            # AI should extract phone number
        ],
        "expected_scam_type": "tech_support",
        "expected_intel": ["9876540000"]
    }
]

# Non-scam messages for false positive testing
LEGITIMATE_MESSAGES: List[Dict] = [
    {
        "message": "Hi, how are you doing today?",
        "expected_is_scam": False
    },
    {
        "message": "Meeting at 3pm tomorrow. Please confirm.",
        "expected_is_scam": False
    },
    {
        "message": "Happy birthday! Have a great day!",
        "expected_is_scam": False
    },
    {
        "message": "Your Swiggy order has been delivered.",
        "expected_is_scam": False
    },
    {
        "message": "Mom sent you a message on WhatsApp.",
        "expected_is_scam": False
    }
]

# Edge case messages
EDGE_CASES: List[Dict] = [
    {
        "message": "Send money",
        "description": "Very short, ambiguous message"
    },
    {
        "message": "call 9876543210",
        "description": "Just a phone number"
    },
    {
        "message": "Your OTP is 123456. Do not share with anyone. - SBI",
        "description": "Legitimate-looking OTP message"
    },
    {
        "message": "Pay electricity bill: paytm.com/bill",
        "description": "Legitimate payment reminder"
    }
]


def get_all_scam_messages() -> List[Dict]:
    """Get all scam messages as a flat list."""
    all_messages = []
    for scam_type, messages in SYNTHETIC_SCAM_MESSAGES.items():
        for msg in messages:
            all_messages.append({
                **msg,
                "scam_type": scam_type
            })
    return all_messages


def get_messages_by_type(scam_type: str) -> List[Dict]:
    """Get scam messages for a specific type."""
    return SYNTHETIC_SCAM_MESSAGES.get(scam_type, [])
