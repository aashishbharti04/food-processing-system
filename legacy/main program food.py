import mysql.connector as sql
conn=sql.connect(host="localhost", user="root", passwd="manager", database="food")
if conn.is_connected():
    print("sucessfully connected")


print("                          ORDER YOUR FOOD HERE")

c1=conn.cursor()
print("1.CREATE YOUR ACCOUNT")
print("2.LOG IN")
print("3.EXIT")
choice=int(input("ENTER YOUR CHOICE:"))
if choice ==1:
    v_cust_name=input("enter your name:")
    v_account_no=int(input("enter your own account number:"))
    v_address=input("enter your address:")
    v_password=int(input("enter your password:"))
    v_SQL_insert="insert into myc values('"+v_cust_name+"',"+str(v_account_no)+",'"+v_address+"' ,"+str (v_password)+")"
    c1.execute(v_SQL_insert)
    conn.commit()
    print("ACCOUNT CREATED")
if choice==3:
    print("THANK YOU FOR VISITING")
if choice==2:
    print('')
    print('TO LOGIN FILL THIS DETAILS')
    print('')
    cust_name=input('enter your name')
    print('')
    v_account_no=int(input('enter your accont no'))
    print(' ')
    v_password=int(input('enter your password'))
    print(' ')
    c1=conn.cursor()
    c1.execute('select * from myc')
    data=c1.fetchall()
    count=c1.rowcount
    for row in data:
        if (cust_name in row) and (v_account_no in row):
            print(' ')
            print(' ')
            print('WELCOME TO YOUR FOOD SERVICE')
            print(' ')
            print(' ')
            print('TO SEE CUSTMER DETAILS PRESS            :1          ')
            print(' ')
            print(' TO UPDATE DETAILS PRESS        :2           ')
            print(' ')
            print('  TO EXIT PRESS :3')
            print(' ')
            print('TO ORDER FOOD:4')
            print(' ')
            print('TO SEE ORDERED FOOD:5   ')
            print(' ')
            print('WANT TO RATE US ?:6')
            print(' ')
            c2=int(input('enter your choice'))
            if (c2==1):
                c1=conn.cursor()
                c1.execute('select * from myc')
                data=c1.fetchall()
                count=c1.rowcount
                print('total custmer is',count)
                for row in data:
                    print(row)
                print("VISIT AGAIN")
            elif (c2==2):
                print('')
                print('TO UPDATE FILL THIS')
                print('')
                v_cust_name=input('enter name    :')
                print('')
                v_acount_no=int(input("enter account number:"))
                c1=conn.cursor()
                #c1.execute('create table myc('"+v_cust_name+"',"+str(v_account_no)+")"
                update_dtails="insert into myc values('"+v_cust_name+"',"+str(v_account_no)+",'"+v_address+"' ,"+str (v_password)+")"
                c1.execute(update_dtails)
                conn.commit()
                print('YOUR DETAILS ARE SUCESSFULLY UPDATED')
            elif (c2==3):
                print('THANK YOU FOR VISITING')
            elif(c2==4):
                 v_f_name=input("enter the name of food:")
                 v_price=int(input("enter the cost of your food:"))
                 v_address=input("enter your address:")
                 v_cust_name=input("enter your name:")
                 v_account_no=int(input("enter your account no:"))
                 v_SQL_insert="insert into sales values("+"'"+ v_f_name+"'"+","+"'"+str(v_price)+"'"+","+"'"+v_address+"'"+","+"'"+v_cust_name+"'"+","+str(v_account_no)+")"
                 c1.execute(v_SQL_insert)
                 conn.commit()
                 print("SUCESSFULLY ORDERED")
            elif(c2==5):
                  c1=conn.cursor()
                  c1.execute('select * from sales')
                  data=c1.fetchall()
                  count=c1.rowcount
                  print('total order food  is',count)
                  for row in data:
                     print(row)
                  print("VISIT AGAIN")
            elif (c2==6):
                print('RATE US FOR YOUR SERVICE')
                rating=int(input("ENTER YOUR RATING:"))
                print('THANK FOR RATING')
            else:
                print("ERROR,ERROR...........")
                 
               
                 
            
