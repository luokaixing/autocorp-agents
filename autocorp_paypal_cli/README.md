# AutoCorp PayPal CLI

> A standalone command-line tool for collecting PayPal payments without a web app. Built for solo creators, freelancers, and small AI companies.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PayPal Live](https://img.shields.io/badge/PayPal-Live-success.svg)]()

## Why?

Most PayPal integration guides assume you have a web app with a backend, a domain, and SSL. **You don't need any of that.** If you're a freelancer, solo creator, or small AI company that just wants to:

- Send a payment link to a customer
- Check if they paid
- See your total revenue

...then you don't need a web framework. You need a CLI.

## Installation

```bash
pip install autocorp-paypal-cli
```

Or from source:

```bash
git clone https://github.com/yourname/autocorp-paypal-cli.git
cd autocorp-paypal-cli
pip install -e .
```

## Setup

### 1. Get PayPal API Credentials

1. Go to [developer.paypal.com/dashboard/](https://developer.paypal.com/dashboard/)
2. Log in with your PayPal business account
3. Switch to **Live** mode (top right)
4. Go to **Apps & Credentials** → **Create App**
5. Choose type: **Merchant**
6. Copy your **Client ID** and **Secret**

### 2. Initialize the CLI

```bash
autocorp-paypal init \
    --client-id "YOUR_CLIENT_ID" \
    --client-secret "YOUR_CLIENT_SECRET"
```

That's it. You're ready to collect payments.

## Usage

### Create a Payment Order

```bash
autocorp-paypal create \
    --amount 50 \
    --currency USD \
    --description "AI Agent consulting - 1 hour"
```

Output:
```
✅ Order created successfully!

  Order ID:     6H707311BH815501H
  Amount:       50.00 USD
  Description:  AI Agent consulting - 1 hour
  Status:       CREATED

  Pay URL:      https://www.paypal.com/checkoutnow?token=6H707311BH815501H

  Share this URL with your customer to receive payment.
```

### Check Order Status

```bash
autocorp-paypal check 6H707311BH815501H
```

Output:
```
Order: 6H707311BH815501H
  Status:   COMPLETED
  Amount:   50.00 USD
  Payer:    customer@example.com
  Payer ID:  ABC123XYZ

✅ Payment completed and captured.
```

### List All Orders

```bash
autocorp-paypal list
```

Output:
```
Order ID                  Status       Amount       Description
--------------------------------------------------------------------------------
6H707311BH815501H         COMPLETED    50.00 USD    AI Agent consulting
5X2981342KL093421R        PENDING      100.00 USD   Crypto market report
7Y1023948RP039123K        COMPLETED    200.00 USD   Architecture design

Total: 3 orders
```

### Show Revenue Dashboard

```bash
autocorp-paypal dashboard
```

Output:
```
==================================================
  AutoCorp PayPal Dashboard
==================================================
  Total Revenue:    $250.00
  Pending Amount:   $100.00
  Completed Orders: 2
  Pending Orders:   1
  Total Orders:     3
==================================================
```

## Use Cases

- **Freelancers**: Send payment links to clients without a website
- **AI companies**: Collect payments for AI agent consulting
- **Content creators**: Sell PDF reports, courses, or subscriptions
- **Crypto researchers**: Charge for market analysis reports
- **Open source maintainers**: Accept sponsorships via PayPal

## Comparison

| Tool | Requires Website | Requires Stripe | CLI | Standalone |
|------|-----------------|-----------------|-----|------------|
| **AutoCorp PayPal CLI** | ❌ | ❌ | ✅ | ✅ |
| Stripe Checkout | ✅ | ✅ | ❌ | ❌ |
| PayPal Buttons | ✅ | ❌ | ❌ | ❌ |
| Gumroad | ❌ | Optional | ❌ | ❌ |
| Lemon Squeezy | ❌ | ✅ | ❌ | ❌ |

## Advanced: Use as a Python Library

```python
from autocorp_paypal_cli import PayPalClient

client = PayPalClient(sandbox=False)

# Create order
order = client.create_order(
    amount=150.00,
    currency="USD",
    description="Premium consulting package"
)

print(f"Send this URL to your client: {order['approval_url']}")

# After client pays, check status
result = client.check_order(order["id"])
if result["status"] == "COMPLETED":
    print(f"Payment received: {result['amount']} {result['currency']}")
```

## Roadmap

- [ ] v0.2: Add subscription billing support
- [ ] v0.3: Add webhook listener (no SSL required, uses polling)
- [ ] v0.4: Add multi-currency support with auto-conversion
- [ ] v0.5: Add invoice PDF generation
- [ ] v1.0: Production stable release

## License

MIT License — see [LICENSE](LICENSE) for details.

## Sponsors

If this tool saves you time, consider sponsoring via GitHub Sponsors:

- GitHub Sponsors: [@autocorp](https://github.com/sponsors/autocorp)

> ETH/PayPal tipping addresses are intentionally omitted from public docs. Use GitHub Sponsors for direct support.

## Author

**AutoCorp Research Desk** — an autonomous AI company operating since June 2026.
