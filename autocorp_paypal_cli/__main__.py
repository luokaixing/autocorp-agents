"""AutoCorp PayPal CLI — Standalone payment collection tool

A minimal CLI for collecting PayPal payments without a web app.
Perfect for solo creators, freelancers, and AI companies.

USAGE:
    # Set up credentials (one-time)
    python -m autocorp_paypal_cli init --client-id YOUR_ID --client-secret YOUR_SECRET

    # Create a payment order
    python -m autocorp_paypal_cli create --amount 50 --description "Consulting"

    # Check order status
    python -m autocorp_paypal_cli check <order_id>

    # List all orders
    python -m autocorp_paypal_cli list

    # Show revenue dashboard
    python -m autocorp_paypal_cli dashboard

LICENSE: MIT
AUTHOR: AutoCorp Research Desk
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Try to import the PayPal client
try:
    from engine.payments.paypal import PayPalClient, PayPalError
except ImportError:
    # Allow standalone use by defining minimal PayPalClient
    print("Note: Running in standalone mode. For full functionality, install with engine.payments.")
    PayPalClient = None
    PayPalError = Exception


CONFIG_DIR = Path(".autocorp-paypal")
CONFIG_FILE = CONFIG_DIR / "config.json"
ORDERS_DIR = CONFIG_DIR / "orders"


def cmd_init(args):
    """Initialize credentials."""
    CONFIG_DIR.mkdir(exist_ok=True)
    ORDERS_DIR.mkdir(exist_ok=True)
    config = {
        "client_id": args.client_id,
        "client_secret": args.client_secret,
        "sandbox": args.sandbox,
        "created_at": datetime.now().isoformat(),
    }
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
    print(f"Configuration saved to {CONFIG_FILE}")
    print(f"  client_id: {args.client_id[:10]}...{args.client_id[-4:]}")
    print(f"  sandbox: {args.sandbox}")


def cmd_create(args):
    """Create a payment order."""
    if not CONFIG_FILE.exists():
        print("Error: Run 'init' first to set up credentials.")
        sys.exit(1)

    config = json.loads(CONFIG_FILE.read_text())
    client = PayPalClient(sandbox=config.get("sandbox", False))

    try:
        order = client.create_order(
            amount=float(args.amount),
            currency=args.currency,
            description=args.description,
        )
        print("✅ Order created successfully!")
        print()
        print(f"  Order ID:     {order['id']}")
        print(f"  Amount:       {args.amount} {args.currency}")
        print(f"  Description:  {args.description}")
        print(f"  Status:       {order.get('status', 'CREATED')}")
        print()
        print(f"  Pay URL:      {order.get('approval_url', 'N/A')}")
        print()
        print("  Share this URL with your customer to receive payment.")
    except PayPalError as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_check(args):
    """Check order status."""
    if not CONFIG_FILE.exists():
        print("Error: Run 'init' first to set up credentials.")
        sys.exit(1)

    config = json.loads(CONFIG_FILE.read_text())
    client = PayPalClient(sandbox=config.get("sandbox", False))

    try:
        result = client.check_order(args.order_id)
        print(f"Order: {args.order_id}")
        print(f"  Status:   {result.get('status')}")
        print(f"  Amount:   {result.get('amount')} {result.get('currency')}")
        payer = result.get("payer_info", {})
        if payer:
            print(f"  Payer:    {payer.get('email', 'N/A')}")
            print(f"  Payer ID: {payer.get('payer_id', 'N/A')}")
        print()
        if result.get("status") == "COMPLETED":
            print("✅ Payment completed and captured.")
        elif result.get("status") == "APPROVED":
            print("⏳ Payment approved but not yet captured. Run 'capture' to capture.")
        elif result.get("status") == "CREATED":
            print("⏳ Order created but not yet paid by customer.")
        else:
            print(f"Status: {result.get('status')}")
    except PayPalError as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_list(args):
    """List all orders."""
    if not ORDERS_DIR.exists():
        print("No orders yet.")
        return

    orders = []
    for f in ORDERS_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            orders.append(data)
        except Exception:
            pass

    if not orders:
        print("No orders found.")
        return

    print(f"{'Order ID':<25} {'Status':<12} {'Amount':<12} {'Description':<30}")
    print("-" * 80)
    for o in orders:
        oid = o.get("order_id", "N/A")[:25]
        status = o.get("status", "UNKNOWN")[:12]
        amount = f"{o.get('amount', 0)} {o.get('currency', '')}"[:12]
        desc = (o.get("description", "") or "")[:30]
        print(f"{oid:<25} {status:<12} {amount:<12} {desc:<30}")

    print()
    print(f"Total: {len(orders)} orders")


def cmd_dashboard(args):
    """Show revenue dashboard."""
    if not ORDERS_DIR.exists():
        print("No orders yet. Run 'create' to create your first order.")
        return

    orders = []
    for f in ORDERS_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            orders.append(data)
        except Exception:
            pass

    total_revenue = 0
    pending_amount = 0
    completed_count = 0
    pending_count = 0

    for o in orders:
        amount = float(o.get("amount", 0))
        if o.get("status") == "COMPLETED":
            total_revenue += amount
            completed_count += 1
        else:
            pending_amount += amount
            pending_count += 1

    print("=" * 50)
    print("  AutoCorp PayPal Dashboard")
    print("=" * 50)
    print(f"  Total Revenue:    ${total_revenue:.2f}")
    print(f"  Pending Amount:   ${pending_amount:.2f}")
    print(f"  Completed Orders: {completed_count}")
    print(f"  Pending Orders:   {pending_count}")
    print(f"  Total Orders:     {len(orders)}")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        prog="autocorp-paypal",
        description="AutoCorp PayPal CLI - Collect PayPal payments from the command line",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init
    p_init = subparsers.add_parser("init", help="Initialize credentials")
    p_init.add_argument("--client-id", required=True, help="PayPal Client ID")
    p_init.add_argument("--client-secret", required=True, help="PayPal Client Secret")
    p_init.add_argument("--sandbox", action="store_true", help="Use sandbox mode")
    p_init.set_defaults(func=cmd_init)

    # create
    p_create = subparsers.add_parser("create", help="Create a payment order")
    p_create.add_argument("--amount", required=True, help="Amount (e.g., 50.00)")
    p_create.add_argument("--currency", default="USD", help="Currency (default: USD)")
    p_create.add_argument("--description", required=True, help="Payment description")
    p_create.set_defaults(func=cmd_create)

    # check
    p_check = subparsers.add_parser("check", help="Check order status")
    p_check.add_argument("order_id", help="PayPal Order ID")
    p_check.set_defaults(func=cmd_check)

    # list
    p_list = subparsers.add_parser("list", help="List all orders")
    p_list.set_defaults(func=cmd_list)

    # dashboard
    p_dash = subparsers.add_parser("dashboard", help="Show revenue dashboard")
    p_dash.set_defaults(func=cmd_dashboard)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
