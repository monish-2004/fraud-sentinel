# Fraud Sentinel - Authentication & MySQL Setup Guide

This guide will help you set up user registration, login, and MySQL database storage for your Fraud Sentinel application.

## Prerequisites

- MySQL Server installed and running
- Python 3.8+
- Node.js 14+

## Step 1: MySQL Setup

### 1.1 Create the Database

Open MySQL Command Line Client and run:

```sql
-- Create the database
CREATE DATABASE fraud_sentinel;

-- Use the database
USE fraud_sentinel;

-- Verify it's created
SHOW DATABASES;
```

### 1.2 Verify Tables Creation

The application will automatically create the required tables (`users` and `transactions`) on startup. You can verify them with:

```sql
USE fraud_sentinel;
SHOW TABLES;
DESCRIBE users;
DESCRIBE transactions;
```

## Step 2: Environment Configuration

Copy the `.env.example` file to `.env` in the backend directory:

```bash
cd fraud-sentinel/backend
cp .env.example .env
```

Edit `.env` with your MySQL credentials:

```env
# MySQL Database Configuration
DB_HOST=localhost          # Your MySQL server hostname
DB_PORT=3306              # Default MySQL port
DB_USER=root              # Your MySQL username
DB_PASSWORD=your_password # Your MySQL password
DB_NAME=fraud_sentinel    # Database name

# JWT Secret Key (Generate a strong random string for production)
SECRET_KEY=your-super-secret-key-change-this

# API Configuration
REACT_APP_API_URL=http://localhost:8000

# Groq API Key (if using Groq)
GROQ_API_KEY=your_key_here
```

## Step 3: Install Backend Dependencies

```bash
cd fraud-sentinel/backend
pip install -r requirements.txt
```

## Step 4: Start the Backend

```bash
cd fraud-sentinel/backend
python -m uvicorn main:app --reload
```

You should see output indicating:
```
✅ Connected to MySQL database
✅ RAG knowledge base seeded with fraud patterns
```

## Step 5: Install and Start Frontend

### 5.1 Install Frontend Dependencies

```bash
cd fraud-sentinel/frontend
npm install
```

### 5.2 Start Frontend

```bash
npm start
```

The app will open at `http://localhost:3000`

## Authentication Flow

### 1. Register New User

1. Navigate to `http://localhost:3000/register`
2. Fill in:
   - Username (unique)
   - Email (unique)
   - Full Name (optional)
   - Password (min 6 characters)
   - Confirm Password
3. Click "Create Account"
4. You'll be automatically logged in and redirected to the dashboard

### 2. Login

1. Navigate to `http://localhost:3000/login`
2. Enter your username/email and password
3. Click "Sign In"
4. Access the dashboard with your authenticated session

### 3. Dashboard

The dashboard will now:
- Display your personal transaction analysis history
- Store all analyzed transactions in MySQL (per-user)
- Keep your data persistent across sessions

### 4. Logout

Click the "Logout" button in the top-right corner to log out and redirect to the login page.

## API Endpoints

### Authentication Endpoints

- **POST** `/api/auth/register`
  ```json
  {
    "username": "john_doe",
    "email": "john@example.com",
    "password": "password123",
    "full_name": "John Doe"
  }
  ```
  Returns: `{ access_token, token_type, user_id, username }`

- **POST** `/api/auth/login`
  ```json
  {
    "username": "john_doe",
    "password": "password123"
  }
  ```
  Returns: `{ access_token, token_type, user_id, username }`

- **GET** `/api/auth/me`
  Requires: `Authorization: Bearer <token>`
  Returns: `{ id, username, email, full_name }`

### Protected Endpoints

All data endpoints now support authentication:

- **POST** `/api/analyze` - Analyzes and stores transaction per user
- **GET** `/api/dashboard/stats` - Returns user-specific statistics
- Send Authorization header: `Authorization: Bearer <access_token>`

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### Transactions Table

```sql
CREATE TABLE transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    transaction_id VARCHAR(255) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    merchant VARCHAR(255),
    merchant_category VARCHAR(100),
    location VARCHAR(255),
    analysis JSON,
    risk_level VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

## Troubleshooting

### Connection Error: "Could not connect to MySQL"

1. Verify MySQL Server is running:
   ```bash
   # On Windows (PowerShell)
   Get-Service MySQL80  # or your MySQL version
   ```

2. Check credentials in `.env`:
   ```bash
   # Test MySQL connection
   mysql -h localhost -u root -p
   ```

3. If MySQL is not running, start it:
   ```bash
   # Windows
   net start MySQL80
   
   # macOS (Homebrew)
   brew services start mysql
   
   # Linux (systemctl)
   sudo systemctl start mysql
   ```

### Port 3306 Already in Use

Change the port in `.env`:
```env
DB_PORT=3307
```

And update MySQL command:
```bash
mysql -h localhost -P 3307 -u root -p
```

### "Username already exists" Error

Each username must be unique. Try registering with a different username.

### Token Expired

Tokens expire after 30 minutes. Log in again to get a new token.

## Verify Everything Works

1. Open `http://localhost:3000/register`
2. Create a test account
3. Log in with the credentials
4. Go to Analyze page and analyze a transaction
5. Check Dashboard - should show your transaction
6. Run this SQL query to verify data stored:

```sql
USE fraud_sentinel;
SELECT u.username, t.transaction_id, t.amount, t.risk_level 
FROM users u 
LEFT JOIN transactions t ON u.id = t.user_id;
```

## Security Notes

⚠️ **For Production:**

1. Change the `SECRET_KEY` to a strong random string
2. Use environment variables for database credentials
3. Enable HTTPS for API calls
4. Implement password strength requirements
5. Add rate limiting on auth endpoints
6. Use database connection pooling
7. Regularly backup your MySQL database

## Next Steps

- Implement email verification for new accounts
- Add password reset functionality
- Add role-based access control (admin, analyst, etc.)
- Implement audit logging for all transactions
- Add 2FA (Two-Factor Authentication)

For more information, see the main [README.md](README.md)
