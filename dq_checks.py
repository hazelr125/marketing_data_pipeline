import sqlite3
from typing import Tuple, Optional, Union
from contextlib import closing

class DataQualityValidator:
    """Executes automated data quality validations against a SQLite database."""
    
    def __init__(self, db_path: str = "marketing_warehouse.db"):
        self.db_path = db_path
        self.passes = 0
        self.fails = 0

    def _log_result(self, passed: bool, message: str) -> None:
        """Formats and prints the check result."""
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {message}")
        if passed:
            self.passes += 1
        else:
            self.fails += 1

    def check_null_rate(self, cursor: sqlite3.Cursor, table: str, column: str, threshold: float) -> None:
        """Fails if the percentage of NULL values in a column exceeds the given threshold."""
        query = f"""
            SELECT 
                CAST(SUM(CASE WHEN {column} IS NULL THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) 
            FROM {table}
        """
        cursor.execute(query)
        result = cursor.fetchone()[0]
        null_rate = result if result is not None else 0.0
        
        passed = null_rate <= threshold
        self._log_result(passed, f"Null rate for {table}.{column} is {null_rate:.2%} (Threshold: <= {threshold:.2%})")

    def check_duplicate_pk(self, cursor: sqlite3.Cursor, table: str, column: str) -> None:
        """Fails if any duplicate values exist in a designated primary key column."""
        query = f"""
            SELECT {column}, COUNT(*) 
            FROM {table} 
            GROUP BY {column} 
            HAVING COUNT(*) > 1 
            LIMIT 1
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result:
            self._log_result(False, f"Duplicate PK found in {table}.{column} (Value '{result[0]}' occurs {result[1]} times)")
        else:
            self._log_result(True, f"No duplicates found in {table}.{column}")

    def check_referential_integrity(self, cursor: sqlite3.Cursor, child_table: str, child_fk: str, parent_table: str, parent_pk: str) -> None:
        """Fails if foreign key values in the child table do not exist in the parent table."""
        query = f"""
            SELECT COUNT(*) 
            FROM {child_table} 
            WHERE {child_fk} IS NOT NULL 
              AND {child_fk} NOT IN (SELECT {parent_pk} FROM {parent_table})
        """
        cursor.execute(query)
        orphans = cursor.fetchone()[0]
        
        if orphans > 0:
            self._log_result(False, f"Referential integrity failure: {orphans} orphaned records in {child_table}.{child_fk}")
        else:
            self._log_result(True, f"Referential integrity intact between {child_table}.{child_fk} and {parent_table}.{parent_pk}")

    def check_value_range(self, cursor: sqlite3.Cursor, table: str, column: str, min_val: Union[int, float, str] = None, max_val: Union[int, float, str] = None, is_date: bool = False) -> None:
        """Fails if any numeric or date values fall strictly outside the specified min/max bounds."""
        conditions = []
        if min_val is not None:
            val_str = f"'{min_val}'" if is_date else str(min_val)
            conditions.append(f"{column} < {val_str}")
        if max_val is not None:
            val_str = f"'{max_val}'" if is_date else str(max_val)
            conditions.append(f"{column} > {val_str}")
            
        if not conditions:
            return
            
        where_clause = " OR ".join(conditions)
        query = f"SELECT COUNT(*) FROM {table} WHERE {where_clause}"
        cursor.execute(query)
        violations = cursor.fetchone()[0]
        
        if violations > 0:
            self._log_result(False, f"Range violation: {violations} records out of bounds in {table}.{column}")
        else:
            self._log_result(True, f"All values within bounds for {table}.{column}")

    def run_suite(self):
        """Connects to the database, executes all tests, and outputs a summary."""
        print("Starting Data Quality Test Suite...\n")
        print("-" * 85)
        
        with closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            
            # 1. Primary Key Checks
            self.check_duplicate_pk(cursor, "raw_crm_customers", "customer_id")
            self.check_duplicate_pk(cursor, "raw_email_export", "email_send_id")
            self.check_duplicate_pk(cursor, "raw_web_analytics", "session_id")
            self.check_duplicate_pk(cursor, "campaign_performance", "campaign_name")
            
            # 2. Null Rate Checks
            self.check_null_rate(cursor, "raw_email_export", "opens", threshold=0.05)
            self.check_null_rate(cursor, "raw_email_export", "clicks", threshold=0.05)
            self.check_null_rate(cursor, "campaign_performance", "total_sends", threshold=0.00)
            
            # 3. Referential Integrity Checks
            self.check_referential_integrity(cursor, "raw_email_export", "customer_id", "raw_crm_customers", "customer_id")
            
            # 4. Value Range Checks (Metrics & Negatives)
            self.check_value_range(cursor, "raw_web_analytics", "pageviews", min_val=0)
            self.check_value_range(cursor, "campaign_performance", "open_rate", min_val=0.0, max_val=1.0)
            
            # 5. Value Range Checks (Stale Dates)
            self.check_value_range(cursor, "raw_email_export", "send_date", min_val="2024-01-01", is_date=True)
            
        print("-" * 85)
        print(f"Execution Summary: {self.passes + self.fails} Checks | {self.passes} Passed | {self.fails} Failed")

if __name__ == "__main__":
    validator = DataQualityValidator()
    validator.run_suite()
