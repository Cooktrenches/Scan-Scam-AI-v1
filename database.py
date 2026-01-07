"""
Database for storing scan history and statistics
"""
import sqlite3
import json
from datetime import datetime
from threading import Lock
import os

# Use /data directory on Render (persistent disk), otherwise use current directory
DATA_DIR = os.getenv("DATA_DIR", ".")
DB_FILE = os.path.join(DATA_DIR, "scans.db")

class ScanDatabase:
    def __init__(self):
        self.lock = Lock()
        self._init_db()

    def _init_db(self):
        """Initialize database with tables"""
        with self.lock:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            # Create scans table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    token_address TEXT NOT NULL,
                    token_name TEXT,
                    token_symbol TEXT,
                    risk_score INTEGER,
                    risk_level TEXT,
                    ai_score INTEGER,
                    source TEXT NOT NULL,
                    user_agent TEXT,
                    ip_address TEXT
                )
            ''')

            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp ON scans(timestamp)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_token ON scans(token_address)
            ''')

            conn.commit()
            conn.close()

    def add_scan(self, token_address, token_name=None, token_symbol=None,
                 risk_score=None, risk_level=None, ai_score=None,
                 source="web", user_agent=None, ip_address=None):
        """Add a scan to the database"""
        with self.lock:
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO scans
                    (timestamp, token_address, token_name, token_symbol,
                     risk_score, risk_level, ai_score, source, user_agent, ip_address)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    token_address,
                    token_name,
                    token_symbol,
                    risk_score,
                    risk_level,
                    ai_score,
                    source,
                    user_agent,
                    ip_address
                ))

                conn.commit()
                scan_id = cursor.lastrowid
                conn.close()

                return scan_id
            except Exception as e:
                print(f"Error adding scan to database: {e}")
                return None

    def get_total_scans(self):
        """Get total number of scans"""
        with self.lock:
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()

                cursor.execute('SELECT COUNT(*) FROM scans')
                total = cursor.fetchone()[0]

                conn.close()
                return total
            except Exception as e:
                print(f"Error getting total scans: {e}")
                return 0

    def get_scans_by_source(self):
        """Get scan counts by source"""
        with self.lock:
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT source, COUNT(*) as count
                    FROM scans
                    GROUP BY source
                ''')

                results = {row[0]: row[1] for row in cursor.fetchall()}
                conn.close()

                return results
            except Exception as e:
                print(f"Error getting scans by source: {e}")
                return {}

    def get_recent_scans(self, limit=10):
        """Get recent scans"""
        with self.lock:
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT timestamp, token_address, token_name, token_symbol,
                           risk_score, risk_level, ai_score, source
                    FROM scans
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))

                scans = []
                for row in cursor.fetchall():
                    scans.append({
                        'timestamp': row[0],
                        'token_address': row[1],
                        'token_name': row[2],
                        'token_symbol': row[3],
                        'risk_score': row[4],
                        'risk_level': row[5],
                        'ai_score': row[6],
                        'source': row[7]
                    })

                conn.close()
                return scans
            except Exception as e:
                print(f"Error getting recent scans: {e}")
                return []

    def get_stats(self):
        """Get comprehensive statistics"""
        with self.lock:
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()

                # Total scans
                cursor.execute('SELECT COUNT(*) FROM scans')
                total_scans = cursor.fetchone()[0]

                # Scans by source
                cursor.execute('''
                    SELECT source, COUNT(*) as count
                    FROM scans
                    GROUP BY source
                ''')
                by_source = {row[0]: row[1] for row in cursor.fetchall()}

                # Scans by risk level
                cursor.execute('''
                    SELECT risk_level, COUNT(*) as count
                    FROM scans
                    WHERE risk_level IS NOT NULL
                    GROUP BY risk_level
                ''')
                by_risk = {row[0]: row[1] for row in cursor.fetchall()}

                # Most scanned tokens
                cursor.execute('''
                    SELECT token_address, token_name, token_symbol, COUNT(*) as count
                    FROM scans
                    GROUP BY token_address
                    ORDER BY count DESC
                    LIMIT 10
                ''')
                top_tokens = []
                for row in cursor.fetchall():
                    top_tokens.append({
                        'address': row[0],
                        'name': row[1],
                        'symbol': row[2],
                        'scan_count': row[3]
                    })

                conn.close()

                return {
                    'total_scans': total_scans,
                    'by_source': by_source,
                    'by_risk_level': by_risk,
                    'top_tokens': top_tokens
                }
            except Exception as e:
                print(f"Error getting stats: {e}")
                return {
                    'total_scans': 0,
                    'by_source': {},
                    'by_risk_level': {},
                    'top_tokens': []
                }

    def check_if_scanned(self, token_address):
        """Check if a token has been scanned before"""
        with self.lock:
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT COUNT(*) FROM scans
                    WHERE token_address = ?
                ''', (token_address,))

                count = cursor.fetchone()[0]
                conn.close()

                return count > 0
            except Exception as e:
                print(f"Error checking if scanned: {e}")
                return False

# Global database instance
db = ScanDatabase()
