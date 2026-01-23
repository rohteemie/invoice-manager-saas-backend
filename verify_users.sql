-- SQL script to verify all users whose email starts with 'user' (for MySQL)
UPDATE users SET is_verified = TRUE WHERE email LIKE 'user%@%';