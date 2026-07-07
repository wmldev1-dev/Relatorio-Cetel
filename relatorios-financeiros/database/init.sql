CREATE DATABASE IF NOT EXISTS relatorios_financeiros
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'relatorios_user'@'%' IDENTIFIED BY 'relatorios123';

GRANT ALL PRIVILEGES ON relatorios_financeiros.* TO 'relatorios_user'@'%';

FLUSH PRIVILEGES;
