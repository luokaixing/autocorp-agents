"""AutoCorp PayPal CLI — A standalone PayPal payment collection CLI tool

A minimal command-line tool for collecting PayPal payments without building a web app.
Built for solo creators, freelancers, and small AI companies that need to accept PayPal
payments without setting up a full e-commerce site.

Features:
- Create payment orders via CLI
- Check order status and capture payments
- List all orders (pending / completed)
- Sync completed payments to a YAML ledger
- Works with PayPal Live and Sandbox

Usage:
    # Initialize (one-time setup)
    autocorp-paypal init --client-id YOUR_ID --client-secret YOUR_SECRET

    # Create a payment order
    autocorp-paypal create --amount 50 --currency USD --description "Consulting"

    # Check order status
    autocorp-paypal check <order_id>

    # List all orders
    autocorp-paypal list

    # Show dashboard (total revenue, pending, completed)
    autocorp-paypal dashboard

License: MIT
Author: AutoCorp Research Desk
"""
__version__ = "0.1.0"
__author__ = "AutoCorp Research Desk"
__license__ = "MIT"
