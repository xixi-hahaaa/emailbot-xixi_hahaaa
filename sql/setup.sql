CREATE DATABASE IF NOT EXISTS emails;

USE emails;

CREATE TABLE IF NOT EXISTS hydro_gmail (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date_day DATE NOT NULL,
    sender_email VARCHAR(100) NOT NULL,
    details VARCHAR(255),
    paid BIT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);




