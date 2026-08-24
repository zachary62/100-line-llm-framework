"""Database fixture — creates the sample shop.db the flow queries."""
import os, sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "shop.db")

def setup_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS customers;
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY, name TEXT, email TEXT, plan TEXT, signed_up DATE
        );
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY, customer_id INTEGER, product TEXT,
            amount REAL, status TEXT, ordered_at DATE,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );
        INSERT INTO customers VALUES
            (1,'Alice','alice@example.com','pro','2024-01-15'),
            (2,'Bob','bob@example.com','free','2024-03-22'),
            (3,'Carol','carol@example.com','pro','2024-02-10'),
            (4,'Dave','dave@example.com','enterprise','2024-01-05'),
            (5,'Eve','eve@example.com','free','2024-04-18');
        INSERT INTO orders VALUES
            (1,1,'Widget',29.99,'completed','2024-02-01'),
            (2,1,'Gadget',49.99,'completed','2024-03-15'),
            (3,2,'Widget',29.99,'refunded','2024-04-01'),
            (4,3,'Gadget',49.99,'completed','2024-02-20'),
            (5,3,'Gizmo',99.99,'completed','2024-03-10'),
            (6,4,'Gizmo',99.99,'completed','2024-01-20'),
            (7,4,'Widget',29.99,'completed','2024-02-15'),
            (8,4,'Gadget',49.99,'pending','2024-04-25'),
            (9,5,'Widget',29.99,'completed','2024-05-01');
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_db()
    print(f"Created {DB_PATH}")
