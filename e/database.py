import sqlite3
from datetime import datetime

class Database:
    def get_monthly_stats_by_client_for_month(self, year=None, month=None):
        """月ごとの取引先別統計を取得する
        
        Args:
            year: 対象年
            month: 対象月
        
        Returns:
            月ごとの取引先別統計データ
        """
        # デフォルトは現在の年月
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
            
        # SQL実行
        try:
            cursor = self.conn.cursor()
            query = """
                SELECT 
                    c.id AS client_id,
                    c.name AS client_name, 
                    COUNT(p.id) AS project_count,
                    SUM(p.amount) AS total_amount
                FROM 
                    projects p
                JOIN 
                    clients c ON p.client_id = c.id
                WHERE 
                    strftime('%Y', p.date) = ? 
                    AND strftime('%m', p.date) = ?
                GROUP BY 
                    c.id, c.name
                ORDER BY 
                    total_amount DESC
            """
            # 月を2桁にフォーマット
            month_str = f"{month:02d}"
            cursor.execute(query, (str(year), month_str))
            results = cursor.fetchall()
            return results
        except sqlite3.Error as e:
            print(f"データベースエラー: {e}")
            return []
    
    def get_monthly_stats_by_service_for_month(self, year=None, month=None):
        """月ごとのサービス別統計を取得する
        
        Args:
            year: 対象年
            month: 対象月
        
        Returns:
            月ごとのサービス別統計データ
        """
        # デフォルトは現在の年月
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month
        
        # SQL実行
        try:
            cursor = self.conn.cursor()
            query = """
                SELECT 
                    s.id AS service_id,
                    s.name AS service_name, 
                    COUNT(p.id) AS project_count,
                    SUM(p.amount) AS total_amount
                FROM 
                    projects p
                JOIN 
                    services s ON p.service_id = s.id
                WHERE 
                    strftime('%Y', p.date) = ? 
                    AND strftime('%m', p.date) = ?
                GROUP BY 
                    s.id, s.name
                ORDER BY 
                    total_amount DESC
            """
            # 月を2桁にフォーマット
            month_str = f"{month:02d}"
            cursor.execute(query, (str(year), month_str))
            results = cursor.fetchall()
            return results
        except sqlite3.Error as e:
            print(f"データベースエラー: {e}")
            return [] 
