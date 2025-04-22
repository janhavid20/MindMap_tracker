# Import necessary libraries
import streamlit as st
from sqlalchemy import create_engine, text
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String
# Database URL configuration
DATABASE_URL = "sqlite:///expense.db"
engine = create_engine(DATABASE_URL)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    email = Column(String, nullable=False)

class Expense(Base):
    __tablename__ = 'expenses'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    amount = Column(Integer)

Base.metadata.create_all(engine)


# Set global style configurations
sns.set_style("whitegrid")
st.set_page_config(page_title="MoneyMap Tracer", page_icon="💰", layout="centered")




# User Authentication Functions
def register_user(username, password, email):
    query = text("INSERT INTO users (username, password, email) VALUES (:username, :password, :email)")
    with engine.connect() as conn:
        try:
            conn.execute(query, {"username": username, "password": password, "email": email})
            conn.commit()  # Commit the transaction to save changes
            st.success("User registered successfully!")
        except Exception as e:
            st.error(f"Registration failed: {e}")

def login_user(username, password):
    query = text("SELECT * FROM users WHERE username = :username AND password = :password")
    with engine.connect() as conn:
        result = conn.execute(query, {"username": username, "password": password}).fetchone()
    return result

# Expense Management Functions
def add_expense(user_id, category_id, amount, date, description):
    query = text("INSERT INTO expenses (user_id, category_id, amount, date, description) VALUES (:user_id, :category_id, :amount, :date, :description)")
    with engine.connect() as conn:
        conn.execute(query, {"user_id": user_id, "category_id": category_id, "amount": amount, "date": date, "description": description})

def load_expenses(user_id):
    query = text("SELECT id, amount, date, description, category_id FROM expenses WHERE user_id = :user_id")
    with engine.connect() as conn:
        return conn.execute(query, {"user_id": user_id}).fetchall()

def load_expenses():
    uploaded_file = st.file_uploader("Choose a file", type=['csv'])
    if uploaded_file is not None:
        st.session_state.expenses = pd.read_csv(uploaded_file)

def save_expenses():
    st.session_state.expenses.to_csv('expenses.csv', index=False)
    st.success("Expenses saved successfully")

def delete_specific_expense(expense_id):
    query = text("DELETE FROM expenses WHERE id = :expense_id")
    with engine.connect() as conn:
        conn.execute(query, {"expense_id": expense_id})
    st.success("Expense deleted successfully!")

# Streamlit UI Enhancements
st.markdown("<h1 style='text-align: center; color: #808080;'>💰 MoneyMap Tracer</h1>", unsafe_allow_html=True)

# Session state for login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Initialize expenses as a DataFrame
if 'expenses' not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=['ID', 'Date', 'Category', 'Amount', 'Description'])

# Login/Register Section
if not st.session_state.logged_in:
    st.sidebar.header("💼 Login/Register")
    tab1, tab2 = st.sidebar.tabs(["Login", "Register"])
    with tab2:
        st.subheader("New User? Register Here!")
        username_reg = st.text_input("Username", placeholder="Choose a username")
        password_reg = st.text_input("Password", type="password", placeholder="Enter a secure password")
        email_reg = st.text_input("Email", placeholder="Your email address")
        if st.button("Register", key="register"):
            if username_reg and password_reg and email_reg:
                register_user(username_reg, password_reg, email_reg)
            else:
                st.warning("Please fill in all fields.")
    with tab1:
        st.subheader("Welcome Back! Login Below")
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        if st.button("Login", key="login"):
            user = login_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_id = user[0]
                st.session_state.username = user[1]
                st.success("Logged in successfully!")
            else:
                st.error("Invalid credentials.")

# Main Content for Logged-in Users
else:
    st.sidebar.header(f"👋 Welcome, {st.session_state.username}")
    if st.sidebar.button("Logout", key="logout"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.expenses = pd.DataFrame(columns=['ID', 'Date', 'Category', 'Amount', 'Description'])
        st.sidebar.info("Logged out successfully.")

    # Functions for Data Operations
    def add_expense_to_df(expense_id, date, category, amount, description):
        new_expense = pd.DataFrame([[expense_id, date, category, amount, description]], columns=st.session_state.expenses.columns)
        st.session_state.expenses = pd.concat([st.session_state.expenses, new_expense], ignore_index=True)

    def visualize_expenses():
        if not st.session_state.expenses.empty:
            category_totals = st.session_state.expenses.groupby('Category')['Amount'].sum()
            colors = [
                (54 / 255, 162 / 255, 235 / 255, 0.8),
                (255 / 255, 162 / 255, 235 / 255, 0.8),
                (255 / 255, 206 / 255, 86 / 255, 0.8),
                (75 / 255, 192 / 255, 192 / 255, 0.8),
                (153 / 255, 102 / 255, 255 / 255, 0.8),
                (255 / 255, 159 / 255, 64 / 255, 0.8),
                (255 / 255, 99 / 255, 132 / 255, 0.8),
            ]
            fig, ax = plt.subplots(figsize=(3, 3))
            wedges, texts, autotexts = ax.pie(
                category_totals,
                labels=category_totals.index,
                autopct='%1.1f%%',
                startangle=140,
                colors=colors,
                wedgeprops=dict(edgecolor='white', linewidth=1),
            )
            centre_circle = plt.Circle((0, 0), 0.40, color='white')
            fig = plt.gcf()
            fig.gca().add_artist(centre_circle)
            plt.setp(autotexts, size=10, weight="bold", color="black")
            ax.set_title('Expenses by Category', color="#4CAF50", fontsize=16, weight='bold', pad=20)
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.warning("No expenses to visualize!")

    # Main Interface Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 Home", "➕ Add Expense", "📜 Expense History", "📊 Visualization"])
    with tab1:
        st.markdown("<h3 style='text-align: center; color: #4CAF50;'>Welcome to your Expense Tracker Dashboard</h3>", unsafe_allow_html=True)
    with tab2:
        st.header('➕ Add Expense')
        date = st.date_input('Date')
        category = st.selectbox('Category', ['Food', 'Transport', 'Entertainment', 'Utilities', 'Health', 'Shopping'])
        amount = st.number_input('Amount', min_value=0.0, format="%.2f")
        description = st.text_input('Description', placeholder="Describe the expense")
        if st.button('Add Expense', key="add_expense"):
            if amount > 0 and description:
                add_expense_to_df(None, date, category, amount, description)
                st.success('Expense added successfully!')
            else:
                st.warning("Please enter a valid amount and description.")
    with tab3:
        st.header('📜 Expense History')
        if st.session_state.expenses.empty:
            st.info("No expenses recorded yet.")
        else:
            for idx, row in st.session_state.expenses.iterrows():
                col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 3, 1])
                col1.write(row['Date'])
                col2.write(row['Category'])
                col3.write(f"${row['Amount']:.2f}")
                col4.write(row['Description'])
                if col5.button("Delete", key=f"delete_{idx}"):
                    delete_specific_expense(row['ID'])
                    st.session_state.expenses.drop(index=idx, inplace=True)
        
        # File Operations Section, only in Expense History tab
        st.header("File Operations")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save Expenses"):
                save_expenses()
        with col2:
            if st.button("Load Expenses"):
                load_expenses()

    with tab4:
        st.header("📊 Expense Visualization")
        visualize_expenses()