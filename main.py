from database import SessionLocal, FamilyMember as DBFamilyMember, Expense as DBExpense
from sqlalchemy import func

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

    @property
    def members(self):
        db = SessionLocal()
        db_members = db.query(DBFamilyMember).filter(DBFamilyMember.user_id == self.user_id).all()
        result = [FamilyMember(m.id, m.name, bool(m.earning_status), m.earnings) for m in db_members]
        db.close()
        return result

    @property
    def expense_list(self):
        db = SessionLocal()
        db_expenses = db.query(DBExpense).filter(DBExpense.user_id == self.user_id).all()
        result = [Expense(e.id, e.value, e.category, e.description, e.date) for e in db_expenses]
        db.close()
        return result

    def add_family_member(self, name, earning_status=True, earnings=0):
        if not name.strip():
            raise ValueError("Name field cannot be empty")
        db = SessionLocal()
        new_member = DBFamilyMember(user_id=self.user_id, name=name, earning_status=earning_status, earnings=earnings)
        db.add(new_member)
        db.commit()
        db.close()

    def delete_family_member(self, member):
        db = SessionLocal()
        db_member = db.query(DBFamilyMember).filter(DBFamilyMember.id == member.id).first()
        if db_member:
            db.delete(db_member)
            db.commit()
        db.close()

    def update_family_member(self, member, earning_status=True, earnings=0):
        if member:
            db = SessionLocal()
            db_member = db.query(DBFamilyMember).filter(DBFamilyMember.id == member.id).first()
            if db_member:
                db_member.earning_status = earning_status
                db_member.earnings = earnings
                db.commit()
            db.close()

    def calculate_total_earnings(self):
        db = SessionLocal()
        total = db.query(func.sum(DBFamilyMember.earnings)).filter(DBFamilyMember.user_id == self.user_id, DBFamilyMember.earning_status == True).scalar()
        db.close()
        return total if total else 0

    def add_expense(self, value, category, description, date):
        if value == 0:
            raise ValueError("Value cannot be zero")
        if not category.strip():
            raise ValueError("Please choose a category")

        db = SessionLocal()
        new_expense = DBExpense(user_id=self.user_id, category=category, description=description, value=value, date=date)
        db.add(new_expense)
        db.commit()
        db.close()

    def delete_expense(self, expense):
        db = SessionLocal()
        db_exp = db.query(DBExpense).filter(DBExpense.id == expense.id).first()
        if db_exp:
            db.delete(db_exp)
            db.commit()
        db.close()


    def merge_similar_category(self, value, category, description, date):
        if value == 0:
            raise ValueError("Value cannot be zero")
        if not category.strip():
            raise ValueError("Please choose a category")

        db = SessionLocal()
        existing_exp = db.query(DBExpense).filter(DBExpense.user_id == self.user_id, DBExpense.category == category).first()

        if existing_exp:
            existing_exp.value += value
            existing_exp.description = description if description else existing_exp.description
        else:
            new_expense = DBExpense(user_id=self.user_id, category=category, description=description, value=value, date=date)
            db.add(new_expense)
            
        db.commit()
        db.close()

    def calculate_total_expenditure(self):
        db = SessionLocal()
        total = db.query(func.sum(DBExpense.value)).filter(DBExpense.user_id == self.user_id).scalar()
        db.close()
        return total if total else 0
