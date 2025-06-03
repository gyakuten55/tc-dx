import sqlite3
import os
import datetime
import hashlib
import secrets
from typing import List, Tuple, Dict, Any, Optional

class Database:
    def __init__(self, db_path: str = 'tc_management.db'):
        """データベース接続を初期化する"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()

    def connect(self) -> None:
        """データベースに接続する"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(f"データベースへの接続エラー: {e}")
            raise

    def close(self) -> None:
        """データベース接続を閉じる"""
        if self.conn:
            self.conn.close()

    def create_tables(self) -> None:
        """必要なテーブルを作成する"""
        # パスワードリセットフラグ - trueにするとパスワードをリセットして初期状態に戻す
        reset_passwords = True

        # 取引先テーブル
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            phone TEXT,
            email TEXT,
            note TEXT,
            has_drawings INTEGER DEFAULT 0,
            has_documents INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 作業員テーブル
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            phone TEXT,
            email TEXT,
            my_number TEXT,
            blood_type TEXT,
            emergency_contact TEXT,
            emergency_phone TEXT,
            emergency_address TEXT,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 既存のworkersテーブルに緊急連絡先住所フィールドを追加（存在しない場合のみ）
        try:
            self.cursor.execute('ALTER TABLE workers ADD COLUMN emergency_address TEXT')
        except sqlite3.OperationalError:
            # カラムが既に存在する場合は無視
            pass

        # サービスマスターテーブル
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # 案件テーブル - trouble_worker_idが確実に作成されるようにする
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            service_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            site_address TEXT,
            price REAL NOT NULL,
            labor_cost REAL DEFAULT 0,
            status TEXT DEFAULT '作業中',
            start_date DATE,
            end_date DATE,
            completion_date DATE,
            has_trouble INTEGER DEFAULT 0,
            trouble_worker_id INTEGER,
            has_photos INTEGER DEFAULT 0,
            photo_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id),
            FOREIGN KEY (service_id) REFERENCES services (id),
            FOREIGN KEY (trouble_worker_id) REFERENCES workers (id)
        )
        ''')

        # 業務指示書テーブル
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS work_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            order_number TEXT,
            creation_date DATE,
            work_type TEXT,
            manager_id INTEGER,
            creator_id INTEGER,
            site_name TEXT,
            site_address TEXT,
            management_tel TEXT,
            duty TEXT,
            start_date DATE,
            end_date DATE,
            arrival_time TEXT,
            scheduled_start TEXT,
            scheduled_end TEXT,
            actual_start TEXT,
            actual_end TEXT,
            work_content TEXT,
            contractor_company TEXT,
            contractor_manager TEXT,
            contact_number TEXT,
            signboard_name TEXT,
            arrival_number TEXT,
            arrival_manager TEXT,
            arrival_contact TEXT,
            completion_number TEXT,
            completion_manager TEXT,
            completion_contact TEXT,
            work_details TEXT,
            business_card INTEGER DEFAULT 0,
            vest INTEGER DEFAULT 0,
            digicam TEXT,
            has_report INTEGER DEFAULT 0,
            reports_count INTEGER DEFAULT 0,
            inspector TEXT,
            sampling_place TEXT,
            sampler TEXT,
            chlorine INTEGER DEFAULT 0,
            seal INTEGER DEFAULT 0,
            report_form INTEGER DEFAULT 0,
            worker1 TEXT,
            worker2 TEXT,
            worker3 TEXT,
            worker4 TEXT,
            slip INTEGER DEFAULT 0,
            bill INTEGER DEFAULT 0,
            report INTEGER DEFAULT 0,
            memo TEXT,
            has_water_quality INTEGER DEFAULT 1,
            water_quality_items TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id),
            FOREIGN KEY (manager_id) REFERENCES workers (id),
            FOREIGN KEY (creator_id) REFERENCES workers (id)
        )
        ''')

        # 案件と作業員の関連テーブル
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            worker_id INTEGER NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects (id),
            FOREIGN KEY (worker_id) REFERENCES workers (id),
            UNIQUE(project_id, worker_id)
        )
        ''')

        # 案件写真テーブル
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            photo_path TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
        ''')

        # 売上目標テーブル
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales_targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,  -- 0は年間目標、1-12は各月の目標
            target_amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(year, month)
        )
        ''')

        # パスワードテーブルの修正
        try:
            # パスワードリセットフラグがtrueの場合、既存のテーブルを削除
            if reset_passwords:
                print("パスワードテーブルをリセットします")
                self.cursor.execute("DROP TABLE IF EXISTS user_passwords")
                self.conn.commit()
                print("既存のパスワードデータを削除しました")

            # 既存のテーブルの存在確認
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_passwords'")
            table_exists = self.cursor.fetchone()

            # テーブルが存在しない場合、または最初の1回だけ実行する条件
            if not table_exists:
                print("パスワードテーブルを作成します")
                # 新しいテーブルを作成
                self.cursor.execute('''
                CREATE TABLE user_passwords (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    password TEXT NOT NULL,
                    salt TEXT,
                    user_level TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                self.conn.commit()
                print("パスワードテーブルを作成しました")

                # 初期パスワードデータの挿入
                print("初期ユーザーデータを作成します")
                # Master psw: 0526
                self.cursor.execute(
                    "INSERT INTO user_passwords (user_id, password, salt, user_level) VALUES (?, ?, ?, ?)",
                    ("0001", "0526", "", "admin")
                )
                # user1 psw: 002
                self.cursor.execute(
                    "INSERT INTO user_passwords (user_id, password, salt, user_level) VALUES (?, ?, ?, ?)",
                    ("0002", "002", "", "user")
                )
                # 以下のユーザーは削除
                # user2 psw: 003
                # self.cursor.execute(
                #     "INSERT INTO user_passwords (user_id, password, salt, user_level) VALUES (?, ?, ?, ?)",
                #     ("0003", "003", "", "user")
                # )
                # # user3 psw: 004
                # self.cursor.execute(
                #     "INSERT INTO user_passwords (user_id, password, salt, user_level) VALUES (?, ?, ?, ?)",
                #     ("0004", "004", "", "user")
                # )
                # # user4 psw: 005
                # self.cursor.execute(
                #     "INSERT INTO user_passwords (user_id, password, salt, user_level) VALUES (?, ?, ?, ?)",
                #     ("0005", "005", "", "user")
                # )
                self.conn.commit()
                print("2人のユーザーが作成されました")
            else:
                # テーブルが既に存在する場合は何もしない
                print("パスワードテーブルは既に存在します")

        except sqlite3.Error as e:
            print(f"パスワードテーブルの処理中にエラー: {e}")
            raise

    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """データをテーブルに挿入する"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        values = tuple(data.values())

        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        try:
            self.cursor.execute(query, values)
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"挿入エラー: {e}")
            self.conn.rollback()
            raise

    def update(self, table: str, data: Dict[str, Any], condition: str, values: Tuple) -> None:
        """テーブルのデータを更新する"""
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        all_values = tuple(data.values()) + values

        query = f"UPDATE {table} SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE {condition}"

        try:
            self.cursor.execute(query, all_values)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"更新エラー: {e}")
            self.conn.rollback()
            raise

    def delete(self, table: str, condition: str, values: Tuple) -> None:
        """テーブルからデータを削除する"""
        query = f"DELETE FROM {table} WHERE {condition}"

        try:
            self.cursor.execute(query, values)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"削除エラー: {e}")
            self.conn.rollback()
            raise

    def select(self, table: str, columns: str = "*", condition: str = "", values: Tuple = ()) -> List[Dict]:
        """テーブルからデータを選択する"""
        query = f"SELECT {columns} FROM {table}"
        if condition:
            query += f" WHERE {condition}"

        try:
            self.cursor.execute(query, values)
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"選択エラー: {e}")
            raise

    def execute_query(self, query: str, values: Tuple = ()) -> List[Dict]:
        """カスタムクエリを実行する"""
        try:
            self.cursor.execute(query, values)
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"クエリ実行エラー: {e}")
            raise

    # 特定のテーブルに関するメソッド
    def get_clients(self) -> List[Dict]:
        """すべての取引先を取得する"""
        return self.select('clients', condition="1 ORDER BY name")

    def get_workers(self) -> List[Dict]:
        """すべての作業員を取得する"""
        return self.select('workers', condition="1 ORDER BY name")

    def get_services(self) -> List[Dict]:
        """すべてのサービスを取得する"""
        return self.select('services', condition="1 ORDER BY name")

    def get_projects(self, condition: str = "", values: Tuple = (), sort_column: str = "created_at", sort_order: str = "DESC") -> List[Dict]:
        """案件を取得する"""
        query = """
        SELECT p.*, c.name as client_name, s.name as service_name,
               w.name as trouble_worker_name
        FROM projects p
        JOIN clients c ON p.client_id = c.id
        JOIN services s ON p.service_id = s.id
        LEFT JOIN workers w ON p.trouble_worker_id = w.id
        """

        if condition:
            query += f" WHERE {condition}"

        # ソートパラメータを安全に使用するためのリスト
        allowed_columns = ["created_at", "title", "price", "status", "start_date", "end_date", "completion_date"]
        allowed_orders = ["ASC", "DESC"]

        # パラメータの検証
        if sort_column not in allowed_columns:
            sort_column = "created_at"  # デフォルト値

        if sort_order not in allowed_orders:
            sort_order = "DESC"  # デフォルト値

        query += f" ORDER BY p.{sort_column} {sort_order}"

        return self.execute_query(query, values)

    def get_projects_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """日付範囲で案件を取得する"""
        condition = "(p.start_date BETWEEN ? AND ?) OR (p.end_date BETWEEN ? AND ?) OR (? BETWEEN p.start_date AND p.end_date) OR (? BETWEEN p.start_date AND p.end_date)"
        values = (start_date, end_date, start_date, end_date, start_date, end_date)
        return self.get_projects(condition, values)

    def get_project_workers(self, project_id: int) -> List[Dict]:
        """案件に関連する作業員を取得する"""
        query = """
        SELECT w.*
        FROM workers w
        JOIN project_workers pw ON w.id = pw.worker_id
        WHERE pw.project_id = ?
        """
        return self.execute_query(query, (project_id,))

    def add_project_worker(self, project_id: int, worker_id: int) -> None:
        """案件に作業員を追加する"""
        try:
            self.insert('project_workers', {
                'project_id': project_id,
                'worker_id': worker_id
            })
        except sqlite3.IntegrityError:
            # 既に存在する場合は無視
            pass

    def remove_project_worker(self, project_id: int, worker_id: int) -> None:
        """案件から作業員を削除する"""
        self.delete('project_workers', 'project_id = ? AND worker_id = ?', (project_id, worker_id))

    def get_monthly_stats_by_client(self, year: int = None) -> List[Dict]:
        """取引先ごとの月別統計を取得する"""
        if year is None:
            year = datetime.datetime.now().year

        query = """
        SELECT
            c.id as client_id,
            c.name as client_name,
            strftime('%m', COALESCE(p.completion_date, p.created_at)) as month,
            SUM(p.price) as total_amount,
            COUNT(p.id) as project_count
        FROM projects p
        JOIN clients c ON p.client_id = c.id
        WHERE strftime('%Y', COALESCE(p.completion_date, p.created_at)) = ?
        GROUP BY c.id, month
        ORDER BY c.name, month
        """

        return self.execute_query(query, (str(year),))

    def get_total_stats_by_client(self, year: int = None) -> List[Dict]:
        """取引先ごとの年間総計統計を取得する"""
        if year is None:
            year = datetime.datetime.now().year

        query = """
        SELECT
            c.id as client_id,
            c.name as client_name,
            SUM(p.price) as total_amount,
            COUNT(p.id) as project_count
        FROM projects p
        JOIN clients c ON p.client_id = c.id
        WHERE strftime('%Y', COALESCE(p.completion_date, p.created_at)) = ?
        GROUP BY c.id
        ORDER BY total_amount DESC
        """

        return self.execute_query(query, (str(year),))

    def get_total_stats_by_service(self, year: int = None) -> List[Dict]:
        """サービスごとの年間総計統計を取得する"""
        if year is None:
            year = datetime.datetime.now().year

        query = """
        SELECT
            s.id as service_id,
            s.name as service_name,
            SUM(p.price) as total_amount,
            COUNT(p.id) as project_count
        FROM projects p
        JOIN services s ON p.service_id = s.id
        WHERE strftime('%Y', COALESCE(p.completion_date, p.created_at)) = ?
        GROUP BY s.id
        ORDER BY total_amount DESC
        """

        return self.execute_query(query, (str(year),))

    def get_monthly_stats_by_client_for_month(self, year: int = None, month: int = None) -> List[Dict]:
        """特定の月の取引先ごとの統計を取得する"""
        if year is None:
            year = datetime.datetime.now().year
        if month is None:
            month = datetime.datetime.now().month

        month_str = f"{month:02d}"

        query = """
        SELECT
            c.id as client_id,
            c.name as client_name,
            SUM(p.price) as total_amount,
            COUNT(p.id) as project_count
        FROM projects p
        JOIN clients c ON p.client_id = c.id
        WHERE strftime('%Y', COALESCE(p.completion_date, p.created_at)) = ?
        AND strftime('%m', COALESCE(p.completion_date, p.created_at)) = ?
        GROUP BY c.id
        ORDER BY total_amount DESC
        """

        return self.execute_query(query, (str(year), month_str))

    def get_monthly_stats_by_service_for_month(self, year: int = None, month: int = None) -> List[Dict]:
        """指定月のサービス別統計を取得する"""
        if year is None:
            year = datetime.datetime.now().year

        if month is None:
            month = datetime.datetime.now().month

        month_str = f"{month:02d}"

        query = """
        SELECT
            s.id as service_id,
            s.name as service_name,
            SUM(p.price) as total_amount,
            COUNT(p.id) as project_count
        FROM projects p
        JOIN services s ON p.service_id = s.id
        WHERE strftime('%Y', COALESCE(p.completion_date, p.created_at)) = ?
          AND strftime('%m', COALESCE(p.completion_date, p.created_at)) = ?
        GROUP BY s.id
        ORDER BY total_amount DESC
        """

        return self.execute_query(query, (str(year), month_str))

    # プロジェクト写真関連のメソッド
    def add_project_photo(self, project_id: int, photo_path: str, description: str = "") -> int:
        """プロジェクトに写真を追加する"""
        photo_id = self.insert('project_photos', {
            'project_id': project_id,
            'photo_path': photo_path,
            'description': description
        })

        # 写真カウントを更新
        self.cursor.execute(
            "UPDATE projects SET has_photos = 1, photo_count = photo_count + 1 WHERE id = ?",
            (project_id,)
        )
        self.conn.commit()

        return photo_id

    def get_project_photos(self, project_id: int) -> List[Dict]:
        """プロジェクトの写真を取得する"""
        return self.select('project_photos', condition="project_id = ? ORDER BY created_at", values=(project_id,))

    def delete_project_photo(self, photo_id: int) -> None:
        """プロジェクトの写真を削除する"""
        # 写真情報を取得
        photo = self.select('project_photos', condition="id = ?", values=(photo_id,))
        if not photo:
            return

        project_id = photo[0]['project_id']

        # 写真を削除
        self.delete('project_photos', 'id = ?', (photo_id,))

        # 残りの写真数を取得
        remaining = self.select('project_photos', 'COUNT(*) as count', 'project_id = ?', (project_id,))
        count = remaining[0]['count'] if remaining else 0

        # プロジェクトの写真情報を更新
        has_photos = 1 if count > 0 else 0
        self.cursor.execute(
            "UPDATE projects SET has_photos = ?, photo_count = ? WHERE id = ?",
            (has_photos, count, project_id)
        )
        self.conn.commit()

    # パスワード関連のメソッド
    def hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """パスワードをハッシュ化する"""
        if salt is None:
            # ソルトが提供されていない場合は新しく生成
            salt = secrets.token_hex(16)

        # SHA-256を使用してパスワードとソルトを組み合わせてハッシュ化
        pw_hash = hashlib.sha256((password + salt).encode()).hexdigest()

        return pw_hash, salt

    def verify_password(self, user_id: str, password: str) -> bool:
        """パスワードを検証する"""
        # ユーザー情報を取得
        result = self.select('user_passwords', condition="user_id = ?", values=(user_id,))

        if not result:
            print(f"ユーザーID '{user_id}' は存在しません")
            return False

        stored_password = result[0]['password']
        print(f"検証中: 入力されたパスワード '{password}', 保存されているパスワード '{stored_password}'")

        # 直接比較チェック（短いパスワードのレガシーサポート）
        if stored_password == password:
            print("直接パスワード一致 - 認証成功")
            return True

        # ソルトを取得
        salt = result[0].get('salt', '')

        # ハッシュパスワードチェック（ソルトがある場合）
        if salt:
            input_hash, _ = self.hash_password(password, salt)
            is_valid = input_hash == stored_password
            print(f"ハッシュパスワードチェック: {'成功' if is_valid else '失敗'}")
            return is_valid

        # どちらの方法でも認証できない場合
        print("認証失敗")
        return False

    def update_password(self, user_id: str, new_password: str) -> bool:
        """パスワードを更新する（ハッシュ化あり）"""
        try:
            # 新しいパスワードをハッシュ化
            password_hash, salt = self.hash_password(new_password)

            # パスワードとソルトを更新
            self.update(
                'user_passwords',
                {'password': password_hash, 'salt': salt},
                'user_id = ?',
                (user_id,)
            )
            return True
        except:
            return False

    def get_user_level(self, user_id: str) -> str:
        """ユーザーの権限レベルを取得する"""
        result = self.select('user_passwords', 'user_level', condition="user_id = ?", values=(user_id,))
        if result:
            return result[0]['user_level']
        return "user"  # デフォルトは一般ユーザー

    # 追加統計メソッド
    def get_service_stats_for_chart(self, year: int = None) -> List[Dict]:
        """サービス別統計（グラフ用）"""
        if year is None:
            year = datetime.datetime.now().year

        query = """
        SELECT
            s.name as service_name,
            SUM(p.price) as total_amount,
            COUNT(p.id) as project_count
        FROM projects p
        JOIN services s ON p.service_id = s.id
        WHERE strftime('%Y', COALESCE(p.completion_date, p.created_at)) = ?
        GROUP BY s.id
        ORDER BY total_amount DESC
        """

        return self.execute_query(query, (str(year),))

    def get_price_statistics(self, year: int = None) -> Dict:
        """価格統計を取得する"""
        if year is None:
            year = datetime.datetime.now().year

        query = """
        SELECT
            AVG(price) as average_price,
            MIN(price) as min_price,
            MAX(price) as max_price,
            SUM(price) as total_price,
            COUNT(*) as total_count
        FROM projects
        WHERE strftime('%Y', COALESCE(completion_date, created_at)) = ?
        """

        result = self.execute_query(query, (str(year),))
        return result[0] if result else {
            'average_price': 0,
            'min_price': 0,
            'max_price': 0,
            'total_price': 0,
            'total_count': 0
        }

    def get_trouble_statistics_by_worker(self, year: int = None) -> List[Dict]:
        """作業員別トラブル統計"""
        if year is None:
            year = datetime.datetime.now().year

        query = """
        SELECT
            w.id as worker_id,
            w.name as worker_name,
            COUNT(CASE WHEN p.has_trouble = 1 AND p.trouble_worker_id = w.id THEN 1 END) as trouble_count,
            COUNT(pw.project_id) as project_count,
            CAST(COUNT(CASE WHEN p.has_trouble = 1 AND p.trouble_worker_id = w.id THEN 1 END) AS FLOAT) /
            CASE WHEN COUNT(pw.project_id) = 0 THEN 1 ELSE COUNT(pw.project_id) END * 100 as trouble_rate
        FROM workers w
        LEFT JOIN project_workers pw ON w.id = pw.worker_id
        LEFT JOIN projects p ON pw.project_id = p.id
        WHERE strftime('%Y', COALESCE(p.completion_date, p.created_at)) = ? OR p.id IS NULL
        GROUP BY w.id
        ORDER BY trouble_rate DESC
        """

        return self.execute_query(query, (str(year),))

    def get_trouble_statistics_by_client(self, year: int = None) -> List[Dict]:
        """取引先別トラブル統計"""
        if year is None:
            year = datetime.datetime.now().year

        query = """
        SELECT
            c.id as client_id,
            c.name as client_name,
            COUNT(CASE WHEN p.has_trouble = 1 THEN 1 END) as trouble_count,
            COUNT(p.id) as project_count,
            CAST(COUNT(CASE WHEN p.has_trouble = 1 THEN 1 END) AS FLOAT) /
            CASE WHEN COUNT(p.id) = 0 THEN 1 ELSE COUNT(p.id) END * 100 as trouble_rate
        FROM clients c
        LEFT JOIN projects p ON c.id = p.client_id
        WHERE strftime('%Y', COALESCE(p.completion_date, p.created_at)) = ? OR p.id IS NULL
        GROUP BY c.id
        ORDER BY trouble_rate DESC
        """

        return self.execute_query(query, (str(year),))

    def get_yearly_comparison_data(self, current_year: int, compare_year: int) -> Dict:
        """年度間比較データを取得する"""
        # 現在年度のデータ
        current_year_query = """
        SELECT
            strftime('%m', COALESCE(completion_date, created_at)) as month,
            SUM(price) as total_amount
        FROM projects
        WHERE strftime('%Y', COALESCE(completion_date, created_at)) = ?
        GROUP BY month
        ORDER BY month
        """

        current_year_data = self.execute_query(current_year_query, (str(current_year),))

        # 比較年度のデータ
        compare_year_query = """
        SELECT
            strftime('%m', COALESCE(completion_date, created_at)) as month,
            SUM(price) as total_amount
        FROM projects
        WHERE strftime('%Y', COALESCE(completion_date, created_at)) = ?
        GROUP BY month
        ORDER BY month
        """

        compare_year_data = self.execute_query(compare_year_query, (str(compare_year),))

        # 月ごとのデータを整形
        months = [f"{i:02d}" for i in range(1, 13)]

        current_dict = {item['month']: item['total_amount'] for item in current_year_data}
        compare_dict = {item['month']: item['total_amount'] for item in compare_year_data}

        result = {
            'months': months,
            'current_year': current_year,
            'compare_year': compare_year,
            'current_data': [current_dict.get(month, 0) for month in months],
            'compare_data': [compare_dict.get(month, 0) for month in months]
        }

        return result

    # 業務指示書関連のメソッド
    def save_work_order(self, order_data: Dict[str, Any]) -> int:
        """業務指示書を保存する"""
        order_id = order_data.get('id')

        if order_id:
            # 既存の業務指示書を更新
            self.update('work_orders', order_data, 'id = ?', (order_id,))
            return order_id
        else:
            # 新規の業務指示書を挿入
            return self.insert('work_orders', order_data)

    def get_work_orders(self, condition: str = "", values: Tuple = ()) -> List[Dict]:
        """業務指示書を取得する"""
        query = """
        SELECT
            wo.*,
            p.title as project_title,
            c.name as client_name,
            m.name as manager_name,
            cr.name as creator_name
        FROM work_orders wo
        LEFT JOIN projects p ON wo.project_id = p.id
        LEFT JOIN clients c ON p.client_id = c.id
        LEFT JOIN workers m ON wo.manager_id = m.id
        LEFT JOIN workers cr ON wo.creator_id = cr.id
        """

        if condition:
            query += f" WHERE {condition}"

        query += " ORDER BY wo.created_at DESC"

        return self.execute_query(query, values)

    def get_work_order(self, order_id: int) -> Optional[Dict]:
        """業務指示書を取得する"""
        orders = self.get_work_orders("wo.id = ?", (order_id,))
        return orders[0] if orders else None

    def delete_work_order(self, order_id: int) -> None:
        """業務指示書を削除する"""
        self.delete('work_orders', 'id = ?', (order_id,))

    def get_next_order_number(self) -> str:
        """次の業務指示書番号を生成する"""
        # 現在の年月を取得
        now = datetime.datetime.now()
        year_month = now.strftime("%Y%m")

        # 該当年月の最大番号を取得
        query = """
        SELECT MAX(order_number) as max_number
        FROM work_orders
        WHERE order_number LIKE ?
        """

        result = self.execute_query(query, (f"{year_month}%",))

        if result and result[0]['max_number']:
            # 既存の番号から連番部分を取得して+1
            last_number = result[0]['max_number']
            seq = int(last_number[-4:]) + 1
        else:
            # 新しい年月の最初の番号
            seq = 1

        # 新しい番号を生成(例: 202501-0001)
        new_number = f"{year_month}-{seq:04d}"

        return new_number

    # 売上目標関連のメソッド
    def get_sales_target(self, year: int, month: int = 0) -> float:
        """指定年度・月の売上目標を取得する"""
        result = self.select('sales_targets', 'target_amount', 'year = ? AND month = ?', (year, month))
        if result:
            return result[0]['target_amount']
        return 0.0

    def set_sales_target(self, year: int, month: int, target_amount: float) -> bool:
        """売上目標を設定する"""
        try:
            # 既存の目標があるか確認
            existing = self.select('sales_targets', 'id', 'year = ? AND month = ?', (year, month))

            if existing:
                # 既存の目標を更新
                self.update(
                    'sales_targets',
                    {'target_amount': target_amount},
                    'year = ? AND month = ?',
                    (year, month)
                )
            else:
                # 新規目標を挿入
                self.insert('sales_targets', {
                    'year': year,
                    'month': month,
                    'target_amount': target_amount
                })
            return True
        except Exception as e:
            print(f"売上目標設定エラー: {e}")
            return False

    def get_all_sales_targets(self, year: int) -> dict:
        """指定年度の全ての売上目標を取得する"""
        results = self.select('sales_targets', condition='year = ? ORDER BY month', values=(year,))

        # 月ごとの目標をディクショナリにまとめる
        targets = {0: 0.0}  # 年間目標のデフォルト値
        for month in range(1, 13):
            targets[month] = 0.0  # 各月のデフォルト値

        # 取得した目標で上書き
        for row in results:
            targets[row['month']] = row['target_amount']

        return targets
