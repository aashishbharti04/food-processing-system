import mysql.connector as sql
conn=sql.connect(host="localhost", user="root", passwd="manager", database="food")
if conn.is_connected():
    print("sucessfully connected")
c1= conn.cursor()
c1.execute('create table sales(f_name varchar(30),price float(10),address varchar(100))')
print('table created')
