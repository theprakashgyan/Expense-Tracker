import streamlit as st
import matplotlib.pyplot as plt
from main import FamilyExpenseTracker
from database import create_user, authenticate_user
from pathlib import Path
import pandas as pd

# Streamlit configuration
st.set_page_config(page_title="Family Expense Tracker", page_icon="💰", layout="wide")

# Path Settings
current_dir = Path(__file__).parent if "__file__" in locals() else Path.cwd()
css_file = current_dir / "styles" / "main.css"

with open(css_file) as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

# Session State Init
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None

# ---------------------------------------------
# LOGIN/REGISTER VIEW
# ---------------------------------------------
if not st.session_state['logged_in']:
    st.markdown("<h1 style='text-align: center;'>Welcome to Family Expense Tracker</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Manage your finances effortlessly. Log in or create an account to continue.</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔒 Login", "📝 Sign Up"])
        
        with tab1:
            st.subheader("Login to your account")
            login_username = st.text_input("Username", key="login_user")
            login_password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login", type="primary", use_container_width=True):
                user_context = authenticate_user(login_username, login_password)
                if user_context:
                    st.session_state['logged_in'] = True
                    st.session_state['user_id'] = user_context["id"]
                    st.session_state['username'] = user_context["username"]
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
        
        with tab2:
            st.subheader("Create a new account")
            reg_username = st.text_input("Username", key="reg_user")
            reg_password = st.text_input("Password", type="password", key="reg_pass")
            reg_confirm = st.text_input("Confirm Password", type="password")
            if st.button("Sign Up", type="primary", use_container_width=True):
                if reg_password != reg_confirm:
                    st.error("Passwords do not match!")
                elif len(reg_password) < 4:
                    st.error("Password must be at least 4 characters long.")
                elif len(reg_username) < 3:
                    st.error("Username must be at least 3 characters long.")
                elif reg_username.lower() == 'admin':
                    st.error("This username is reserved for the system administrator.")
                else:
                    success = create_user(reg_username, reg_password)
                    if success:
                        st.success("Account created successfully! You can now log in from the Login tab.")
                    else:
                        st.error("Username already exists. Please choose a different one.")

