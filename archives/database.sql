show databases;
create database arami;
use arami;
show tables;

SELECT * FROM users;
SELECT * FROM modules;

alter table users
add password varchar(255);
create table if not exists users (
	user_id INT AUTO_INCREMENT PRIMARY KEY,
	user_name VARCHAR(255),
	proficiency DOUBLE,
    password varchar(255)
    );

create table if not exists word_library (
	word_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id int,
    word VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    );

CREATE TABLE IF NOT EXISTS modules (
    module_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    module_name VARCHAR(255),
    completion_status BOOL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS levels (
    level_id INT AUTO_INCREMENT PRIMARY KEY,
    module_id INT,
    level_num INT,
    completion_status BOOL,
    FOREIGN KEY (module_id) REFERENCES modules(module_id)
);

CREATE TABLE IF NOT EXISTS chapter_tests (
    chapter_test_id INT AUTO_INCREMENT PRIMARY KEY,
    module_id INT,
    chapter_test_name VARCHAR(255),
    completion_status BOOL,
    FOREIGN KEY (module_id) REFERENCES modules(module_id)
);
    
create table if not exists questions_wrong (
	user_id INT,
	question VARCHAR(255),
	answer VARCHAR(255),
	FOREIGN KEY (user_id) REFERENCES users(user_id)
    );

CREATE TABLE IF NOT EXISTS questions_correct (
	user_id INT,
	question VARCHAR(255),
	answer VARCHAR(255),
	FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    
CREATE TABLE IF NOT EXISTS word_library (
	user_id INT,
	word VARCHAR(255),
	FOREIGN KEY (user_id) REFERENCES users(user_id)
    );

CREATE TABLE IF NOT EXISTS achievements (
	user_id INT,
	achievement_name VARCHAR(255),
	unlocked BOOLEAN,
	FOREIGN KEY (user_id) REFERENCES users(user_id)
    );


