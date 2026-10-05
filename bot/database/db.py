import json
import secrets
from pathlib import Path
from datetime import datetime, timezone

from config import DB_ENABLED, DATABASE_URL

_pool = None
DATA_FILE = Path("data/shop.json")


def _load():
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        _save({"orders": [], "keys": {}, "next_order_id": 1})
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"orders": [], "keys": {}, "next_order_id": 1}


def _save(data):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


async def init_db():
    global _pool

    if not DB_ENABLED:
        _load()
        return

    if not DATABASE_URL:
        raise RuntimeError("DB_ENABLED=true, но DATABASE_URL не задана")

    import asyncpg

    _pool = await asyncpg.create_pool(
        dsn=DATABASE_URL,
        min_size=1,
        max_size=5,
    )

    async with _pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id BIGSERIAL PRIMARY KEY,
                telegram_id BIGINT NOT NULL,
                username VARCHAR(255),
                product VARCHAR(30) NOT NULL,
                amount NUMERIC(10,2) NOT NULL,
                status VARCHAR(40) NOT NULL,
                payment_id VARCHAR(100) UNIQUE,
                full_name VARCHAR(255),
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paid_at TIMESTAMP NULL,
                details_received_at TIMESTAMP NULL
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS activation_codes (
                id BIGSERIAL PRIMARY KEY,
                code VARCHAR(10) UNIQUE NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'available',
                order_id BIGINT NULL,
                buyer_telegram_id BIGINT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                issued_at TIMESTAMP NULL,
                activated_at TIMESTAMP NULL
            )
        """)

        # Used by the game bot to remember who has activated access.
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS activated_users (
                telegram_id BIGINT PRIMARY KEY,
                activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


async def close_db():
    global _pool

    if _pool:
        await _pool.close()
        _pool = None


async def create_order(telegram_id, username, product, amount):
    if DB_ENABLED:
        async with _pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO orders
                    (telegram_id, username, product, amount, status)
                VALUES ($1, $2, $3, $4, 'pending')
                RETURNING id
                """,
                telegram_id,
                username,
                product,
                amount,
            )
            return row["id"]

    data = _load()
    oid = data["next_order_id"]
    data["next_order_id"] += 1
    data["orders"].append({
        "id": oid,
        "telegram_id": telegram_id,
        "username": username,
        "product": product,
        "amount": amount,
        "status": "pending",
        "payment_id": None,
        "full_name": None,
        "address": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "paid_at": None,
        "details_received_at": None,
    })
    _save(data)
    return oid


async def set_payment_id(order_id, payment_id):
    if DB_ENABLED:
        async with _pool.acquire() as conn:
            await conn.execute(
                "UPDATE orders SET payment_id=$1 WHERE id=$2",
                payment_id,
                order_id,
            )
        return

    data = _load()
    for o in data["orders"]:
        if o["id"] == order_id:
            o["payment_id"] = payment_id
    _save(data)


async def get_order(order_id):
    if DB_ENABLED:
        async with _pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM orders WHERE id=$1",
                order_id,
            )

    return next(
        (o for o in _load()["orders"] if o["id"] == order_id),
        None,
    )


async def get_order_by_payment(payment_id):
    if DB_ENABLED:
        async with _pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM orders WHERE payment_id=$1",
                payment_id,
            )

    return next(
        (o for o in _load()["orders"]
         if o.get("payment_id") == payment_id),
        None,
    )


async def get_latest_paid_paper_order(telegram_id):
    if DB_ENABLED:
        async with _pool.acquire() as conn:
            return await conn.fetchrow(
                """
                SELECT *
                FROM orders
                WHERE telegram_id=$1
                  AND product='paper'
                  AND status='paid'
                ORDER BY id DESC
                LIMIT 1
                """,
                telegram_id,
            )

    orders = [
        o for o in _load()["orders"]
        if o["telegram_id"] == telegram_id
        and o["product"] == "paper"
        and o["status"] == "paid"
    ]
    return orders[-1] if orders else None


