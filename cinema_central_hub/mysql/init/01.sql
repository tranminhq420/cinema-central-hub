DROP USER IF EXISTS 'newuser'@'%';

CREATE USER 'newuser'@'%'
IDENTIFIED WITH mysql_native_password
BY '123quan123';

GRANT ALL PRIVILEGES ON hanoicinema.* 
TO 'newuser'@'%';

FLUSH PRIVILEGES;
