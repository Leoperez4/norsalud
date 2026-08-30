-- Crea la base de datos y el usuario que usa Django (ver .env.example).
-- Correr una sola vez, la primera vez que se instala el proyecto en un computador nuevo.
--
-- Con XAMPP (MariaDB), desde una terminal:
--   C:\xampp\mysql\bin\mysql.exe -u root < setup_db.sql
--
-- O pegando el contenido directo en la pestaña "SQL" de phpMyAdmin (http://localhost/phpmyadmin/).

CREATE DATABASE IF NOT EXISTS norsalud CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
CREATE USER IF NOT EXISTS 'norsalud_user'@'localhost' IDENTIFIED BY 'norsalud_pass';
GRANT ALL PRIVILEGES ON norsalud.* TO 'norsalud_user'@'localhost';
