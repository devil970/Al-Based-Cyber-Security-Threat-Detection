CREATE DATABASE IF NOT EXISTS securitysystem;
USE securitysystem;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    mobile VARCHAR(15) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email_verified TINYINT(1) DEFAULT 0,
    mobile_verified TINYINT(1) DEFAULT 0,
    status ENUM('active','locked','restricted') DEFAULT 'active',
    failed_attempts INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS otp_store (
    id INT AUTO_INCREMENT PRIMARY KEY,
    identifier VARCHAR(150) NOT NULL,
    otp VARCHAR(6) NOT NULL,
    otp_type ENUM('email','mobile') NOT NULL,
    expires_at DATETIME NOT NULL,
    used TINYINT(1) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS login_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    ip_address VARCHAR(45),
    login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    logout_time DATETIME DEFAULT NULL,
    session_duration INT DEFAULT NULL COMMENT 'seconds',
    status ENUM('success','failed','locked') NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(150),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS support_tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_number VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    problem TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);


-- Default admin: username=ADMIN, password=Nehaadmin@123
-- Password stored as bcrypt hash
INSERT IGNORE INTO admin (username, password_hash, email)
VALUES ('ADMIN', '$2b$12$/jOuFvssuQ0iKnQChBj9Hev900.EJpgmCdWWTWQouABfWIR7G2BMS', 'walkeneha310@gmail.com');
