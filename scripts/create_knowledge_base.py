"""
scripts/create_knowledge_base.py
Generates all 8 TechMart Electronics PDF knowledge base documents.
Run: python scripts/create_knowledge_base.py
Requires: pip install fpdf2
"""
from pathlib import Path

try:
    from fpdf import FPDF
except ImportError:
    raise SystemExit("Install fpdf2 first:  pip install fpdf2")

OUTPUT_DIR = Path("knowledge_base")
OUTPUT_DIR.mkdir(exist_ok=True)


def _safe(text: str) -> str:
    """Replace characters outside latin-1 range."""
    return (text
            .replace("\u2014", "-").replace("\u2013", "-")
            .replace("\u2018", "'").replace("\u2019", "'")
            .replace("\u201c", '"').replace("\u201d", '"')
            .replace("\u2026", "...").replace("\u00a0", " "))


def make_pdf(filename: str, title: str, sections: list[tuple[str, str]]) -> None:
    from fpdf.enums import XPos, YPos
    pdf = FPDF()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Company header
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_fill_color(30, 80, 160)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, "TechMart Electronics", fill=True,
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(2)

    # Document title
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 80, 160)
    pdf.cell(0, 9, _safe(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    for heading, body in sections:
        # Section heading
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(230, 240, 255)
        pdf.cell(0, 7, _safe(heading), fill=True,
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1)
        # Body text
        pdf.set_font("Helvetica", size=9)
        for line in _safe(body.strip()).split("\n"):
            stripped = line.strip()
            if stripped:
                pdf.multi_cell(pdf.epw, 5, stripped)
            else:
                pdf.ln(3)
        pdf.ln(2)

    path = OUTPUT_DIR / filename
    pdf.output(str(path))
    print(f"  Created: {path}")


# ── 1. FAQ ─────────────────────────────────────────────────────────────────────
make_pdf("faq.pdf", "Frequently Asked Questions", [
    ("How do I contact TechMart support?",
     "Live chat: support.techmart.com (24/7)\n"
     "Email: support@techmart.com — responses within 4 hours\n"
     "Phone: 1-800-TECHMART, Monday–Friday 8 AM–8 PM EST"),
    ("What are TechMart's business hours?",
     "Live chat is available 24 hours a day, 7 days a week.\n"
     "Phone support operates Monday to Friday, 8 AM to 8 PM Eastern Standard Time."),
    ("How do I track my order?",
     "Log in to your TechMart account, navigate to My Orders, "
     "and click Track Shipment for real-time updates."),
    ("Can I change or cancel my order?",
     "Orders can be cancelled within 1 hour of placement.\n"
     "After 1 hour, wait to receive the item and initiate a return instead."),
    ("How do I create a TechMart account?",
     "Visit techmart.com, click Sign Up, and complete the registration form.\n"
     "A verification email will be sent to confirm your address."),
    ("Does TechMart offer student discounts?",
     "Yes. Students with a valid .edu email address receive 10% off all products.\n"
     "Apply at checkout using coupon code STUDENT10."),
    ("Where is TechMart headquartered?",
     "TechMart Electronics is headquartered in Austin, Texas, USA.\n"
     "We ship to over 40 countries worldwide."),
    ("How do I leave a product review?",
     "Navigate to the product page while logged in and click Write a Review.\n"
     "Reviews are published within 24 hours after moderation."),
])

# ── 2. Refund Policy ───────────────────────────────────────────────────────────
make_pdf("refund_policy.pdf", "Refund & Return Policy", [
    ("Return Window",
     "Items may be returned within 30 days of delivery for a full refund.\n"
     "After 30 days, returns are accepted only for defective items covered by warranty."),
    ("Conditions for Return",
     "Item must be in original packaging with all accessories included.\n"
     "Item must not show signs of physical damage caused by the customer.\n"
     "Software licenses that have been activated are non-refundable."),
    ("Refund Processing Time",
     "Credit/Debit Card: 5–7 business days after we receive the returned item.\n"
     "PayPal: 3–5 business days.\n"
     "Store Credit: Issued immediately upon return approval."),
    ("How to Initiate a Return",
     "1. Log in to your TechMart account.\n"
     "2. Navigate to My Orders.\n"
     "3. Select the item and click Request Return.\n"
     "4. Print the prepaid return label.\n"
     "5. Drop the package at any UPS or FedEx location."),
    ("Subscription Refunds",
     "TechMart Premium subscriptions are refundable within 7 days of purchase "
     "if no Premium features have been used.\n"
     "After 7 days, the subscription is non-refundable for the current billing period."),
    ("Non-Refundable Items",
     "Downloaded digital software licenses.\n"
     "Gift cards and promotional credits.\n"
     "Items returned after 30 days without a confirmed defect."),
    ("Damaged or Defective Items",
     "If your item arrives damaged, contact support within 48 hours with photos.\n"
     "We will arrange a free replacement or full refund including shipping costs."),
])

# ── 3. Shipping Policy ─────────────────────────────────────────────────────────
make_pdf("shipping_policy.pdf", "Shipping Policy", [
    ("Standard Shipping",
     "Estimated delivery: 5–7 business days within the continental US.\n"
     "Cost: Free on orders over $50. $4.99 for orders under $50."),
    ("Expedited Shipping",
     "Estimated delivery: 2–3 business days.\n"
     "Cost: $9.99 per order. Available for US addresses only."),
    ("Overnight Shipping",
     "Next business day delivery when ordered before 2 PM EST.\n"
     "Cost: $19.99 per order. Not available for PO Boxes or Hawaii/Alaska."),
    ("International Shipping",
     "Available to 40+ countries. Estimated delivery: 7–14 business days.\n"
     "International customers are responsible for customs duties and taxes."),
    ("Order Tracking",
     "A tracking number is emailed within 24 hours of shipment.\n"
     "Track your order at techmart.com/track or via the carrier's website."),
    ("Shipping Carriers",
     "We ship via UPS, FedEx, and USPS depending on order size and destination.\n"
     "Large items (monitors, desktops) are shipped via freight with liftgate service."),
    ("Lost or Stolen Packages",
     "If your tracking shows delivered but you have not received the package:\n"
     "1. Check with neighbors and building management.\n"
     "2. Contact your local carrier office.\n"
     "3. If unresolved within 3 business days, contact TechMart support."),
])

# ── 4. Warranty ────────────────────────────────────────────────────────────────
make_pdf("warranty.pdf", "Warranty Policy", [
    ("Standard Warranty — 1 Year",
     "All TechMart products include a 1-year limited warranty covering:\n"
     "Manufacturing defects, hardware failures under normal use, "
     "and screen defects (more than 5 dead pixels)."),
    ("Extended Warranty — 3 Years",
     "Available for purchase at checkout for $49.99.\n"
     "Covers all Standard Warranty items plus:\n"
     "One accidental damage incident per year.\n"
     "Battery replacement if capacity drops below 80% within 3 years."),
    ("What Is NOT Covered",
     "Physical damage caused by the customer (drops, cracks, spills).\n"
     "Water damage on non-IPX-certified models.\n"
     "Software issues, virus damage, or data loss.\n"
     "Unauthorized modifications or third-party repairs."),
    ("How to File a Warranty Claim",
     "1. Visit warranty.techmart.com.\n"
     "2. Enter your product serial number.\n"
     "3. Describe the issue and upload photos if applicable.\n"
     "4. A technician will contact you within 24 hours.\n"
     "5. A prepaid shipping label is provided for approved claims."),
    ("Warranty Repair Timeframe",
     "Standard repairs: 5–10 business days.\n"
     "Screen replacements: 3–5 business days.\n"
     "Complete replacement (if unrepairable): 7–14 business days."),
    ("International Warranty",
     "TechMart warranties are valid worldwide.\n"
     "For international claims, contact support@techmart.com for instructions."),
])

# ── 5. Pricing ─────────────────────────────────────────────────────────────────
make_pdf("pricing.pdf", "Product Pricing & Subscription Plans", [
    ("TechMart Premium Subscription",
     "Free Plan: Basic chat support, standard response times.\n"
     "Premium Monthly: $9.99/month — Priority support, 24/7 chat, 1-hour response SLA.\n"
     "Premium Annual: $89.99/year — Same as monthly, save 25%."),
    ("Laptop Pricing",
     "TechMart UltraBook 13: $899 — Intel i5, 16 GB RAM, 512 GB SSD.\n"
     "TechMart UltraBook Pro 15: $1,299 — Intel i7, 32 GB RAM, 1 TB SSD.\n"
     "TechMart UltraBook Max 17: $1,799 — Intel i9, 64 GB RAM, 2 TB SSD."),
    ("Smartphone Pricing",
     "TechMart Phone SE: $399 — 6.1 inch, 128 GB, 5G.\n"
     "TechMart Phone Pro: $699 — 6.5 inch, 256 GB, 5G, triple camera.\n"
     "TechMart Phone Ultra: $999 — 6.7 inch, 512 GB, 5G, satellite connectivity."),
    ("Tablet Pricing",
     "TechMart Pad 10: $349 — 10.2 inch, 64 GB, Wi-Fi.\n"
     "TechMart Pad Pro 12: $599 — 12.9 inch, 256 GB, Wi-Fi + LTE."),
    ("Smart Home Devices",
     "TechMart Smart Speaker: $79 — Voice assistant, multi-room audio.\n"
     "TechMart Smart Display 8: $149 — 8 inch display, smart home hub.\n"
     "TechMart Security Camera: $99 — 4K, night vision, cloud storage."),
    ("Student & Education Discount",
     "Students with a valid .edu email receive 10% off.\n"
     "Educational institutions receive 20% off orders of 10+ units."),
])

# ── 6. Products ────────────────────────────────────────────────────────────────
make_pdf("products.pdf", "Product Catalog & Specifications", [
    ("TechMart UltraBook 13",
     "Processor: Intel Core i5-13500H.\n"
     "Memory: 16 GB DDR5 RAM (upgradeable to 32 GB).\n"
     "Storage: 512 GB NVMe SSD.\n"
     "Display: 13.3 inch IPS, 2560x1600, 120 Hz.\n"
     "Battery: 72 Wh, up to 12 hours. Weight: 1.2 kg.\n"
     "Ports: 2x USB-C (Thunderbolt 4), 1x USB-A, HDMI 2.1, SD card reader."),
    ("TechMart Phone Pro",
     "Display: 6.5 inch AMOLED, 2400x1080, 120 Hz.\n"
     "Processor: TechMart A7 chip.\n"
     "Camera: 50 MP main, 12 MP ultra-wide, 10 MP telephoto (3x zoom).\n"
     "Battery: 5000 mAh, 65W fast charging, 15W wireless charging.\n"
     "Storage: 256 GB. RAM: 12 GB. 5G supported."),
    ("TechMart Pad Pro 12",
     "Display: 12.9 inch Liquid Retina XDR, 2732x2048.\n"
     "Processor: TechMart M2 chip.\n"
     "Storage: 256 GB (expandable via USB-C hub).\n"
     "Battery: Up to 10 hours. Supports TechMart Pencil and Magic Keyboard."),
    ("TechMart Smart Speaker",
     "Audio: 360-degree sound, 3 tweeters + 1 woofer.\n"
     "Voice Assistant: Built-in TechMart Assistant + Alexa compatible.\n"
     "Connectivity: Wi-Fi 6, Bluetooth 5.2.\n"
     "Smart Home: Controls 1000+ compatible devices via voice."),
    ("Comparisons",
     "UltraBook 13 vs UltraBook Pro 15:\n"
     "  Pro 15 has larger display, i7 vs i5, and double the RAM and storage.\n"
     "  UltraBook 13 is lighter and better for portability.\n\n"
     "Phone SE vs Phone Pro:\n"
     "  Pro has triple camera, larger battery, and 5G.\n"
     "  SE is a budget option with single camera."),
])

# ── 7. Installation Guide ──────────────────────────────────────────────────────
make_pdf("installation_guide.pdf", "Installation & Setup Guide", [
    ("Setting Up Your TechMart Laptop",
     "1. Press the power button to start the initial setup wizard.\n"
     "2. Select your language, region, and keyboard layout.\n"
     "3. Connect to Wi-Fi.\n"
     "4. Sign in with your TechMart account or create a new one.\n"
     "5. The system will download and install the latest updates automatically."),
    ("Installing TechMart Drivers (Windows)",
     "1. Open techmart.com/drivers in your browser.\n"
     "2. Enter your device serial number.\n"
     "3. Download the Driver Pack for your model.\n"
     "4. Run the installer and follow the prompts.\n"
     "5. Restart your computer after installation."),
    ("Common Installation Errors",
     "Error: Driver installation failed — Run the installer as Administrator.\n"
     "Error: Incompatible OS — Verify your Windows version meets minimum requirements (Windows 11).\n"
     "Error: Signature verification failed — Disable Secure Boot temporarily in BIOS."),
    ("Resetting Your Device to Factory Settings",
     "Windows: Settings > Recovery > Reset this PC > Remove everything.\n"
     "This will erase all personal data. Back up important files first.\n"
     "Full factory reset with OS reinstall: Hold Shift when clicking Restart, "
     "then Troubleshoot > Reset this PC."),
    ("Setting Up TechMart Phone",
     "1. Insert SIM card (nano-SIM, slot on left side).\n"
     "2. Power on and follow the on-screen setup.\n"
     "3. Sign in to your Google account to restore apps.\n"
     "4. Download TechMart Connect app from the Play Store.\n"
     "5. Enable 5G in Settings > Network > Mobile Network."),
    ("Bluetooth Pairing",
     "1. On your device, go to Settings > Bluetooth.\n"
     "2. Enable Bluetooth.\n"
     "3. Put the TechMart accessory in pairing mode (hold button for 3 seconds).\n"
     "4. Select the device from the list and confirm pairing."),
])

# ── 8. User Manual ─────────────────────────────────────────────────────────────
make_pdf("user_manual.pdf", "User Account Manual", [
    ("Creating Your Account",
     "1. Go to techmart.com/signup.\n"
     "2. Enter your full name, email address, and a password (minimum 8 characters, "
     "must include a number and a special character).\n"
     "3. Check your email for a verification link.\n"
     "4. Click the link to activate your account."),
    ("Logging In",
     "1. Go to techmart.com/login.\n"
     "2. Enter your registered email and password.\n"
     "3. If 2FA is enabled, enter the 6-digit code from your authenticator app."),
    ("Password Reset",
     "1. Go to techmart.com/login and click Forgot Password.\n"
     "2. Enter your registered email address.\n"
     "3. Check your inbox for the reset link (valid for 1 hour).\n"
     "4. Check your spam/junk folder if the email does not arrive within 5 minutes.\n"
     "5. Click the link and enter your new password.\n"
     "6. You will receive a confirmation email once the password is changed."),
    ("Managing Your TechMart Premium Subscription",
     "1. Log in and go to Account Settings > Subscription.\n"
     "2. You can upgrade, downgrade, or cancel from this page.\n"
     "3. Downgrades take effect at the end of the current billing period.\n"
     "4. Cancellations are effective immediately with no prorated refund."),
    ("Enabling Two-Factor Authentication",
     "1. Go to Account Settings > Security.\n"
     "2. Click Enable Two-Factor Authentication.\n"
     "3. Scan the QR code with Google Authenticator or Authy.\n"
     "4. Enter the 6-digit code shown to confirm.\n"
     "5. Save your backup codes in a secure location."),
    ("Updating Account Information",
     "Name and email can be updated in Account Settings > Profile.\n"
     "Email changes require verification via a confirmation link.\n"
     "Billing address can be updated in Account Settings > Billing."),
    ("Deactivating Your Account",
     "Go to Account Settings > Privacy > Deactivate Account.\n"
     "Your data will be retained for 30 days then permanently deleted.\n"
     "Contact support@techmart.com to cancel deactivation within 30 days."),
])

print(f"\nAll 8 knowledge base PDFs created in {OUTPUT_DIR.resolve()}/")
print("Next step: run  python -m backend.rag.pipeline  to ingest them.")
