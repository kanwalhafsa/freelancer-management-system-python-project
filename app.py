import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import hashlib
import uuid
import os
from PIL import Image
import io
import base64

# Set page configuration
st.set_page_config(
    page_title="FreelanceFlow",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4F8BF9;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #4F8BF9;
        margin-bottom: 1rem;
    }
    .card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #4F8BF9;
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        margin: 0.5rem;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        background-color: #4F8BF9;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Database class using OOP principles
class Database:
    def __init__(self, db_name="freelance_flow.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        # Users table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            email TEXT UNIQUE,
            full_name TEXT,
            subscription_type TEXT DEFAULT 'free',
            subscription_end_date TEXT,
            created_at TEXT
        )
        ''')
        
        # Clients table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            name TEXT,
            email TEXT,
            phone TEXT,
            company TEXT,
            address TEXT,
            notes TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Projects table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            client_id TEXT,
            name TEXT,
            description TEXT,
            start_date TEXT,
            end_date TEXT,
            status TEXT,
            budget REAL,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (client_id) REFERENCES clients (id)
        )
        ''')
        
        # Tasks table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            name TEXT,
            description TEXT,
            due_date TEXT,
            status TEXT,
            created_at TEXT,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
        ''')
        
        # Invoices table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            amount REAL,
            issue_date TEXT,
            due_date TEXT,
            status TEXT,
            notes TEXT,
            created_at TEXT,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
        ''')
        
        # Payments table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id TEXT PRIMARY KEY,
            invoice_id TEXT,
            amount REAL,
            payment_date TEXT,
            payment_method TEXT,
            notes TEXT,
            created_at TEXT,
            FOREIGN KEY (invoice_id) REFERENCES invoices (id)
        )
        ''')
        
        self.conn.commit()
    
    def close(self):
        self.conn.close()
    
    # User methods
    def add_user(self, username, password, email, full_name):
        user_id = str(uuid.uuid4())
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            self.cursor.execute(
                "INSERT INTO users (id, username, password, email, full_name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, username, hashed_password, email, full_name, created_at)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def verify_user(self, username, password):
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        self.cursor.execute(
            "SELECT id, username, email, full_name, subscription_type FROM users WHERE username = ? AND password = ?",
            (username, hashed_password)
        )
        user = self.cursor.fetchone()
        if user:
            return {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "full_name": user[3],
                "subscription_type": user[4]
            }
        return None
    
    # Client methods
    def add_client(self, user_id, name, email, phone, company, address, notes):
        client_id = str(uuid.uuid4())
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.cursor.execute(
            "INSERT INTO clients (id, user_id, name, email, phone, company, address, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (client_id, user_id, name, email, phone, company, address, notes, created_at)
        )
        self.conn.commit()
        return client_id
    
    def get_clients(self, user_id):
        self.cursor.execute("SELECT * FROM clients WHERE user_id = ?", (user_id,))
        clients = self.cursor.fetchall()
        return clients
    
    def get_client(self, client_id):
        self.cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        client = self.cursor.fetchone()
        return client
    
    def update_client(self, client_id, name, email, phone, company, address, notes):
        self.cursor.execute(
            "UPDATE clients SET name = ?, email = ?, phone = ?, company = ?, address = ?, notes = ? WHERE id = ?",
            (name, email, phone, company, address, notes, client_id)
        )
        self.conn.commit()
    
    def delete_client(self, client_id):
        self.cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        self.conn.commit()
    
    # Project methods
    def add_project(self, user_id, client_id, name, description, start_date, end_date, status, budget):
        project_id = str(uuid.uuid4())
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.cursor.execute(
            "INSERT INTO projects (id, user_id, client_id, name, description, start_date, end_date, status, budget, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (project_id, user_id, client_id, name, description, start_date, end_date, status, budget, created_at)
        )
        self.conn.commit()
        return project_id
    
    def get_projects(self, user_id):
        self.cursor.execute("""
            SELECT p.*, c.name as client_name 
            FROM projects p
            JOIN clients c ON p.client_id = c.id
            WHERE p.user_id = ?
        """, (user_id,))
        projects = self.cursor.fetchall()
        return projects
    
    def get_project(self, project_id):
        self.cursor.execute("""
            SELECT p.*, c.name as client_name 
            FROM projects p
            JOIN clients c ON p.client_id = c.id
            WHERE p.id = ?
        """, (project_id,))
        project = self.cursor.fetchone()
        return project
    
    def update_project(self, project_id, client_id, name, description, start_date, end_date, status, budget):
        self.cursor.execute(
            "UPDATE projects SET client_id = ?, name = ?, description = ?, start_date = ?, end_date = ?, status = ?, budget = ? WHERE id = ?",
            (client_id, name, description, start_date, end_date, status, budget, project_id)
        )
        self.conn.commit()
    
    def delete_project(self, project_id):
        self.cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        self.conn.commit()
    
    # Task methods
    def add_task(self, project_id, name, description, due_date, status):
        task_id = str(uuid.uuid4())
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.cursor.execute(
            "INSERT INTO tasks (id, project_id, name, description, due_date, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (task_id, project_id, name, description, due_date, status, created_at)
        )
        self.conn.commit()
        return task_id
    
    def get_tasks(self, project_id):
        self.cursor.execute("SELECT * FROM tasks WHERE project_id = ?", (project_id,))
        tasks = self.cursor.fetchall()
        return tasks
    
    def get_task(self, task_id):
        self.cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = self.cursor.fetchone()
        return task
    
    def update_task(self, task_id, name, description, due_date, status):
        self.cursor.execute(
            "UPDATE tasks SET name = ?, description = ?, due_date = ?, status = ? WHERE id = ?",
            (name, description, due_date, status, task_id)
        )
        self.conn.commit()
    
    def delete_task(self, task_id):
        self.cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()
    
    # Invoice methods
    def add_invoice(self, project_id, amount, issue_date, due_date, status, notes):
        invoice_id = str(uuid.uuid4())
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.cursor.execute(
            "INSERT INTO invoices (id, project_id, amount, issue_date, due_date, status, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (invoice_id, project_id, amount, issue_date, due_date, status, notes, created_at)
        )
        self.conn.commit()
        return invoice_id
    
    def get_invoices(self, project_id=None):
        if project_id:
            self.cursor.execute("""
                SELECT i.*, p.name as project_name, c.name as client_name
                FROM invoices i
                JOIN projects p ON i.project_id = p.id
                JOIN clients c ON p.client_id = c.id
                WHERE i.project_id = ?
            """, (project_id,))
        else:
            self.cursor.execute("""
                SELECT i.*, p.name as project_name, c.name as client_name
                FROM invoices i
                JOIN projects p ON i.project_id = p.id
                JOIN clients c ON p.client_id = c.id
            """)
        invoices = self.cursor.fetchall()
        return invoices
    
    def get_invoice(self, invoice_id):
        self.cursor.execute("""
            SELECT i.*, p.name as project_name, c.name as client_name
            FROM invoices i
            JOIN projects p ON i.project_id = p.id
            JOIN clients c ON p.client_id = c.id
            WHERE i.id = ?
        """, (invoice_id,))
        invoice = self.cursor.fetchone()
        return invoice
    
    def update_invoice(self, invoice_id, amount, issue_date, due_date, status, notes):
        self.cursor.execute(
            "UPDATE invoices SET amount = ?, issue_date = ?, due_date = ?, status = ?, notes = ? WHERE id = ?",
            (amount, issue_date, due_date, status, notes, invoice_id)
        )
        self.conn.commit()
    
    def delete_invoice(self, invoice_id):
        self.cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
        self.conn.commit()
    
    # Payment methods
    def add_payment(self, invoice_id, amount, payment_date, payment_method, notes):
        payment_id = str(uuid.uuid4())
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.cursor.execute(
            "INSERT INTO payments (id, invoice_id, amount, payment_date, payment_method, notes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (payment_id, invoice_id, amount, payment_date, payment_method, notes, created_at)
        )
        self.conn.commit()
        
        # Update invoice status if fully paid
        self.cursor.execute("SELECT amount FROM invoices WHERE id = ?", (invoice_id,))
        invoice_amount = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT SUM(amount) FROM payments WHERE invoice_id = ?", (invoice_id,))
        total_paid = self.cursor.fetchone()[0] or 0
        
        if total_paid >= invoice_amount:
            self.cursor.execute("UPDATE invoices SET status = 'Paid' WHERE id = ?", (invoice_id,))
        elif total_paid > 0:
            self.cursor.execute("UPDATE invoices SET status = 'Partially Paid' WHERE id = ?", (invoice_id,))
        
        self.conn.commit()
        return payment_id
    
    def get_payments(self, invoice_id):
        self.cursor.execute("SELECT * FROM payments WHERE invoice_id = ?", (invoice_id,))
        payments = self.cursor.fetchall()
        return payments
    
    def get_payment(self, payment_id):
        self.cursor.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
        payment = self.cursor.fetchone()
        return payment
    
    def update_payment(self, payment_id, amount, payment_date, payment_method, notes):
        self.cursor.execute(
            "UPDATE payments SET amount = ?, payment_date = ?, payment_method = ?, notes = ? WHERE id = ?",
            (amount, payment_date, payment_method, notes, payment_id)
        )
        self.conn.commit()
    
    def delete_payment(self, payment_id):
        self.cursor.execute("SELECT invoice_id FROM payments WHERE id = ?", (payment_id,))
        invoice_id = self.cursor.fetchone()[0]
        
        self.cursor.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
        self.conn.commit()
        
        # Update invoice status
        self.cursor.execute("SELECT amount FROM invoices WHERE id = ?", (invoice_id,))
        invoice_amount = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT SUM(amount) FROM payments WHERE invoice_id = ?", (invoice_id,))
        total_paid = self.cursor.fetchone()[0] or 0
        
        if total_paid >= invoice_amount:
            self.cursor.execute("UPDATE invoices SET status = 'Paid' WHERE id = ?", (invoice_id,))
        elif total_paid > 0:
            self.cursor.execute("UPDATE invoices SET status = 'Partially Paid' WHERE id = ?", (invoice_id,))
        else:
            self.cursor.execute("UPDATE invoices SET status = 'Unpaid' WHERE id = ?", (invoice_id,))
        
        self.conn.commit()
    
    # Dashboard methods
    def get_dashboard_data(self, user_id):
        # Total clients
        self.cursor.execute("SELECT COUNT(*) FROM clients WHERE user_id = ?", (user_id,))
        total_clients = self.cursor.fetchone()[0]
        
        # Total projects
        self.cursor.execute("SELECT COUNT(*) FROM projects WHERE user_id = ?", (user_id,))
        total_projects = self.cursor.fetchone()[0]
        
        # Total invoices
        self.cursor.execute("""
            SELECT COUNT(*) 
            FROM invoices i
            JOIN projects p ON i.project_id = p.id
            WHERE p.user_id = ?
        """, (user_id,))
        total_invoices = self.cursor.fetchone()[0]
        
        # Total revenue - FIXED QUERY
        self.cursor.execute("""
            SELECT SUM(pa.amount) 
            FROM payments pa
            JOIN invoices i ON pa.invoice_id = i.id
            JOIN projects p ON i.project_id = p.id
            WHERE p.user_id = ?
        """, (user_id,))
        total_revenue = self.cursor.fetchone()[0] or 0
        
        # Pending invoices
        self.cursor.execute("""
            SELECT COUNT(*) 
            FROM invoices i
            JOIN projects p ON i.project_id = p.id
            WHERE p.user_id = ? AND i.status != 'Paid'
        """, (user_id,))
        pending_invoices = self.cursor.fetchone()[0]
        
        # Pending amount
        self.cursor.execute("""
            SELECT SUM(i.amount - COALESCE((SELECT SUM(amount) FROM payments WHERE invoice_id = i.id), 0)) 
            FROM invoices i
            JOIN projects p ON i.project_id = p.id
            WHERE p.user_id = ? AND i.status != 'Paid'
        """, (user_id,))
        pending_amount = self.cursor.fetchone()[0] or 0
        
        # Projects by status
        self.cursor.execute("""
            SELECT status, COUNT(*) 
            FROM projects 
            WHERE user_id = ? 
            GROUP BY status
        """, (user_id,))
        projects_by_status = self.cursor.fetchall()
        
        # Recent projects
        self.cursor.execute("""
            SELECT p.*, c.name as client_name 
            FROM projects p
            JOIN clients c ON p.client_id = c.id
            WHERE p.user_id = ?
            ORDER BY p.created_at DESC
            LIMIT 5
        """, (user_id,))
        recent_projects = self.cursor.fetchall()
        
        # Recent invoices
        self.cursor.execute("""
            SELECT i.*, p.name as project_name, c.name as client_name
            FROM invoices i
            JOIN projects p ON i.project_id = p.id
            JOIN clients c ON p.client_id = c.id
            WHERE p.user_id = ?
            ORDER BY i.created_at DESC
            LIMIT 5
        """, (user_id,))
        recent_invoices = self.cursor.fetchall()
        
        # Monthly revenue - FIXED QUERY
        self.cursor.execute("""
            SELECT strftime('%Y-%m', pa.payment_date) as month, SUM(pa.amount) as revenue
            FROM payments pa
            JOIN invoices i ON pa.invoice_id = i.id
            JOIN projects p ON i.project_id = p.id
            WHERE p.user_id = ?
            GROUP BY month
            ORDER BY month
            LIMIT 12
        """, (user_id,))
        monthly_revenue = self.cursor.fetchall()
        
        return {
            "total_clients": total_clients,
            "total_projects": total_projects,
            "total_invoices": total_invoices,
            "total_revenue": total_revenue,
            "pending_invoices": pending_invoices,
            "pending_amount": pending_amount,
            "projects_by_status": projects_by_status,
            "recent_projects": recent_projects,
            "recent_invoices": recent_invoices,
            "monthly_revenue": monthly_revenue
        }

# Authentication class
class Auth:
    def __init__(self, db):
        self.db = db
    
    def login(self, username, password):
        return self.db.verify_user(username, password)
    
    def register(self, username, password, email, full_name):
        return self.db.add_user(username, password, email, full_name)
    
    def is_premium(self, subscription_type):
        return subscription_type in ["premium", "enterprise"]

# Payment class (simulated)
class Payment:
    def __init__(self):
        pass
    
    def process_payment(self, amount, card_number, expiry, cvv):
        # Simulate payment processing
        # In a real app, this would integrate with Stripe, PayPal, etc.
        if len(card_number) == 16 and len(expiry) == 5 and len(cvv) == 3:
            return {
                "success": True,
                "transaction_id": str(uuid.uuid4()),
                "amount": amount,
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        return {
            "success": False,
            "error": "Invalid payment details"
        }
    
    def upgrade_subscription(self, user_id, plan_type, payment_details):
        # Simulate subscription upgrade
        # In a real app, this would create a subscription in Stripe, etc.
        result = self.process_payment(
            99.99 if plan_type == "annual" else 9.99,
            payment_details["card_number"],
            payment_details["expiry"],
            payment_details["cvv"]
        )
        
        if result["success"]:
            # Calculate subscription end date
            if plan_type == "annual":
                end_date = (datetime.datetime.now() + datetime.timedelta(days=365)).strftime("%Y-%m-%d")
            else:
                end_date = (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
            
            return {
                "success": True,
                "subscription_type": "premium",
                "subscription_end_date": end_date,
                "transaction_id": result["transaction_id"]
            }
        
        return {
            "success": False,
            "error": result["error"]
        }

# Initialize database
db = Database()
auth = Auth(db)
payment = Payment()

# Session state initialization
if 'user' not in st.session_state:
    st.session_state.user = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'temp_data' not in st.session_state:
    st.session_state.temp_data = {}

# Navigation function
def navigate_to(page):
    st.session_state.page = page
    st.session_state.temp_data = {}

# Logo and branding
def display_logo():
    # Create a simple logo using matplotlib
    fig, ax = plt.subplots(figsize=(2, 2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    
    # Draw the logo
    circle = plt.Circle((5, 5), 4, fill=True, color='#4F8BF9')
    ax.add_patch(circle)
    
    # Add text
    ax.text(5, 5, 'FF', fontsize=24, color='white', 
            ha='center', va='center', fontweight='bold')
    
    ax.axis('off')
    
    # Convert to image
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
    buf.seek(0)
    
    # Display the logo
    st.image(buf, width=100)
    plt.close(fig)

# Login page
def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<h1 class="main-header">FreelanceFlow</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align: center;">Your all-in-one freelance project management solution</p>', unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if username and password:
                    user = auth.login(username, password)
                    if user:
                        st.session_state.user = user
                        navigate_to('dashboard')
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Please enter both username and password")
        
        st.markdown('<div style="text-align: center; margin-top: 1rem;">', unsafe_allow_html=True)
        if st.button("Create an account"):
            navigate_to('register')
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# Register page
def register_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<h1 class="main-header">Create an Account</h1>', unsafe_allow_html=True)
        
        with st.form("register_form"):
            full_name = st.text_input("Full Name")
            email = st.text_input("Email")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            submit = st.form_submit_button("Register")
            
            if submit:
                if full_name and email and username and password and confirm_password:
                    if password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters long")
                    else:
                        success = auth.register(username, password, email, full_name)
                        if success:
                            st.success("Account created successfully! Please login.")
                            navigate_to('login')
                            st.rerun()
                        else:
                            st.error("Username or email already exists")
                else:
                    st.error("Please fill in all fields")
        
        st.markdown('<div style="text-align: center; margin-top: 1rem;">', unsafe_allow_html=True)
        if st.button("Already have an account? Login"):
            navigate_to('login')
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
# Dashboard page
def dashboard_page():
    st.markdown('<h1 class="main-header">Dashboard</h1>', unsafe_allow_html=True)
    
    # Get dashboard data
    dashboard_data = db.get_dashboard_data(st.session_state.user["id"])
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{dashboard_data['total_clients']}</h3>
            <p>Clients</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{dashboard_data['total_projects']}</h3>
            <p>Projects</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>${dashboard_data['total_revenue']:,.2f}</h3>
            <p>Total Revenue</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>${dashboard_data['pending_amount']:,.2f}</h3>
            <p>Pending Payments</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Projects by status
    st.markdown('<h2 class="sub-header">Projects by Status</h2>', unsafe_allow_html=True)
    
    if dashboard_data['projects_by_status']:
        # Create a DataFrame for the pie chart
        status_df = pd.DataFrame(dashboard_data['projects_by_status'], columns=['Status', 'Count'])
        
        # Create a pie chart
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.pie(status_df['Count'], labels=status_df['Status'], autopct='%1.1f%%', startangle=90, colors=['#4F8BF9', '#36b9cc', '#1cc88a', '#f6c23e', '#e74a3b'])
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        
        st.pyplot(fig)
    else:
        st.info("No projects found. Create your first project to see statistics.")
    
    # Monthly revenue
    st.markdown('<h2 class="sub-header">Monthly Revenue</h2>', unsafe_allow_html=True)
    
    if dashboard_data['monthly_revenue']:
        # Create a DataFrame for the bar chart
        revenue_df = pd.DataFrame(dashboard_data['monthly_revenue'], columns=['Month', 'Revenue'])
        
        # Create a bar chart
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(revenue_df['Month'], revenue_df['Revenue'], color='#4F8BF9')
        ax.set_xlabel('Month')
        ax.set_ylabel('Revenue ($)')
        ax.set_title('Monthly Revenue')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        st.pyplot(fig)
    else:
        st.info("No revenue data available yet. Create invoices and record payments to see statistics.")
    
    # Recent projects
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<h2 class="sub-header">Recent Projects</h2>', unsafe_allow_html=True)
        
        if dashboard_data['recent_projects']:
            for project in dashboard_data['recent_projects']:
                st.markdown(f"""
                <div class="card">
                    <h3>{project[3]}</h3>
                    <p><strong>Client:</strong> {project[10]}</p>
                    <p><strong>Status:</strong> {project[7]}</p>
                    <p><strong>Budget:</strong> ${project[8]:,.2f}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No projects found. Create your first project.")
    
    with col2:
        st.markdown('<h2 class="sub-header">Recent Invoices</h2>', unsafe_allow_html=True)
        
        if dashboard_data['recent_invoices']:
            for invoice in dashboard_data['recent_invoices']:
                # Safe access to invoice data with proper index checking
                invoice_id = invoice[0][:8] if len(invoice) > 0 else "N/A"
                project_name = invoice[8] if len(invoice) > 8 else "N/A"
                client_name = invoice[9] if len(invoice) > 9 else "N/A"
                amount = invoice[2] if len(invoice) > 2 else 0
                status = invoice[5] if len(invoice) > 5 else "Unknown"
                
                st.markdown(f"""
                <div class="card">
                    <h3>Invoice #{invoice_id}</h3>
                    <p><strong>Project:</strong> {project_name}</p>
                    <p><strong>Client:</strong> {client_name}</p>
                    <p><strong>Amount:</strong> ${amount:,.2f}</p>
                    <p><strong>Status:</strong> {status}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No invoices found. Create your first invoice.")
# Clients page
def clients_page():
    st.markdown('<h1 class="main-header">Clients</h1>', unsafe_allow_html=True)
    
    # Add client button
    if st.button("Add New Client"):
        navigate_to('add_client')
        st.rerun()
    
    # Get all clients
    clients = db.get_clients(st.session_state.user["id"])
    
    if clients:
        # Convert to DataFrame for better display
        clients_df = pd.DataFrame(clients, columns=[
            'ID', 'User ID', 'Name', 'Email', 'Phone', 'Company', 'Address', 'Notes', 'Created At'
        ])
        
        # Display clients in a table
        st.dataframe(clients_df[['Name', 'Email', 'Phone', 'Company']], use_container_width=True)
        
        # Client details
        st.markdown('<h2 class="sub-header">Client Details</h2>', unsafe_allow_html=True)
        
        # Select client
        client_names = [client[2] for client in clients]
        selected_client_name = st.selectbox("Select a client", client_names)
        
        # Find the selected client
        selected_client = next((client for client in clients if client[2] == selected_client_name), None)
        
        if selected_client:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div class="card">
                    <h3>{selected_client[2]}</h3>
                    <p><strong>Email:</strong> {selected_client[3]}</p>
                    <p><strong>Phone:</strong> {selected_client[4]}</p>
                    <p><strong>Company:</strong> {selected_client[5]}</p>
                    <p><strong>Address:</strong> {selected_client[6]}</p>
                    <p><strong>Notes:</strong> {selected_client[7]}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Client actions
                if st.button("Edit Client"):
                    st.session_state.temp_data["client_id"] = selected_client[0]
                    navigate_to('edit_client')
                    st.rerun()
                
                if st.button("Delete Client"):
                    if st.checkbox("Confirm deletion"):
                        db.delete_client(selected_client[0])
                        st.success(f"Client '{selected_client[2]}' deleted successfully")
                        st.rerun()
                
                if st.button("Add Project for this Client"):
                    st.session_state.temp_data["client_id"] = selected_client[0]
                    navigate_to('add_project')
                    st.rerun()
    else:
        st.info("No clients found. Add your first client.")

# Add client page
def add_client_page():
    st.markdown('<h1 class="main-header">Add New Client</h1>', unsafe_allow_html=True)
    
    with st.form("add_client_form"):
        name = st.text_input("Client Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        company = st.text_input("Company")
        address = st.text_area("Address")
        notes = st.text_area("Notes")
        
        submit = st.form_submit_button("Add Client")
        
        if submit:
            if name and email:
                client_id = db.add_client(
                    st.session_state.user["id"],
                    name,
                    email,
                    phone,
                    company,
                    address,
                    notes
                )
                st.success(f"Client '{name}' added successfully")
                navigate_to('clients')
                st.rerun()
            else:
                st.error("Client name and email are required")
    
    if st.button("Cancel"):
        navigate_to('clients')
        st.rerun()

# Edit client page
def edit_client_page():
    st.markdown('<h1 class="main-header">Edit Client</h1>', unsafe_allow_html=True)
    
    client_id = st.session_state.temp_data.get("client_id")
    if not client_id:
        st.error("No client selected")
        if st.button("Back to Clients"):
            navigate_to('clients')
            st.rerun()
        return
    
    client = db.get_client(client_id)
    if not client:
        st.error("Client not found")
        if st.button("Back to Clients"):
            navigate_to('clients')
            st.rerun()
        return
    
    with st.form("edit_client_form"):
        name = st.text_input("Client Name", value=client[2])
        email = st.text_input("Email", value=client[3])
        phone = st.text_input("Phone", value=client[4])
        company = st.text_input("Company", value=client[5])
        address = st.text_area("Address", value=client[6])
        notes = st.text_area("Notes", value=client[7])
        
        submit = st.form_submit_button("Update Client")
        
        if submit:
            if name and email:
                db.update_client(
                    client_id,
                    name,
                    email,
                    phone,
                    company,
                    address,
                    notes
                )
                st.success(f"Client '{name}' updated successfully")
                navigate_to('clients')
                st.rerun()
            else:
                st.error("Client name and email are required")
    
    if st.button("Cancel"):
        navigate_to('clients')
        st.rerun()

# Projects page
def projects_page():
    st.markdown('<h1 class="main-header">Projects</h1>', unsafe_allow_html=True)
    
    # Add project button
    if st.button("Add New Project"):
        navigate_to('add_project')
        st.rerun()
    
    # Get all projects
    projects = db.get_projects(st.session_state.user["id"])
    
    if projects:
        # Filter options
        status_options = ["All"] + list(set(project[7] for project in projects))
        selected_status = st.selectbox("Filter by Status", status_options)
        
        # Filter projects by status
        filtered_projects = projects
        if selected_status != "All":
            filtered_projects = [project for project in projects if project[7] == selected_status]
        
        # Convert to DataFrame for better display
        projects_df = pd.DataFrame(filtered_projects, columns=[
            'ID', 'User ID', 'Client ID', 'Name', 'Description', 'Start Date', 'End Date', 
            'Status', 'Budget', 'Created At', 'Client Name'
        ])
        
        # Display projects in a table
        st.dataframe(projects_df[['Name', 'Client Name', 'Status', 'Budget', 'Start Date', 'End Date']], use_container_width=True)
        
        # Project details
        st.markdown('<h2 class="sub-header">Project Details</h2>', unsafe_allow_html=True)
        
        # Select project
        project_names = [project[3] for project in filtered_projects]
        selected_project_name = st.selectbox("Select a project", project_names)
        
        # Find the selected project
        selected_project = next((project for project in filtered_projects if project[3] == selected_project_name), None)
        
        if selected_project:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div class="card">
                    <h3>{selected_project[3]}</h3>
                    <p><strong>Client:</strong> {selected_project[10]}</p>
                    <p><strong>Status:</strong> {selected_project[7]}</p>
                    <p><strong>Budget:</strong> ${selected_project[8]:,.2f}</p>
                    <p><strong>Start Date:</strong> {selected_project[5]}</p>
                    <p><strong>End Date:</strong> {selected_project[6]}</p>
                    <p><strong>Description:</strong> {selected_project[4]}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Project actions
                if st.button("Edit Project"):
                    st.session_state.temp_data["project_id"] = selected_project[0]
                    navigate_to('edit_project')
                    st.rerun()
                
                if st.button("Delete Project"):
                    if st.checkbox("Confirm deletion"):
                        db.delete_project(selected_project[0])
                        st.success(f"Project '{selected_project[3]}' deleted successfully")
                        st.rerun()
                
                if st.button("Manage Tasks"):
                    st.session_state.temp_data["project_id"] = selected_project[0]
                    navigate_to('tasks')
                    st.rerun()
                
                if st.button("Create Invoice"):
                    st.session_state.temp_data["project_id"] = selected_project[0]
                    navigate_to('add_invoice')
                    st.rerun()
    else:
        st.info("No projects found. Add your first project.")

# Add project page
def add_project_page():
    st.markdown('<h1 class="main-header">Add New Project</h1>', unsafe_allow_html=True)
    
    # Get all clients
    clients = db.get_clients(st.session_state.user["id"])
    
    if not clients:
        st.warning("You need to add a client first")
        if st.button("Add Client"):
            navigate_to('add_client')
            st.rerun()
        return
    
    with st.form("add_project_form"):
        # If client_id is in temp_data, preselect that client
        preselected_client_id = st.session_state.temp_data.get("client_id")
        client_names = [client[2] for client in clients]
        
        if preselected_client_id:
            preselected_client = next((client for client in clients if client[0] == preselected_client_id), None)
            if preselected_client:
                preselected_index = client_names.index(preselected_client[2])
            else:
                preselected_index = 0
        else:
            preselected_index = 0
        
        client_name = st.selectbox("Client", client_names, index=preselected_index)
        client_id = next((client[0] for client in clients if client[2] == client_name), None)
        
        name = st.text_input("Project Name")
        description = st.text_area("Description")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date")
        with col2:
            end_date = st.date_input("End Date")
        
        status = st.selectbox("Status", ["Not Started", "In Progress", "On Hold", "Completed", "Cancelled"])
        budget = st.number_input("Budget ($)", min_value=0.0, step=100.0)
        
        submit = st.form_submit_button("Add Project")
        
        if submit:
            if name and client_id:
                if end_date < start_date:
                    st.error("End date cannot be before start date")
                else:
                    project_id = db.add_project(
                        st.session_state.user["id"],
                        client_id,
                        name,
                        description,
                        start_date.strftime("%Y-%m-%d"),
                        end_date.strftime("%Y-%m-%d"),
                        status,
                        budget
                    )
                    st.success(f"Project '{name}' added successfully")
                    navigate_to('projects')
                    st.rerun()
            else:
                st.error("Project name and client are required")
    
    if st.button("Cancel"):
        navigate_to('projects')
        st.rerun()

# Edit project page
def edit_project_page():
    st.markdown('<h1 class="main-header">Edit Project</h1>', unsafe_allow_html=True)
    
    project_id = st.session_state.temp_data.get("project_id")
    if not project_id:
        st.error("No project selected")
        if st.button("Back to Projects"):
            navigate_to('projects')
            st.rerun()
        return
    
    project = db.get_project(project_id)
    if not project:
        st.error("Project not found")
        if st.button("Back to Projects"):
            navigate_to('projects')
            st.rerun()
        return
    
    # Get all clients
    clients = db.get_clients(st.session_state.user["id"])
    
    with st.form("edit_project_form"):
        client_names = [client[2] for client in clients]
        current_client = next((client for client in clients if client[0] == project[2]), None)
        
        if current_client:
            current_client_index = client_names.index(current_client[2])
        else:
            current_client_index = 0
        
        client_name = st.selectbox("Client", client_names, index=current_client_index)
        client_id = next((client[0] for client in clients if client[2] == client_name), None)
        
        name = st.text_input("Project Name", value=project[3])
        description = st.text_area("Description", value=project[4])
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=datetime.datetime.strptime(project[5], "%Y-%m-%d").date())
        with col2:
            end_date = st.date_input("End Date", value=datetime.datetime.strptime(project[6], "%Y-%m-%d").date())
        
        status = st.selectbox("Status", ["Not Started", "In Progress", "On Hold", "Completed", "Cancelled"], index=["Not Started", "In Progress", "On Hold", "Completed", "Cancelled"].index(project[7]))
        budget = st.number_input("Budget ($)", min_value=0.0, step=100.0, value=float(project[8]))
        
        submit = st.form_submit_button("Update Project")
        
        if submit:
            if name and client_id:
                if end_date < start_date:
                    st.error("End date cannot be before start date")
                else:
                    db.update_project(
                        project_id,
                        client_id,
                        name,
                        description,
                        start_date.strftime("%Y-%m-%d"),
                        end_date.strftime("%Y-%m-%d"),
                        status,
                        budget
                    )
                    st.success(f"Project '{name}' updated successfully")
                    navigate_to('projects')
                    st.rerun()
            else:
                st.error("Project name and client are required")
    
    if st.button("Cancel"):
        navigate_to('projects')
        st.rerun()

# Tasks page
def tasks_page():
    st.markdown('<h1 class="main-header">Tasks</h1>', unsafe_allow_html=True)
    
    project_id = st.session_state.temp_data.get("project_id")
    if not project_id:
        st.error("No project selected")
        if st.button("Back to Projects"):
            navigate_to('projects')
            st.rerun()
        return
    
    project = db.get_project(project_id)
    if not project:
        st.error("Project not found")
        if st.button("Back to Projects"):
            navigate_to('projects')
            st.rerun()
        return
    
    st.markdown(f'<h2 class="sub-header">Tasks for Project: {project[3]}</h2>', unsafe_allow_html=True)
    
    # Add task button
    if st.button("Add New Task"):
        st.session_state.temp_data["add_task"] = True
    
    # Get all tasks for the project
    tasks = db.get_tasks(project_id)
    
    # Add task form
    if st.session_state.temp_data.get("add_task"):
        with st.form("add_task_form"):
            st.markdown('<h3>Add New Task</h3>', unsafe_allow_html=True)
            
            name = st.text_input("Task Name")
            description = st.text_area("Description")
            due_date = st.date_input("Due Date")
            status = st.selectbox("Status", ["Not Started", "In Progress", "Completed"])
            
            submit = st.form_submit_button("Add Task")
            
            if submit:
                if name:
                    task_id = db.add_task(
                        project_id,
                        name,
                        description,
                        due_date.strftime("%Y-%m-%d"),
                        status
                    )
                    st.success(f"Task '{name}' added successfully")
                    st.session_state.temp_data.pop("add_task", None)
                    st.rerun()
                else:
                    st.error("Task name is required")
        
        if st.button("Cancel Adding Task"):
            st.session_state.temp_data.pop("add_task", None)
            st.rerun()
    
    # Display tasks
    if tasks:
        # Convert to DataFrame for better display
        tasks_df = pd.DataFrame(tasks, columns=[
            'ID', 'Project ID', 'Name', 'Description', 'Due Date', 'Status', 'Created At'
        ])
        
        # Display tasks in a table
        st.dataframe(tasks_df[['Name', 'Due Date', 'Status']], use_container_width=True)
        
        # Task details and actions
        st.markdown('<h3>Task Details</h3>', unsafe_allow_html=True)
        
        # Select task
        task_names = [task[2] for task in tasks]
        selected_task_name = st.selectbox("Select a task", task_names)
        
        # Find the selected task
        selected_task = next((task for task in tasks if task[2] == selected_task_name), None)
        
        if selected_task:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div class="card">
                    <h3>{selected_task[2]}</h3>
                    <p><strong>Description:</strong> {selected_task[3]}</p>
                    <p><strong>Due Date:</strong> {selected_task[4]}</p>
                    <p><strong>Status:</strong> {selected_task[5]}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Task actions
                if st.button("Edit Task"):
                    st.session_state.temp_data["edit_task"] = True
                    st.session_state.temp_data["task_id"] = selected_task[0]
                
                if st.button("Delete Task"):
                    if st.checkbox("Confirm deletion"):
                        db.delete_task(selected_task[0])
                        st.success(f"Task '{selected_task[2]}' deleted successfully")
                        st.rerun()
                
                # Mark as complete button
                if selected_task[5] != "Completed":
                    if st.button("Mark as Completed"):
                        db.update_task(
                            selected_task[0],
                            selected_task[2],
                            selected_task[3],
                            selected_task[4],
                            "Completed"
                        )
                        st.success(f"Task '{selected_task[2]}' marked as completed")
                        st.rerun()
        
        # Edit task form
        if st.session_state.temp_data.get("edit_task"):
            task_id = st.session_state.temp_data.get("task_id")
            task = db.get_task(task_id)
            
            if task:
                with st.form("edit_task_form"):
                    st.markdown('<h3>Edit Task</h3>', unsafe_allow_html=True)
                    
                    name = st.text_input("Task Name", value=task[2])
                    description = st.text_area("Description", value=task[3])
                    due_date = st.date_input("Due Date", value=datetime.datetime.strptime(task[4], "%Y-%m-%d").date())
                    status = st.selectbox("Status", ["Not Started", "In Progress", "Completed"], index=["Not Started", "In Progress", "Completed"].index(task[5]))
                    
                    submit = st.form_submit_button("Update Task")
                    
                    if submit:
                        if name:
                            db.update_task(
                                task_id,
                                name,
                                description,
                                due_date.strftime("%Y-%m-%d"),
                                status
                            )
                            st.success(f"Task '{name}' updated successfully")
                            st.session_state.temp_data.pop("edit_task", None)
                            st.session_state.temp_data.pop("task_id", None)
                            st.rerun()
                        else:
                            st.error("Task name is required")
                
                if st.button("Cancel Editing Task"):
                    st.session_state.temp_data.pop("edit_task", None)
                    st.session_state.temp_data.pop("task_id", None)
                    st.rerun()
    else:
        st.info("No tasks found for this project. Add your first task.")
    
    if st.button("Back to Projects"):
        navigate_to('projects')
        st.rerun()

# Invoices page
def invoices_page():
    st.markdown('<h1 class="main-header">Invoices</h1>', unsafe_allow_html=True)
    
    # Get all projects
    projects = db.get_projects(st.session_state.user["id"])
    
    if not projects:
        st.warning("You need to add a project first")
        if st.button("Add Project"):
            navigate_to('add_project')
            st.rerun()
        return
    
    # Add invoice button
    if st.button("Create New Invoice"):
        navigate_to('add_invoice')
        st.rerun()
    
    # Get all invoices
    invoices = db.get_invoices()
    
    if invoices:
        # Filter options
        status_options = ["All"] + list(set(invoice[5] for invoice in invoices))
        selected_status = st.selectbox("Filter by Status", status_options)
        
        # Filter invoices by status
        filtered_invoices = invoices
        if selected_status != "All":
            filtered_invoices = [invoice for invoice in invoices if invoice[5] == selected_status]
        
        # Convert to DataFrame for better display
        invoices_df = pd.DataFrame(filtered_invoices, columns=[
            'ID', 'Project ID', 'Amount', 'Issue Date', 'Due Date', 
            'Status', 'Notes', 'Created At', 'Project Name', 'Client Name'
        ])
        
        # Display invoices in a table
        st.dataframe(invoices_df[['Project Name', 'Client Name', 'Amount', 'Due Date', 'Status']], use_container_width=True)
        
        # Invoice details
        st.markdown('<h2 class="sub-header">Invoice Details</h2>', unsafe_allow_html=True)
        
        # Select invoice
        invoice_ids = [f"Invoice #{invoice[0][:8]} - {invoice[8]}" for invoice in filtered_invoices]
        selected_invoice_id_display = st.selectbox("Select an invoice", invoice_ids)
        
        # Extract the actual invoice ID from the display string
        selected_invoice_id = filtered_invoices[invoice_ids.index(selected_invoice_id_display)][0]
        
        # Find the selected invoice
        selected_invoice = next((invoice for invoice in filtered_invoices if invoice[0] == selected_invoice_id), None)
        
        if selected_invoice:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div class="card">
                    <h3>Invoice #{selected_invoice[0][:8]}</h3>
                    <p><strong>Project:</strong> {selected_invoice[8]}</p>
                    <p><strong>Client:</strong> {selected_invoice[9]}</p>
                    <p><strong>Amount:</strong> ${selected_invoice[2]:,.2f}</p>
                    <p><strong>Issue Date:</strong> {selected_invoice[3]}</p>
                    <p><strong>Due Date:</strong> {selected_invoice[4]}</p>
                    <p><strong>Status:</strong> {selected_invoice[5]}</p>
                    <p><strong>Notes:</strong> {selected_invoice[6]}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Invoice actions
                if st.button("Edit Invoice"):
                    st.session_state.temp_data["invoice_id"] = selected_invoice[0]
                    navigate_to('edit_invoice')
                    st.rerun()
                
                if st.button("Delete Invoice"):
                    if st.checkbox("Confirm deletion"):
                        db.delete_invoice(selected_invoice[0])
                        st.success(f"Invoice deleted successfully")
                        st.rerun()
                
                if st.button("Record Payment"):
                    st.session_state.temp_data["invoice_id"] = selected_invoice[0]
                    navigate_to('add_payment')
                    st.rerun()
                
                # View payments button
                payments = db.get_payments(selected_invoice[0])
                if payments:
                    if st.button("View Payments"):
                        st.session_state.temp_data["invoice_id"] = selected_invoice[0]
                        navigate_to('payments')
                        st.rerun()
    else:
        st.info("No invoices found. Create your first invoice.")

# Add invoice page
def add_invoice_page():
    st.markdown('<h1 class="main-header">Create New Invoice</h1>', unsafe_allow_html=True)
    
    # Get all projects
    projects = db.get_projects(st.session_state.user["id"])
    
    if not projects:
        st.warning("You need to add a project first")
        if st.button("Add Project"):
            navigate_to('add_project')
            st.rerun()
        return
    
    with st.form("add_invoice_form"):
        # If project_id is in temp_data, preselect that project
        preselected_project_id = st.session_state.temp_data.get("project_id")
        project_names = [f"{project[3]} ({project[10]})" for project in projects]
        
        if preselected_project_id:
            preselected_project = next((project for project in projects if project[0] == preselected_project_id), None)
            if preselected_project:
                preselected_index = project_names.index(f"{preselected_project[3]} ({preselected_project[10]})")
            else:
                preselected_index = 0
        else:
            preselected_index = 0
        
        project_name = st.selectbox("Project", project_names, index=preselected_index)
        
        project_id = projects[project_names.index(project_name)][0]
        
        amount = st.number_input("Amount ($)", min_value=0.0, step=100.0)
        
        col1, col2 = st.columns(2)
        with col1:
            issue_date = st.date_input("Issue Date", value=datetime.datetime.now().date())
        with col2:
            due_date = st.date_input("Due Date", value=(datetime.datetime.now() + datetime.timedelta(days=30)).date())
        
        status = st.selectbox("Status", ["Unpaid", "Partially Paid", "Paid"])
        notes = st.text_area("Notes")
        
        submit = st.form_submit_button("Create Invoice")
        
        if submit:
            if amount > 0:
                if due_date < issue_date:
                    st.error("Due date cannot be before issue date")
                else:
                    invoice_id = db.add_invoice(
                        project_id,
                        amount,
                        issue_date.strftime("%Y-%m-%d"),
                        due_date.strftime("%Y-%m-%d"),
                        status,
                        notes
                    )
                    st.success("Invoice created successfully")
                    navigate_to('invoices')
                    st.rerun()
            else:
                st.error("Amount must be greater than zero")
    
    if st.button("Cancel"):
        navigate_to('invoices')
        st.rerun()

# Edit invoice page
def edit_invoice_page():
    st.markdown('<h1 class="main-header">Edit Invoice</h1>', unsafe_allow_html=True)
    
    invoice_id = st.session_state.temp_data.get("invoice_id")
    if not invoice_id:
        st.error("No invoice selected")
        if st.button("Back to Invoices"):
            navigate_to('invoices')
            st.experimental_rerun()
        return
    
    invoice = db.get_invoice(invoice_id)
    if not invoice:
        st.error("Invoice not found")
        if st.button("Back to Invoices"):
            navigate_to('invoices')
            st.rerun()
        return
    
    # Get all projects
    projects = db.get_projects(st.session_state.user["id"])
    
    with st.form("edit_invoice_form"):
        project_names = [f"{project[3]} ({project[10]})" for project in projects]
        current_project = next((project for project in projects if project[0] == invoice[1]), None)
        
        if current_project:
            current_project_index = project_names.index(f"{current_project[3]} ({current_project[10]})")
        else:
            current_project_index = 0
        
        project_name = st.selectbox("Project", project_names, index=current_project_index)
        project_id = projects[project_names.index(project_name)][0]
        
        amount = st.number_input("Amount ($)", min_value=0.0, step=100.0, value=float(invoice[2]))
        
        col1, col2 = st.columns(2)
        with col1:
            issue_date = st.date_input("Issue Date", value=datetime.datetime.strptime(invoice[3], "%Y-%m-%d").date())
        with col2:
            due_date = st.date_input("Due Date", value=datetime.datetime.strptime(invoice[4], "%Y-%m-%d").date())
        
        status = st.selectbox("Status", ["Unpaid", "Partially Paid", "Paid"], index=["Unpaid", "Partially Paid", "Paid"].index(invoice[5]))
        notes = st.text_area("Notes", value=invoice[6])
        
        submit = st.form_submit_button("Update Invoice")
        
        if submit:
            if amount > 0:
                if due_date < issue_date:
                    st.error("Due date cannot be before issue date")
                else:
                    db.update_invoice(
                        invoice_id,
                        amount,
                        issue_date.strftime("%Y-%m-%d"),
                        due_date.strftime("%Y-%m-%d"),
                        status,
                        notes
                    )
                    st.success("Invoice updated successfully")
                    navigate_to('invoices')
                    st.rerun()
            else:
                st.error("Amount must be greater than zero")
    
    if st.button("Cancel"):
        navigate_to('invoices')
        st.rerun()

# Payments page
def payments_page():
    st.markdown('<h1 class="main-header">Payments</h1>', unsafe_allow_html=True)
    
    invoice_id = st.session_state.temp_data.get("invoice_id")
    if not invoice_id:
        st.error("No invoice selected")
        if st.button("Back to Invoices"):
            navigate_to('invoices')
            st.rerun()
        return
    
    invoice = db.get_invoice(invoice_id)
    if not invoice:
        st.error("Invoice not found")
        if st.button("Back to Invoices"):
            navigate_to('invoices')
            st.rerun()
        return
    
    st.markdown(f'<h2 class="sub-header">Payments for Invoice #{invoice[0][:8]}</h2>', unsafe_allow_html=True)
    
    # Display invoice details
    st.markdown(f"""
    <div class="card">
        <h3>Invoice Details</h3>
        <p><strong>Project:</strong> {invoice[8]}</p>
        <p><strong>Client:</strong> {invoice[9]}</p>
        <p><strong>Amount:</strong> ${invoice[2]:,.2f}</p>
        <p><strong>Status:</strong> {invoice[5]}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Add payment button
    if st.button("Record New Payment"):
        navigate_to('add_payment')
        st.rerun()
    
    # Get all payments for the invoice
    payments = db.get_payments(invoice_id)
    
    if payments:
        # Calculate total paid
        total_paid = sum(payment[2] for payment in payments)
        remaining = float(invoice[2]) - total_paid
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>${total_paid:,.2f}</h3>
                <p>Total Paid</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>${remaining:,.2f}</h3>
                <p>Remaining</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Convert to DataFrame for better display
        payments_df = pd.DataFrame(payments, columns=[
            'ID', 'Invoice ID', 'Amount', 'Payment Date', 'Payment Method', 'Notes', 'Created At'
        ])
        
        # Display payments in a table
        st.dataframe(payments_df[['Amount', 'Payment Date', 'Payment Method']], use_container_width=True)
        
        # Payment details
        st.markdown('<h3>Payment Details</h3>', unsafe_allow_html=True)
        
        # Select payment
        payment_ids = [f"Payment of ${payment[2]:,.2f} on {payment[3]}" for payment in payments]
        selected_payment_id_display = st.selectbox("Select a payment", payment_ids)
        
        # Extract the actual payment ID
        selected_payment_id = payments[payment_ids.index(selected_payment_id_display)][0]
        
        # Find the selected payment
        selected_payment = next((payment for payment in payments if payment[0] == selected_payment_id), None)
        
        if selected_payment:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div class="card">
                    <h3>Payment of ${selected_payment[2]:,.2f}</h3>
                    <p><strong>Date:</strong> {selected_payment[3]}</p>
                    <p><strong>Method:</strong> {selected_payment[4]}</p>
                    <p><strong>Notes:</strong> {selected_payment[5]}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Payment actions
                if st.button("Edit Payment"):
                    st.session_state.temp_data["payment_id"] = selected_payment[0]
                    navigate_to('edit_payment')
                    st.rerun()
                
                if st.button("Delete Payment"):
                    if st.checkbox("Confirm deletion"):
                        db.delete_payment(selected_payment[0])
                        st.success("Payment deleted successfully")
                        st.rerun()
    else:
        st.info("No payments recorded for this invoice.")
    
    if st.button("Back to Invoices"):
        navigate_to('invoices')
        st.rerun()

# Add payment page
def add_payment_page():
    st.markdown('<h1 class="main-header">Record Payment</h1>', unsafe_allow_html=True)
    
    invoice_id = st.session_state.temp_data.get("invoice_id")
    if not invoice_id:
        st.error("No invoice selected")
        if st.button("Back to Invoices"):
            navigate_to('invoices')
            st.rerun()
        return
    
    invoice = db.get_invoice(invoice_id)
    if not invoice:
        st.error("Invoice not found")
        if st.button("Back to Invoices"):
            navigate_to('invoices')
            st.rerun()
        return
    
    # Calculate remaining amount
    payments = db.get_payments(invoice_id)
    total_paid = sum(payment[2] for payment in payments) if payments else 0
    remaining = float(invoice[2]) - total_paid
    
    st.markdown(f"""
    <div class="card">
        <h3>Invoice Details</h3>
        <p><strong>Project:</strong> {invoice[8]}</p>
        <p><strong>Client:</strong> {invoice[9]}</p>
        <p><strong>Total Amount:</strong> ${invoice[2]:,.2f}</p>
        <p><strong>Paid So Far:</strong> ${total_paid:,.2f}</p>
        <p><strong>Remaining:</strong> ${remaining:,.2f}</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("add_payment_form"):
        amount = st.number_input("Payment Amount ($)", min_value=0.01, max_value=float(remaining), step=0.01, value=float(remaining))
        payment_date = st.date_input("Payment Date", value=datetime.datetime.now().date())
        payment_method = st.selectbox("Payment Method", ["Credit Card", "Bank Transfer", "Cash", "Check", "PayPal", "Other"])
        notes = st.text_area("Notes")
        
        submit = st.form_submit_button("Record Payment")
        
        if submit:
            if amount > 0 and amount <= remaining:
                payment_id = db.add_payment(
                    invoice_id,
                    amount,
                    payment_date.strftime("%Y-%m-%d"),
                    payment_method,
                    notes
                )
                st.success("Payment recorded successfully")
                navigate_to('payments')
                st.rerun()
            else:
                st.error("Invalid payment amount")
    
    if st.button("Cancel"):
        navigate_to('payments')
        st.rerun()

# Edit payment page
def edit_payment_page():
    st.markdown('<h1 class="main-header">Edit Payment</h1>', unsafe_allow_html=True)
    
    payment_id = st.session_state.temp_data.get("payment_id")
    if not payment_id:
        st.error("No payment selected")
        if st.button("Back to Payments"):
            navigate_to('payments')
            st.rerun()
        return
    
    payment = db.get_payment(payment_id)
    if not payment:
        st.error("Payment not found")
        if st.button("Back to Payments"):
            navigate_to('payments')
            st.rerun()
        return
    
    invoice_id = payment[1]
    invoice = db.get_invoice(invoice_id)
    
    # Calculate maximum amount (original amount + remaining)
    payments = db.get_payments(invoice_id)
    total_paid = sum(p[2] for p in payments if p[0] != payment_id) if payments else 0
    max_amount = float(invoice[2]) - total_paid
    
    with st.form("edit_payment_form"):
        amount = st.number_input("Payment Amount ($)", min_value=0.01, max_value=float(max_amount), step=0.01, value=float(payment[2]))
        payment_date = st.date_input("Payment Date", value=datetime.datetime.strptime(payment[3], "%Y-%m-%d").date())
        payment_method = st.selectbox("Payment Method", ["Credit Card", "Bank Transfer", "Cash", "Check", "PayPal", "Other"], index=["Credit Card", "Bank Transfer", "Cash", "Check", "PayPal", "Other"].index(payment[4]))
        notes = st.text_area("Notes", value=payment[5])
        
        submit = st.form_submit_button("Update Payment")
        
        if submit:
            if amount > 0 and amount <= max_amount:
                db.update_payment(
                    payment_id,
                    amount,
                    payment_date.strftime("%Y-%m-%d"),
                    payment_method,
                    notes
                )
                st.success("Payment updated successfully")
                navigate_to('payments')
                st.rerun()
            else:
                st.error("Invalid payment amount")
    
    if st.button("Cancel"):
        navigate_to('payments')
        st.rerun()

# Settings page
def settings_page():
    st.markdown('<h1 class="main-header">Settings</h1>', unsafe_allow_html=True)
    
    # User profile
    st.markdown('<h2 class="sub-header">User Profile</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="card">
            <h3>{st.session_state.user["full_name"]}</h3>
            <p><strong>Username:</strong> {st.session_state.user["username"]}</p>
            <p><strong>Email:</strong> {st.session_state.user["email"]}</p>
            <p><strong>Subscription:</strong> {st.session_state.user["subscription_type"].capitalize()}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Subscription
    st.markdown('<h2 class="sub-header">Subscription</h2>', unsafe_allow_html=True)
    
    if st.session_state.user["subscription_type"] == "free":
        st.markdown("""
        <div class="card">
            <h3>Upgrade to Premium</h3>
            <p>Get access to premium features:</p>
            <ul>
                <li>Unlimited clients and projects</li>
                <li>Advanced reporting and analytics</li>
                <li>Invoice templates and customization</li>
                <li>Priority support</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="card">
                <h3>Monthly Plan</h3>
                <h2>$9.99/month</h2>
                <p>Billed monthly</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Subscribe Monthly"):
                st.session_state.temp_data["subscription_plan"] = "monthly"
                st.session_state.temp_data["show_payment_form"] = True
        
        with col2:
            st.markdown("""
            <div class="card">
                <h3>Annual Plan</h3>
                <h2>$99/year</h2>
                <p>Save ~17%</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Subscribe Annually"):
                st.session_state.temp_data["subscription_plan"] = "annual"
                st.session_state.temp_data["show_payment_form"] = True
        
        # Payment form
        if st.session_state.temp_data.get("show_payment_form"):
            plan_type = st.session_state.temp_data.get("subscription_plan")
            
            st.markdown(f'<h3>Payment Details for {plan_type.capitalize()} Plan</h3>', unsafe_allow_html=True)
            
            with st.form("payment_form"):
                card_number = st.text_input("Card Number")
                
                col1, col2 = st.columns(2)
                with col1:
                    expiry = st.text_input("Expiry Date (MM/YY)")
                with col2:
                    cvv = st.text_input("CVV", type="password")
                
                submit = st.form_submit_button("Process Payment")
                
                if submit:
                    if len(card_number) == 16 and len(expiry) == 5 and len(cvv) == 3:
                        # Simulate payment processing
                        result = payment.upgrade_subscription(
                            st.session_state.user["id"],
                            plan_type,
                            {
                                "card_number": card_number,
                                "expiry": expiry,
                                "cvv": cvv
                            }
                        )
                        
                        if result["success"]:
                            st.success(f"Subscription upgraded to Premium! Valid until {result['subscription_end_date']}")
                            st.session_state.user["subscription_type"] = "premium"
                            st.session_state.temp_data.pop("show_payment_form", None)
                            st.session_state.temp_data.pop("subscription_plan", None)
                            st.rerun()
                        else:
                            st.error(result["error"])
                    else:
                        st.error("Invalid payment details")
            
            if st.button("Cancel Payment"):
                st.session_state.temp_data.pop("show_payment_form", None)
                st.session_state.temp_data.pop("subscription_plan", None)
                st.rerun()
    else:
        st.markdown("""
        <div class="card">
            <h3>Premium Subscription</h3>
            <p>You are currently on the Premium plan. Enjoy all the premium features!</p>
        </div>
        """, unsafe_allow_html=True)

# Main app
def main():
    # Sidebar
    with st.sidebar:
        display_logo()
        
        st.markdown(f"<h3>Welcome, {st.session_state.user['full_name'] if st.session_state.user else 'Guest'}</h3>", unsafe_allow_html=True)
        
        if st.session_state.user:
            st.markdown(f"<p>Subscription: {st.session_state.user['subscription_type'].capitalize()}</p>", unsafe_allow_html=True)
            
            st.markdown("### Navigation")
            
            if st.button("Dashboard"):
                navigate_to('dashboard')
                st.rerun()
            
            if st.button("Clients"):
                navigate_to('clients')
                st.rerun()
            
            if st.button("Projects"):
                navigate_to('projects')
                st.rerun()
            
            if st.button("Invoices"):
                navigate_to('invoices')
                st.rerun()
            
            st.markdown("### Settings")
            
            if st.button("Account Settings"):
                navigate_to('settings')
                st.rerun()
            
            if st.button("Logout"):
                st.session_state.user = None
                navigate_to('login')
                st.rerun()
    
    # Main content
    if not st.session_state.user:
        if st.session_state.page == 'login':
            login_page()
        elif st.session_state.page == 'register':
            register_page()
    else:
        if st.session_state.page == 'dashboard':
            dashboard_page()
        elif st.session_state.page == 'clients':
            clients_page()
        elif st.session_state.page == 'add_client':
            add_client_page()
        elif st.session_state.page == 'edit_client':
            edit_client_page()
        elif st.session_state.page == 'projects':
            projects_page()
        elif st.session_state.page == 'add_project':
            add_project_page()
        elif st.session_state.page == 'edit_project':
            edit_project_page()
        elif st.session_state.page == 'tasks':
            tasks_page()
        elif st.session_state.page == 'invoices':
            invoices_page()
        elif st.session_state.page == 'add_invoice':
            add_invoice_page()
        elif st.session_state.page == 'edit_invoice':
            edit_invoice_page()
        elif st.session_state.page == 'payments':
            payments_page()
        elif st.session_state.page == 'add_payment':
            add_payment_page()
        elif st.session_state.page == 'edit_payment':
            edit_payment_page()
        elif st.session_state.page == 'settings':
            settings_page()

if __name__ == "__main__":
    main()





