from pathlib import Path
import pandas as pd


# =====================================================
# PROJECT CONFIGURATION
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


# Expected columns for each dataset
REQUIRED_COLUMNS = {
    "categories": [
        "category_id",
        "name",
        "description"
    ],

    "customers": [
        "customer_id",
        "name",
        "phone",
        "email",
        "city"
    ],

    "order_items": [
        "order_id",
        "quantity",
        "product_id"
    ],

    "orders": [
        "order_id",
        "customer_id",
        "order_date",
        "status",
        "total_brl",
        "payment_method",
        "tracking_code",
        "estimated_delivery",
        "notes"
    ],

    "products": [
        "product_id",
        "price_brl",
        "name",
        "category_id",
        "description",
        "stock_quantity",
        "status",
        "specs",
        "created_at"
    ],

    "promotions": [
        "promotion_id",
        "product_id",
        "discount_percent",
        "description",
        "is_active"
    ]
}


# =====================================================
# CSV LOADING AND VALIDATION
# =====================================================

def load_csv(filename: str, source_filename: str = None) -> pd.DataFrame:

    source_filename = source_filename or filename

    file_path = DATA_DIR / f"{source_filename}.csv"

    # Check if file exists
    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {file_path}"
        )

    # Check if file is empty
    if file_path.stat().st_size == 0:
        raise ValueError(
            f"Dataset is empty: {source_filename}.csv"
        )

    try:
        df = pd.read_csv(
            file_path,
            encoding="utf-8-sig"
        )

    except pd.errors.EmptyDataError:
        raise ValueError(
            f"No columns found in {source_filename}.csv. "
            "Check the original file."
        )

    except pd.errors.ParserError as error:
        raise ValueError(
            f"Invalid CSV format in {source_filename}.csv: {error}"
        )

    # Validate required columns
    required = REQUIRED_COLUMNS[filename]

    missing_columns = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns in {source_filename}.csv: "
            f"{missing_columns}"
        )

    return df


# =====================================================
# DATA CLEANING
# =====================================================

def clean_data(data: dict) -> dict:

    products = data["products"]
    orders = data["orders"]
    promotions = data["promotions"]

    # Convert numeric values
    products["price_brl"] = pd.to_numeric(
        products["price_brl"],
        errors="coerce"
    )

    products["stock_quantity"] = pd.to_numeric(
        products["stock_quantity"],
        errors="coerce"
    ).fillna(0)

    orders["total_brl"] = pd.to_numeric(
        orders["total_brl"],
        errors="coerce"
    )

    promotions["discount_percent"] = pd.to_numeric(
        promotions["discount_percent"],
        errors="coerce"
    )

    # Convert dates
    orders["order_date"] = pd.to_datetime(
        orders["order_date"],
        errors="coerce"
    )

    orders["estimated_delivery"] = pd.to_datetime(
        orders["estimated_delivery"],
        errors="coerce"
    )

    products["created_at"] = pd.to_datetime(
        products["created_at"],
        errors="coerce"
    )

    # Normalize promotion status
    promotions["is_active"] = (
        pd.to_numeric(
            promotions["is_active"],
            errors="coerce"
        ).fillna(0).eq(1)
    )

    return data


# =====================================================
# LOAD ALL DATASETS
# =====================================================

def load_data() -> dict:

    print("\nLoading Emporio da Musica datasets...")

    data = {}

    for filename in REQUIRED_COLUMNS:

        source_filename = filename

        # Use anonymized customer data when available
        if filename == "customers":

            public_customers = DATA_DIR / "customers_public.csv"

            if public_customers.exists():
                source_filename = "customers_public"

        print(f"Loading {source_filename}.csv...")

        data[filename] = load_csv(
            filename,
            source_filename
        )

    # Clean datasets
    data = clean_data(data)

    # Connect products with categories
    data["products"] = data["products"].merge(
        data["categories"][
            ["category_id", "name"]
        ].rename(
            columns={"name": "category_name"}
        ),
        on="category_id",
        how="left",
        validate="many_to_one"
    )

    print("\nAll datasets loaded successfully!")

    return data


# =====================================================
# PRODUCT SEARCH
# =====================================================

def get_available_products(
    data: dict,
    max_price: float = None,
    category: str = None
) -> pd.DataFrame:

    products = data["products"].copy()

    # Only active products with available stock
    products = products[
        (products["status"] == "active") &
        (products["stock_quantity"] > 0) &
        (products["price_brl"].notna())
    ]

    # Filter by maximum price
    if max_price is not None:

        products = products[
            products["price_brl"] <= max_price
        ]

    # Filter by category
    if category:

        products = products[
            products["category_name"].str.contains(
                category,
                case=False,
                na=False
            )
        ]

    return products.sort_values(
        by="price_brl"
    )


# =====================================================
# PRODUCT PRICE SEARCH
# =====================================================

def search_product(
    data: dict,
    product_name: str
) -> pd.DataFrame:

    products = data["products"]

    result = products[
        products["name"].str.contains(
            product_name,
            case=False,
            na=False
        )
    ]

    return result


# =====================================================
# ACTIVE PROMOTIONS
# =====================================================

def get_active_promotions(data: dict) -> pd.DataFrame:

    return data["promotions"][
        data["promotions"]["is_active"]
    ].copy()


# =====================================================
# ORDER SEARCH
# =====================================================

def get_order(
    data: dict,
    order_id: int
) -> pd.DataFrame:

    orders = data["orders"]

    return orders[
        orders["order_id"] == order_id
    ].copy()


# =====================================================
# MAIN EXECUTION
# =====================================================

if __name__ == "__main__":

    try:

        datasets = load_data()

        print("\n" + "=" * 50)
        print("EMPORIO DA MUSICA - DATA LOADER")
        print("=" * 50)

        # Dataset summary
        for name, df in datasets.items():

            print(
                f"{name}: {len(df)} records"
            )

        # Available products
        print("\nAVAILABLE PRODUCTS")

        available = get_available_products(
            datasets
        )

        print(
            available[
                [
                    "name",
                    "category_name",
                    "price_brl",
                    "stock_quantity"
                ]
            ].head(10).to_string(index=False)
        )

        # Active promotions
        print("\nACTIVE PROMOTIONS")

        promotions = get_active_promotions(
            datasets
        )

        print(
            promotions.to_string(index=False)
            if not promotions.empty
            else "No active promotions found."
        )

        print("\n" + "=" * 50)
        print("DATA LOADING COMPLETED SUCCESSFULLY!")
        print("=" * 50)

    except (FileNotFoundError, ValueError, KeyError) as error:

        print("\nDATA LOADING ERROR:")
        print(error)