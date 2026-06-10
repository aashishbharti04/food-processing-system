import mysql.connector as sql
conn=sql.connect(host="localhost", user="root", passwd="manager", database="food")
if conn.is_connected():
    print("sucessfully connected")
c1= conn.cursor()
c1.execute('create table myc(cust_name varchar(30),account_no int(50))')
print('table created')
