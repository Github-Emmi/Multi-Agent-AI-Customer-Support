# 10 — Knowledge Base Creation Guide

> **Project:** Multi-Agent AI Customer Support Assistant  
> **Fictional Company:** TechMart Electronics  
> **Format:** PDF files ingested into FAISS vector store

---

## TechMart Electronics — Company Profile

| Field | Value |
|-------|-------|
| Company Name | TechMart Electronics |
| Industry | Consumer Electronics Retail |
| Products | Laptops, Smartphones, Tablets, Smart Home Devices |
| Support Channels | Chat, Email, Phone |
| Return Window | 30 days |
| Warranty | 1 year standard, 3 years extended |

---

## Required Knowledge Base Files

Create the following PDFs in `knowledge_base/`:

| File | Content Summary | Primary Agent |
|------|----------------|--------------|
| `FAQ.pdf` | General questions, contact info, hours | FAQ Agent |
| `RefundPolicy.pdf` | Return/refund rules, timelines, conditions | Billing Agent |
| `ShippingPolicy.pdf` | Delivery timeframes, carriers, tracking | FAQ / Product Agent |
| `Warranty.pdf` | Warranty coverage, claim process, exclusions | Product Agent |
| `Pricing.pdf` | Product prices, subscription tiers, discounts | Billing / Product Agent |
| `Products.pdf` | Full product catalog, specs, comparisons | Product Agent |
| `InstallationGuide.pdf` | Device setup, driver installation, troubleshooting | Technical Agent |
| `UserManual.pdf` | Account management, login, password reset | Technical Agent |

---

## Content Templates

### FAQ.pdf — Minimum Content

```
TechMart Electronics — Frequently Asked Questions

Q: How do I contact TechMart support?
A: You can reach us via:
   - Live chat at support.techmart.com (24/7)
   - Email: support@techmart.com (response within 4 hours)
   - Phone: 1-800-TECHMART (Mon–Fri, 8AM–8PM EST)

Q: What are your business hours?
A: Our live chat is available 24/7. Phone support operates Monday to Friday,
   8AM to 8PM Eastern Standard Time.

Q: How do I track my order?
A: Log in to your TechMart account, go to "My Orders", and click
   "Track Shipment" for real-time updates.

Q: Can I change or cancel my order?
A: Orders can be cancelled within 1 hour of placement. After that, please
   wait to receive the item and initiate a return.

Q: How do I create a TechMart account?
A: Visit techmart.com, click "Sign Up", and follow the registration steps.
   A verification email will be sent to confirm your address.
```

### RefundPolicy.pdf — Minimum Content

```
TechMart Electronics — Refund & Return Policy

Return Window
Items may be returned within 30 days of delivery for a full refund.
After 30 days, returns are accepted only for defective items under warranty.

Conditions for Return
- Item must be in original packaging
- All accessories and documentation must be included
- Item must not show signs of physical damage caused by the customer

Refund Processing Time
- Credit/Debit Card: 5-7 business days after we receive the item
- PayPal: 3-5 business days
- Store Credit: Immediate upon return approval

How to Initiate a Return
1. Log in to your TechMart account
2. Navigate to "My Orders"
3. Select the item and click "Request Return"
4. Print the prepaid return label
5. Drop the package at any UPS or FedEx location

Subscription Refunds
TechMart Premium subscriptions are refundable within 7 days of purchase if
no Premium features have been used. After 7 days, the subscription is
non-refundable for the current billing period.

Non-Refundable Items
- Downloaded digital software licenses
- Gift cards
- Items returned after 30 days without defect
```

### Warranty.pdf — Minimum Content

```
TechMart Electronics — Warranty Policy

Standard Warranty (1 Year)
All TechMart products include a 1-year limited warranty covering:
- Manufacturing defects
- Hardware failures under normal use
- Screen defects (dead pixels > 5)

Extended Warranty (3 Years)
Available for purchase at checkout. Covers all Standard Warranty items plus:
- Accidental damage (1 incident per year)
- Battery replacement (if capacity drops below 80%)

What Is NOT Covered
- Physical damage caused by the customer
- Water damage (unless IPX-certified model)
- Software issues or virus damage
- Unauthorized modifications or repairs

How to File a Warranty Claim
1. Visit warranty.techmart.com
2. Enter your product serial number
3. Describe the issue
4. A technician will contact you within 24 hours
5. Ship the device to our repair center (prepaid label provided)

Warranty Repair Timeframe
- Standard repairs: 5-10 business days
- Screen replacements: 3-5 business days
- Complete replacement (if unrepairable): 7-14 business days
```

### UserManual.pdf — Minimum Content

```
TechMart Electronics — User Account Manual

Creating Your Account
1. Go to techmart.com/signup
2. Enter your full name, email address, and a password (min 8 characters)
3. Check your email for a verification link
4. Click the verification link to activate your account

Logging In
1. Go to techmart.com/login
2. Enter your email and password
3. If you have 2FA enabled, enter the code from your authenticator app

Password Reset
1. Go to techmart.com/login
2. Click "Forgot Password?"
3. Enter your registered email address
4. Check your email for the reset link (valid for 1 hour)
5. Click the link and enter your new password
6. You will receive a confirmation email

Managing Your Subscription
1. Log in to your account
2. Go to "Account Settings" → "Subscription"
3. You can upgrade, downgrade, or cancel from this page
4. Downgrades take effect at the end of the current billing period

Two-Factor Authentication
1. Go to "Account Settings" → "Security"
2. Click "Enable 2FA"
3. Scan the QR code with Google Authenticator or Authy
4. Enter the 6-digit code to confirm
```

---

## Generating PDFs

You can use any of these approaches to create PDFs:

### Option 1 — Python (fpdf2)

```bash
pip install fpdf2
```

```python
from fpdf import FPDF

def create_pdf(title: str, content: str, filename: str):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, title, ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Helvetica", size=11)
    for line in content.split("\n"):
        pdf.multi_cell(0, 6, line)
    pdf.output(f"knowledge_base/{filename}")

# Run: python scripts/create_knowledge_base.py
```

### Option 2 — Google Docs

1. Write content in Google Docs
2. File → Download → PDF Document

### Option 3 — Microsoft Word → Export as PDF

---

## Ingestion Verification

After creating all PDFs, run ingestion and verify:

```bash
# Ingest all PDFs
python -m backend.rag.pipeline

# Test retrieval for each domain
python -c "
from backend.rag.retriever import retriever

tests = [
    ('How do I get a refund?', 'RefundPolicy'),
    ('My password reset is not working', 'UserManual'),
    ('What is the warranty on laptops?', 'Warranty'),
    ('What are TechMart business hours?', 'FAQ'),
]

for query, expected_source in tests:
    results = retriever.search(query, top_k=3)
    sources = [r['source'] for r in results]
    passed = any(expected_source.lower() in s.lower() for s in sources)
    print(f'[{\"PASS\" if passed else \"FAIL\"}] {query}')
    print(f'  Sources: {sources}')
"
```
