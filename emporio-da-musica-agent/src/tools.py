
import pandas as pd

from src.data_loader import load_data


# Load the store datasets
DATASETS = load_data()

products = DATASETS["products"]
customers = DATASETS["customers"]
orders = DATASETS["orders"]
promotions = DATASETS["promotions"]


def clean_value(value):
    """Convert pandas values into safe Python values."""
    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        return value.item()

    return value


def search_products(query="", max_price=None, category=None):
    """
    Search available products by name, description or category.
    Only active products with available stock are returned.
    """

    df = products.copy()

    df = df[
        (df["status"].astype(str).str.lower() == "active")
        & (df["stock_quantity"] > 0)
    ]

    if query:
        search_text = query.lower()

        searchable_columns = [
            "name",
            "description",
            "category_name"
        ]

        mask = pd.Series(False, index=df.index)

        for column in searchable_columns:
            if column in df.columns:
                mask |= df[column].astype(str).str.lower().str.contains(
                    search_text,
                    na=False
                )

        df = df[mask]

    if max_price is not None:
        df = df[df["price_brl"] <= float(max_price)]

    if category:
        df = df[
            df["category_name"].astype(str).str.lower().str.contains(
                category.lower(),
                na=False
            )
        ]

    results = []

    for _, row in df.head(10).iterrows():
        results.append({
            "product_id": clean_value(row["product_id"]),
            "name": clean_value(row["name"]),
            "category": clean_value(row.get("category_name")),
            "price_brl": clean_value(row["price_brl"]),
            "stock_quantity": clean_value(row["stock_quantity"]),
            "description": clean_value(row["description"])
        })

    return {
        "total_found": len(df),
        "products": results
    }


def get_product_details(product_id):
    """Retrieve details about a specific product."""

    result = products[
        products["product_id"].astype(str) == str(product_id)
    ]

    if result.empty:
        return {"error": "Product not found."}

    row = result.iloc[0]

    return {
        "product_id": clean_value(row["product_id"]),
        "name": clean_value(row["name"]),
        "category": clean_value(row.get("category_name")),
        "price_brl": clean_value(row["price_brl"]),
        "stock_quantity": clean_value(row["stock_quantity"]),
        "status": clean_value(row["status"]),
        "description": clean_value(row["description"]),
        "specifications": clean_value(row.get("specs"))
    }


def get_active_promotions():
    """Retrieve active promotions and their associated products."""

    active = promotions[
        promotions["is_active"] == True
    ].copy()

    result = active.merge(
        products[["product_id", "name", "price_brl"]],
        on="product_id",
        how="left"
    )

    promotions_list = []

    for _, row in result.iterrows():
        promotions_list.append({
            "promotion_id": clean_value(row["promotion_id"]),
            "product_id": clean_value(row["product_id"]),
            "product_name": clean_value(row["name"]),
            "original_price_brl": clean_value(row["price_brl"]),
            "discount_percent": clean_value(row["discount_percent"]),
            "description": clean_value(row["description"])
        })

    return {
        "total_promotions": len(promotions_list),
        "promotions": promotions_list
    }


def get_order_status(order_id, customer_email):
    """
    Check an order using its ID and the customer's registered email.
    Does not expose unnecessary customer information.
    """

    order = orders[
        orders["order_id"].astype(str) == str(order_id)
    ]

    if order.empty:
        return {"error": "Order not found."}

    order_row = order.iloc[0]

    customer = customers[
        (customers["customer_id"].astype(str)
         == str(order_row["customer_id"]))
        &
        (customers["email"].astype(str).str.lower()
         == customer_email.strip().lower())
    ]

    if customer.empty:
        return {
            "error": "The order ID and email could not be verified."
        }

    return {
        "order_id": clean_value(order_row["order_id"]),
        "status": clean_value(order_row["status"]),
        "order_date": clean_value(order_row["order_date"]),
        "total_brl": clean_value(order_row["total_brl"]),
        "payment_method": clean_value(order_row["payment_method"]),
        "tracking_code": clean_value(order_row["tracking_code"]),
        "estimated_delivery": clean_value(
            order_row["estimated_delivery"]
        ),
        "notes": clean_value(order_row["notes"])
    }


if __name__ == "__main__":
    print("=" * 50)
    print("EMPORIO DA MUSICA - TOOLS TEST")
    print("=" * 50)

    print("\n1. PRODUCT SEARCH")
    print(search_products(query="guitar"))

    print("\n2. ACTIVE PROMOTIONS")
    print(get_active_promotions())

    print("\nTools loaded successfully!")
