import psycopg2
import uuid
from datetime import datetime
from psycopg2.extras import RealDictCursor

# --- Database Credentials ---
DB_NAME = "financial_portfolio_db"
DB_USER = "postgres"
DB_PASSWORD = "bijujohn"
DB_HOST = "localhost"
DB_PORT = "5432"

class DatabaseManager:
    def __init__(self):
        self.conn = self._connect()
        if self.conn:
            self._create_tables()

    def _connect(self):
        """Establishes a connection to the PostgreSQL database."""
        try:
            conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT
            )
            return conn
        except psycopg2.Error as e:
            print(f"Error connecting to the database: {e}")
            return None

    def _create_tables(self):
        """Creates the necessary database tables if they do not exist."""
        if self.conn:
            with self.conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id VARCHAR(255) PRIMARY KEY,
                        name VARCHAR(255)
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS assets (
                        asset_id VARCHAR(255) PRIMARY KEY,
                        user_id VARCHAR(255) REFERENCES users(user_id),
                        ticker VARCHAR(50) NOT NULL,
                        purchase_date DATE NOT NULL,
                        shares DECIMAL(15, 6) NOT NULL,
                        cost_basis DECIMAL(15, 2) NOT NULL,
                        asset_class VARCHAR(50) NOT NULL
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        transaction_id VARCHAR(255) PRIMARY KEY,
                        asset_id VARCHAR(255) REFERENCES assets(asset_id),
                        transaction_date TIMESTAMP NOT NULL,
                        transaction_type VARCHAR(50) NOT NULL,
                        quantity DECIMAL(15, 6) NOT NULL,
                        price DECIMAL(15, 2) NOT NULL,
                        total_amount DECIMAL(15, 2) NOT NULL
                    );
                """)
                self.conn.commit()
                self._ensure_single_user()

    def _ensure_single_user(self):
        """Inserts a default user if one doesn't exist."""
        if self.conn:
            with self.conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM users;")
                if cur.fetchone()[0] == 0:
                    user_id = "single_user_123"
                    cur.execute("INSERT INTO users (user_id, name) VALUES (%s, %s);", (user_id, "User Portfolio"))
                    self.conn.commit()

    # --- CRUD for Assets ---
    def create_asset(self, ticker, purchase_date, shares, cost_basis, asset_class):
        """Adds a new asset to the portfolio."""
        if self.conn:
            with self.conn.cursor() as cur:
                asset_id = str(uuid.uuid4())
                user_id = "single_user_123"
                cur.execute("""
                    INSERT INTO assets (asset_id, user_id, ticker, purchase_date, shares, cost_basis, asset_class)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                """, (asset_id, user_id, ticker, purchase_date, shares, cost_basis, asset_class))
                self.conn.commit()
                return True
        return False

    def read_assets(self):
        """Fetches all assets from the database."""
        if self.conn:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM assets;")
                return cur.fetchall()
        return []

    def update_asset(self, asset_id, shares, cost_basis):
        """Updates an existing asset's shares and cost basis."""
        if self.conn:
            with self.conn.cursor() as cur:
                cur.execute("""
                    UPDATE assets SET shares = %s, cost_basis = %s WHERE asset_id = %s;
                """, (shares, cost_basis, asset_id))
                self.conn.commit()
                return cur.rowcount > 0
        return False

    def delete_asset(self, asset_id):
        """Deletes an asset and all related transactions."""
        if self.conn:
            with self.conn.cursor() as cur:
                cur.execute("DELETE FROM transactions WHERE asset_id = %s;", (asset_id,))
                cur.execute("DELETE FROM assets WHERE asset_id = %s;", (asset_id,))
                self.conn.commit()
                return cur.rowcount > 0
        return False

    # --- CRUD for Transactions ---
    def create_transaction(self, asset_id, transaction_type, quantity, price, total_amount):
        """Logs a new transaction for an asset."""
        if self.conn:
            with self.conn.cursor() as cur:
                transaction_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO transactions (transaction_id, asset_id, transaction_date, transaction_type, quantity, price, total_amount)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                """, (transaction_id, asset_id, datetime.now(), transaction_type, quantity, price, total_amount))
                self.conn.commit()
                return True
        return False

    def read_transactions_by_asset(self, asset_id):
        """Fetches transactions for a specific asset."""
        if self.conn:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM transactions WHERE asset_id = %s ORDER BY transaction_date DESC;", (asset_id,))
                return cur.fetchall()
        return []

    # --- Reporting and Aggregation ---
    def get_portfolio_summary(self):
        """Calculates total portfolio value and asset class breakdown."""
        if self.conn:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT COUNT(DISTINCT ticker) as total_assets FROM assets;")
                total_assets = cur.fetchone()['total_assets'] or 0

                cur.execute("SELECT COALESCE(SUM(cost_basis), 0) as total_cost FROM assets;")
                total_cost = cur.fetchone()['total_cost'] or 0

                # Convert total_cost to float for calculations
                total_cost_float = float(total_cost)

                current_value = total_cost_float * 1.05
                gain_loss = current_value - total_cost_float
                
                cur.execute("SELECT asset_class, COALESCE(SUM(cost_basis), 0) as total_value FROM assets GROUP BY asset_class;")
                breakdown = cur.fetchall()

                return {
                    "total_assets": total_assets,
                    "total_cost": total_cost,
                    "current_value": current_value,
                    "gain_loss": gain_loss,
                    "gain_loss_percent": (gain_loss / total_cost_float) * 100 if total_cost_float > 0 else 0,
                    "breakdown": breakdown
                }
        return {}