else:
    # ---------------------------------------------
    # INITIALIZE USER'S TRACKER
    # ---------------------------------------------
    expense_tracker = FamilyExpenseTracker(st.session_state['user_id'])

    # ---------------------------------------------
    # SIDEBAR (Data Entry & Logout)
    # ---------------------------------------------
    with st.sidebar:
        st.title("⚙️ Data Entry")
        st.markdown("---")
        
        if st.button("Logout", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['user_id'] = None
            st.session_state['username'] = None
            st.rerun()
            
        st.markdown("---")

        if st.session_state.get('username') == 'admin':
            st.subheader("👑 Admin Access")
            admin_mode = st.checkbox("Enable Admin Panel")
            st.markdown("---")
        else:
            admin_mode = False

    if admin_mode:
        st.title("🛡️ Admin Panel (Superuser)")
        st.markdown("View all database records securely.")
        
        tab1, tab2, tab3 = st.tabs(["Users", "Family Members", "Expenses"])
        
        from database import get_all_users, get_all_members, get_all_expenses
        
        with tab1:
            st.subheader("All Registered Users")
            users_data = get_all_users()
            if users_data:
                df_users = pd.DataFrame(users_data, columns=["ID", "Username"])
                st.dataframe(df_users, use_container_width=True, hide_index=True)
            else:
                 st.info("No users found.")
                 
        with tab2:
            st.subheader("All Family Members")
            members_data = get_all_members()
            if members_data:
                df_members = pd.DataFrame(members_data, columns=["ID", "Owner (Username)", "Name", "Earning Status", "Earnings"])
                st.dataframe(df_members, use_container_width=True, hide_index=True)
            else:
                 st.info("No family members found.")

        with tab3:
            st.subheader("All Expenses")
            exp_data = get_all_expenses()
            if exp_data:
                df_exp = pd.DataFrame(exp_data, columns=["ID", "Spender (Username)", "Category", "Description", "Value", "Date"])
                st.dataframe(df_exp, use_container_width=True, hide_index=True)
                
                csv_admin = df_exp.to_csv(index=False).encode('utf-8')
                st.download_button(
                     label="📥 Download Global Expenses",
                     data=csv_admin,
                     file_name="global_expenses_database.csv",
                     mime="text/csv",
                     use_container_width=True
                )
            else:
                 st.info("No expenses found.")

    else:
        st.header("Add Family Member")
        with st.expander("Member Details", expanded=False):
            member_name = st.text_input("Name").title()
            earning_status = st.checkbox("Earning Status", value=True)
            earnings = st.number_input("Earnings", value=1, min_value=0) if earning_status else 0

            if st.button("Add / Update Member", use_container_width=True):
                try:
                    member_query = [m for m in expense_tracker.members if m.name == member_name]
                    if not member_query:
                        expense_tracker.add_family_member(member_name, earning_status, earnings)
                        st.success("Added successfully!")
                    else:
                        expense_tracker.update_family_member(member_query[0], earning_status, earnings)
                        st.success("Updated successfully!")
                except ValueError as e:
                    st.error(str(e))

        st.header("Add Expenses")
        with st.expander("Expense Details", expanded=False):
            expense_category = st.selectbox(
                "Category",
                ("Housing", "Food", "Transportation", "Entertainment", "Child-Related", "Medical", "Investment", "Miscellaneous"),
            )
            expense_description = st.text_input("Description (optional)").title()
            expense_value = st.number_input("Value", min_value=0)
            expense_date = st.date_input("Date", value="today")

            if st.button("Add Expense", use_container_width=True, type="primary"):
                try:
                    expense_tracker.merge_similar_category(
                        expense_value, expense_category, expense_description, expense_date
                    )
                    st.success("Expense logged!")
                except ValueError as e:
                    st.error(str(e))

    # ---------------------------------------------
    # MAIN DASHBOARD
    # ---------------------------------------------
    st.title("🏦 Family Expense Dashboard")
    st.markdown("Monitor your family's finances effortlessly.")

    # Top Row: Key Metrics
    total_earnings = expense_tracker.calculate_total_earnings()
    total_expenditure = expense_tracker.calculate_total_expenditure()
    remaining_balance = total_earnings - total_expenditure

    # Styled metric columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Earnings", f"₹{total_earnings:,.2f}")
    with col2:
        st.metric("Total Expenditure", f"₹{total_expenditure:,.2f}")
    with col3:
        st.metric("Remaining Balance", f"₹{remaining_balance:,.2f}", 
                  delta="Surplus" if remaining_balance >= 0 else "Deficit",
                  delta_color="normal")

    st.markdown("---")

    # Middle Row: Charts & Data Overview
    if not expense_tracker.members and not expense_tracker.expense_list:
        st.info("👋 Welcome! Start by adding family members and logging expenses from the sidebar.")
    else:
        chart_col, data_col = st.columns([1, 1])

        with chart_col:
            st.subheader("📊 Expense Distribution")
            expense_data = [{"Category": exp.category, "Value": exp.value} for exp in expense_tracker.expense_list]
            if expense_data:
                expenses = [data["Category"] for data in expense_data]
                values = [data["Value"] for data in expense_data]
                total = sum(values)
                percentages = [(value / total) * 100 for value in values]

                # Custom neon palette
                neon_colors = ["#f43f5e", "#8b5cf6", "#10b981", "#3b82f6", "#f59e0b", "#06b6d4"]

                fig, ax = plt.subplots(figsize=(4, 4), dpi=300)
                ax.pie(
                    percentages,
                    labels=expenses,
                    autopct="%1.1f%%",
                    startangle=140,
                    colors=neon_colors,
                    textprops={"fontsize": 8, "color": "#f8fafc", "weight": "bold"},
                    wedgeprops={"linewidth": 1, "edgecolor": "#0f172a"}
                )
                fig.patch.set_facecolor("none")
                st.pyplot(fig)
            else:
                st.info("No expenses logged yet. Add some to see the chart!")

        with data_col:
            st.subheader("👥 Family Members")
            if expense_tracker.members:
                for member in expense_tracker.members:
                    with st.container():
                        mc1, mc2, mc3 = st.columns([2, 1, 1])
                        mc1.write(f"**{member.name}**")
                        mc2.write(f"₹{member.earnings:,.2f}")
                        if mc3.button("Drop", key=f"del_{member.id}", help="Remove Member"):
                            expense_tracker.delete_family_member(member)
                            st.rerun()
            else:
                st.info("No family members added yet.")

        st.markdown("---")
        if expense_tracker.expense_list:
            col_title, col_download = st.columns([3, 1])
            with col_title:
                st.subheader("🧾 Recent Expenses")
            with col_download:
                expense_dicts = [{"Category": exp.category, "Description": exp.description, "Value": exp.value, "Date": exp.date} for exp in expense_tracker.expense_list]
                df_user_exp = pd.DataFrame(expense_dicts)
                csv = df_user_exp.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"{st.session_state['username']}_expenses.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
            for expense in expense_tracker.expense_list:
                with st.container():
                    ec1, ec2, ec3, ec4 = st.columns([2, 2, 2, 1])
                    ec1.write(f"**{expense.category}**")
                    ec2.write(f"₹{expense.value:,.2f}")
                    ec3.write(str(expense.date))
                    if ec4.button("Drop", key=f"del_exp_{expense.id}", help="Remove Expense"):
                        expense_tracker.delete_expense(expense)
                        st.rerun()
        else:
             st.info("No expenses logged yet.")
