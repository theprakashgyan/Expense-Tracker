import sqlite3
from database import DB_PATH

class FamilyMember:
    def __init__(self, id, name, earning_status, earnings):
        self.id = id
        self.name = name
        self.earning_status = earning_status
        self.earnings = earnings

    def __str__(self):
        return (
            f"Name: {self.name}, Earning Status: {'Earning' if self.earning_status else 'Not Earning'}, "
            f"Earnings: {self.earnings}"
        )


class Expense:
    def __init__(self, id, value, category, description, date):
        self.id = id
        self.value = value
        self.category = category
        self.description = description
        self.date = date

    def __str__(self):
        return f"Value: {self.value}, Category: {self.category}, Description: {self.description}, Date: {self.date}"


class FamilyExpenseTracker:
    def __init__(self, user_id):
        self.user_id = user_id

    def _get_connection(self):
        return sqlite3.connect(DB_PATH)

    @property
    def members(self):
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('SELECT id, name, earning_status, earnings FROM family_members WHERE user_id = ?', (self.user_id,))
        rows = c.fetchall()
        conn.close()
        return [FamilyMember(r[0], r[1], bool(r[2]), r[3]) for r in rows]

    @property
    def expense_list(self):
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('SELECT id, value, category, description, date FROM expenses WHERE user_id = ?', (self.user_id,))
        rows = c.fetchall()
        conn.close()
        return [Expense(r[0], r[1], r[2], r[3], r[4]) for r in rows]

    def add_family_member(self, name, earning_status=True, earnings=0):
        if not name.strip():
            raise ValueError("Name field cannot be empty")
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('INSERT INTO family_members (user_id, name, earning_status, earnings) VALUES (?, ?, ?, ?)',
                  (self.user_id, name, earning_status, earnings))
        conn.commit()
        conn.close()
    
    def delete_family_member(self, member):
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('DELETE FROM family_members WHERE id = ?', (member.id,))
        conn.commit()
        conn.close()

    def update_family_member(self, member, earning_status=True, earnings=0):
        if member:
            conn = self._get_connection()
            c = conn.cursor()
            c.execute('UPDATE family_members SET earning_status = ?, earnings = ? WHERE id = ?',
                      (earning_status, earnings, member.id))
            conn.commit()
            conn.close()

    def calculate_total_earnings(self):
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('SELECT SUM(earnings) FROM family_members WHERE user_id = ? AND earning_status = 1', (self.user_id,))
        total = c.fetchone()[0]
        conn.close()
        return total if total else 0

    def add_expense(self, value, category, description, date):
        if value == 0:
            raise ValueError("Value cannot be zero")
        if not category.strip():
            raise ValueError("Please choose a category")

        conn = self._get_connection()
        c = conn.cursor()
        c.execute('INSERT INTO expenses (user_id, category, description, value, date) VALUES (?, ?, ?, ?, ?)',
                  (self.user_id, category, description, value, date))
        conn.commit()
        conn.close()

    def delete_expense(self, expense):
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('DELETE FROM expenses WHERE id = ?', (expense.id,))
        conn.commit()
        conn.close()


    def merge_similar_category(self, value, category, description, date):
        if value == 0:
            raise ValueError("Value cannot be zero")
        if not category.strip():
            raise ValueError("Please choose a category")

        conn = self._get_connection()
        c = conn.cursor()
        c.execute('SELECT id, value, description FROM expenses WHERE user_id = ? AND category = ?', (self.user_id, category))
        row = c.fetchone()

        if row:
            exp_id, existing_value, existing_desc = row
            new_val = existing_value + value
            new_desc = description if description else existing_desc
            c.execute('UPDATE expenses SET value = ?, description = ? WHERE id = ?', (new_val, new_desc, exp_id))
        else:
            c.execute('INSERT INTO expenses (user_id, category, description, value, date) VALUES (?, ?, ?, ?, ?)',
                      (self.user_id, category, description, value, date))
            
        conn.commit()
        conn.close()

    def calculate_total_expenditure(self):
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('SELECT SUM(value) FROM expenses WHERE user_id = ?', (self.user_id,))
        total = c.fetchone()[0]
        conn.close()
        return total if total else 0
