"""PayPal Live 配置验证测试"""
import json
from pathlib import Path
from engine.payments.paypal import PayPalClient, PayPalError

ORDER_ID = "6H707311BH815501H"

print("[Test 4a] 检查 pending 订单文件")
client = PayPalClient(sandbox=False)
pending_path = client.pending_dir / f"{ORDER_ID}.json"
if pending_path.exists():
    with pending_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"  文件: {pending_path}")
    print(f"  order_id: {data.get('order_id')}")
    print(f"  amount: {data.get('amount')} {data.get('currency')}")
    print(f"  status: {data.get('status')}")
    print(f"  sandbox: {data.get('sandbox')}")
    print(f"  created_at: {data.get('created_at')}")
    print("[Test 4a] OK 订单文件已落盘")
else:
    print(f"[Test 4a] FAIL 订单文件不存在: {pending_path}")

print()
print("[Test 4b] 查询订单状态（check_order）")
try:
    result = client.check_order(ORDER_ID)
    print(f"  status: {result.get('status')}")
    print(f"  amount: {result.get('amount')} {result.get('currency')}")
    payer = result.get("payer_info", {})
    payer_id = payer.get("payer_id", "(none - unpaid)")
    payer_email = payer.get("email", "(none - unpaid)")
    print(f"  payer_id: {payer_id}")
    print(f"  payer_email: {payer_email}")
    print("[Test 4b] OK 查询订单成功（PayPal Live API 可读）")
except PayPalError as e:
    print(f"[Test 4b] FAIL: {e}")
except Exception as e:
    print(f"[Test 4b] FAIL: {type(e).__name__}: {e}")