async def mark_paid(order_id):
    if DB_ENABLED:
        async with _pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE orders
                SET status='paid', paid_at=CURRENT_TIMESTAMP
                WHERE id=$1 AND status='pending'
                """,
                order_id,
            )
        return

    data = _load()
    for o in data["orders"]:
        if o["id"] == order_id:
            o["status"] = "paid"
            o["paid_at"] = datetime.now(timezone.utc).isoformat()
    _save(data)


async def set_order_details(order_id, full_name, address):
    if DB_ENABLED:
        async with _pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE orders
                SET full_name=$1,
                    address=$2,
                    status='details_received',
                    details_received_at=CURRENT_TIMESTAMP
                WHERE id=$3
                """,
                full_name,
                address,
                order_id,
            )
        return

    data = _load()
    for o in data["orders"]:
        if o["id"] == order_id:
            o["full_name"] = full_name
            o["address"] = address
            o["status"] = "details_received"
            o["details_received_at"] = datetime.now(timezone.utc).isoformat()
    _save(data)


async def get_orders(limit=20):
    if DB_ENABLED:
        async with _pool.acquire() as conn:
            return await conn.fetch(
                "SELECT * FROM orders ORDER BY id DESC LIMIT $1",
                limit,
            )

    return list(reversed(_load()["orders"][-limit:]))


async def get_sales_stats():
    if DB_ENABLED:
        async with _pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT COUNT(*) AS count,
                       COALESCE(SUM(amount), 0) AS total
                FROM orders
                WHERE status IN ('paid', 'details_received')
                """
            )
            return int(row["count"]), float(row["total"])

    orders = [
        o for o in _load()["orders"]
        if o["status"] in ("paid", "details_received")
    ]
    return len(orders), sum(float(o["amount"]) for o in orders)


async def generate_keys(count=10):
    created = []

    if DB_ENABLED:
        async with _pool.acquire() as conn:
            while len(created) < count:
                code = "".join(
                    str(secrets.randbelow(10))
                    for _ in range(10)
                )
                try:
                    await conn.execute(
                        """
                        INSERT INTO activation_codes(code, status)
                        VALUES($1, 'available')
                        """,
                        code,
                    )
                    created.append(code)
                except Exception:
                    # Collision: generate another code.
                    continue

        return created

    data = _load()

    while len(created) < count:
        code = "".join(
            str(secrets.randbelow(10))
            for _ in range(10)
        )

        if code not in data["keys"]:
            data["keys"][code] = {
                "status": "available",
                "order_id": None,
                "buyer_telegram_id": None,
            }
            created.append(code)

    _save(data)
    return created


async def issue_key(order_id, buyer_telegram_id):
    if DB_ENABLED:
        async with _pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    SELECT id, code
                    FROM activation_codes
                    WHERE status='available'
                    ORDER BY id
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                    """
                )

                if not row:
                    # Generate a batch inside the same database.
                    for _ in range(20):
                        code = "".join(
                            str(secrets.randbelow(10))
                            for _ in range(10)
                        )
                        try:
                            await conn.execute(
                                """
                                INSERT INTO activation_codes(code, status)
                                VALUES($1, 'available')
                                """,
                                code,
                            )
                        except Exception:
                            continue

                    row = await conn.fetchrow(
                        """
                        SELECT id, code
                        FROM activation_codes
                        WHERE status='available'
                        ORDER BY id
                        FOR UPDATE SKIP LOCKED
                        LIMIT 1
                        """
                    )

                if not row:
                    raise RuntimeError("No activation keys available")

                updated = await conn.fetchrow(
                    """
                    UPDATE activation_codes
                    SET status='issued',
                        order_id=$1,
                        buyer_telegram_id=$2,
                        issued_at=CURRENT_TIMESTAMP
                    WHERE id=$3 AND status='available'
                    RETURNING code
                    """,
                    order_id,
                    buyer_telegram_id,
                    row["id"],
                )

                if not updated:
                    raise RuntimeError("Activation key was already issued")

                return updated["code"]

    data = _load()
    code = next(
        (k for k, v in data["keys"].items()
         if v["status"] == "available"),
        None,
    )

    if not code:
        await generate_keys(20)
        data = _load()
        code = next(
            k for k, v in data["keys"].items()
            if v["status"] == "available"
        )

    data["keys"][code].update({
        "status": "issued",
        "order_id": order_id,
        "buyer_telegram_id": buyer_telegram_id,
    })
    _save(data)
    return code


async def get_key_stats():
    if DB_ENABLED:
        async with _pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT status, COUNT(*) AS count
                FROM activation_codes
                GROUP BY status
                """
            )
            return {r["status"]: int(r["count"]) for r in rows}

    result = {}
    for v in _load()["keys"].values():
        result[v["status"]] = result.get(v["status"], 0) + 1
    return result
