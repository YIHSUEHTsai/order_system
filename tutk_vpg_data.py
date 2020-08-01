#!/usr/bin/python3
# -*- coding: utf-8 -*-
import MySQLdb
import os
import sys
import csv
import pandas as pd
import subprocess
import time
import requests
import sqlite3
import datetime 

file_path = "/home/ubuntu/op_script/tutk_vpg_data/"
#file_path = "/home/ethan/Desktop/tutk_vpg_data/"
master_list = ["m1","m2","m3","m4","m5","m6","m7","m9","m10"]
service_mode_list = ['[1] add_sessionkey', '[2] create_vpg_inventory', '[3] update_vpg_inventory', '[4] check_vpg_inventory', '[5] migrate_vpg', '[6] delete_vpg', '[7] create_vpg_inventory_test']
update_vpg_inventory_service_mode_list = ['[1] start_date', '[2] expiration_date', '[3] server_bandwidth_service_level']
create_vpg_mode_list = ["[1] vpg", "[2] vpg_list"]
server_bandwidth_service_level_list = ['[1] A', '[2] B', '[3] C', '[4] D', '[5] E', '[6] F', '[7] G']
vpg_login_time_threshold = 12

def add_sessionkey(p2p_domain, p2p_ip_address, session_key):
    conn = sqlite3.connect(file_path + 'tutk_vpg_data.db')
    c = conn.cursor()
    sqlite_cmd = "INSERT INTO p2pdomain_sessionkey_mapping_table (p2p_domain, p2p_ip_address, session_key) SELECT "+"'"+p2p_domain+"','"+p2p_ip_address+"','"+session_key+"'"+" where not exists (select * from p2pdomain_sessionkey_mapping_table where p2p_domain="+"'"+p2p_domain+"'"+");"
    print (sqlite_cmd)
    cursor = c.execute(sqlite_cmd)
    conn.commit()
    conn.close()
    print ("add sessionley success!")

def create_vpg_inventory_test(p2p_domain):
    csv_file = file_path + "vpg.csv"
    vpg_csv_data = pd.read_csv(csv_file)

    db = MySQLdb.connect(db='urp',host='192.168.5.213',user='analysis',passwd='eEtm9a3jHK9m6Umc',port=3306,charset='utf8')
    cursor = db.cursor()

    conn = sqlite3.connect(file_path + 'tutk_vpg_data.db')
    c = conn.cursor()

    sqlite_cmd_list = []
    mysql_cmd_list = []
    vpg_list = []

    file = open(file_path+"hostlist/"+p2p_domain+"/hostlist", mode = 'r', encoding = 'utf-8-sig')
    lines = file.readlines()
    file.close()

    server_bandwidth_service_level = ""
    for line in lines:
        vid = line.split(",",4)[0].split(":",3)[0]
        pid = line.split(",",4)[0].split(":",3)[1]
        gid = line.split(",",4)[0].split(":",3)[2]
        start_date = line.split(",",4)[1]
        expiration_date = line.split(",",4)[2]
        buy_uid_count = line.split(",",4)[3]

        vid_dec = int(vid,16)
        pid_dec = int(pid,16)
        gid_dec = int(gid,16)

        for vpg_csv_data_index in range(len(vpg_csv_data)):
            vid_hex_from_csv = vpg_csv_data['vid'][vpg_csv_data_index]
            pid_hex_from_csv = vpg_csv_data['pid'][vpg_csv_data_index]
            gid_hex_from_csv = vpg_csv_data['gid'][vpg_csv_data_index]

            vid_dec_from_csv = int(vid_hex_from_csv,16)
            pid_dec_from_csv = int(pid_hex_from_csv,16)
            gid_dec_from_csv = int(gid_hex_from_csv,16)

            if (vid_dec == vid_dec_from_csv and pid_dec == pid_dec_from_csv and gid_dec == gid_dec_from_csv):
                server_bandwidth_service_level = vpg_csv_data['server_bandwidth_service_level'][vpg_csv_data_index]
                break

        cmd = "SELECT customer_name FROM urp_vid WHERE vid='" + str(vid_dec) + "';"
        cursor.execute(cmd)
        customer_name = cursor.fetchall()[0][0]
        print (customer_name)
        
        #INSERT customer_vpg_inventory_table
        sqlite_cmd = "INSERT INTO customer_vpg_inventory_table (p2p_domain, customer_name, vid, pid, gid, start_date, expiration_date, server_bandwidth_service_level, buy_uid_count) SELECT '"+str(p2p_domain)+"','"+str(customer_name)+"','"+str(vid)+"','"+str(pid)+"','"+str(gid)+"'"+",'"+str(start_date)+"','"+str(expiration_date)+"','"+str(server_bandwidth_service_level)+"','"+str(buy_uid_count)+"' where not exists (select * from customer_vpg_inventory_table where p2p_domain='"+p2p_domain+"' and vid="+"'"+vid+"'"+" and pid='"+pid+"'"+" and gid='"+gid+"');"
        c.execute(sqlite_cmd)

        cmd = "INSERT INTO vpg_info (p2p_domain, customer_name, vid, pid, gid, start_date, expiration_date, server_bandwidth_service_level, buy_uid_count) VALUES ('"+str(p2p_domain)+"','"+str(customer_name)+"','"+str(vid)+"','"+str(pid)+"','"+str(gid)+"','"+str(start_date)+"','"+str(expiration_date)+"','"+str(server_bandwidth_service_level)+"',"+str(buy_uid_count)+");"
        mysql_cmd_list.append(cmd)
        
        print ("add customer_vpg_inventory_table success!")

        #INSERT master1_vpg_logintime_status_table
        for master_index in range(len(master_list)):
            master_name = master_list[master_index]
            sqlite_cmd = "INSERT INTO "+master_name+"_vpg_logintime_status_table (p2p_domain, vid, pid, gid) SELECT '"+p2p_domain+"','"+vid+"','"+pid+"','"+gid+"'"+" where not exists (select * from "+master_name+"_vpg_logintime_status_table where p2p_domain='"+p2p_domain+"' and vid="+"'"+vid+"'"+" and pid='"+pid+"'"+" and gid='"+gid+"');"
            sqlite_cmd_list.append(sqlite_cmd)

        for index in range(len(sqlite_cmd_list)):
            sqlite_cmd = sqlite_cmd_list[index]
            c.execute(sqlite_cmd)

        for mysql_cmd_index in range(len(mysql_cmd_list)):
            mysql_cmd = mysql_cmd_list[mysql_cmd_index]
            print (mysql_cmd)
            cursor.execute(mysql_cmd)
            db.commit()

        sqlite_cmd_list.clear()
        mysql_cmd_list.clear()

    conn.commit()
    conn.close()

def create_vpg_inventory(p2p_domain_list, hostlist, vid, pid, gid, start_date, expiration_date, server_bandwidth_service_level, service_mode, buy_uid_count):
    db = MySQLdb.connect(db='urp',host='192.168.5.213',user='analysis',passwd='eEtm9a3jHK9m6Umc',port=3306,charset='utf8')
    cursor = db.cursor()

    conn = sqlite3.connect(file_path + 'tutk_vpg_data.db')
    c = conn.cursor()

    sqlite_cmd_list = []
    vpg_list = []

    if (service_mode == "vpg"):
        vpg = vid+":"+pid+":"+gid
        vpg_list.append(vpg)

    elif (service_mode == "vpg_list"):
        file = open(file_path+"hostlist/"+hostlist, mode = 'r', encoding = 'utf-8-sig')
        lines = file.readlines()
        file.close()

        for line in lines:
            vpg = line[0:14]
            vpg_list.append(vpg)

    for index in range(len(vpg_list)):
        vpg = vpg_list[index]
        vid = vpg.split(":",3)[0]
        pid = vpg.split(":",3)[1]
        gid = vpg.split(":",3)[2]
        print ("Insert db vpg:",vid,":",pid,":",gid)

        vid_dec = int(vid,16)
        pid_dec = int(pid,16)
        gid_dec = int(gid,16)

        cmd = "SELECT customer_name FROM urp_vid WHERE vid='" + str(vid_dec) + "';"
        cursor.execute(cmd)
        customer_name = cursor.fetchall()[0][0]

        for p2p_domain_index in range(len(p2p_domain_list)):
            p2p_domain = p2p_domain_list[p2p_domain_index]

            #INSERT customer_vpg_inventory_table
            sqlite_cmd = "INSERT INTO customer_vpg_inventory_table (p2p_domain, customer_name, vid, pid, gid, start_date, expiration_date, server_bandwidth_service_level, buy_uid_count) SELECT '"+str(p2p_domain)+"','"+str(customer_name)+"','"+str(vid)+"','"+str(pid)+"','"+str(gid)+"'"+",'"+str(start_date)+"','"+str(expiration_date)+"','"+str(server_bandwidth_service_level)+"','"+str(buy_uid_count)+"' where not exists (select * from customer_vpg_inventory_table where p2p_domain='"+p2p_domain+"' and vid="+"'"+vid+"'"+" and pid='"+pid+"'"+" and gid='"+gid+"');"
            c.execute(sqlite_cmd)

            mysql_cmd = "INSERT INTO vpg_info (p2p_domain, customer_name, vid, pid, gid, start_date, expiration_date, server_bandwidth_service_level, buy_uid_count) VALUES ('"+str(p2p_domain)+"','"+str(customer_name)+"','"+str(vid)+"','"+str(pid)+"','"+str(gid)+"','"+str(start_date)+"','"+str(expiration_date)+"','"+str(server_bandwidth_service_level)+"',"+str(buy_uid_count)+");"
            cursor.execute(mysql_cmd)
            db.commit()

            print ("add customer_vpg_inventory_table success!")

            #INSERT master1_vpg_logintime_status_table
            for index in range(len(master_list)):
                master_name = master_list[index]
                sqlite_cmd = "INSERT INTO "+master_name+"_vpg_logintime_status_table (p2p_domain, vid, pid, gid) SELECT '"+p2p_domain+"','"+vid+"','"+pid+"','"+gid+"'"+" where not exists (select * from "+master_name+"_vpg_logintime_status_table where p2p_domain='"+p2p_domain+"' and vid="+"'"+vid+"'"+" and pid='"+pid+"'"+" and gid='"+gid+"');"
                sqlite_cmd_list.append(sqlite_cmd)

        for index in range(len(sqlite_cmd_list)):
            sqlite_cmd = sqlite_cmd_list[index]
            c.execute(sqlite_cmd)
        
        sqlite_cmd_list.clear()

    conn.commit()
    conn.close()
    print ("add master_vpg_logintime_status_table!")

def update_vpg_inventory_service(hostlist, vid, pid, gid, start_date, expiration_date, server_bandwidth_service_level, update_vpg_inventory_service_mode):
    conn = sqlite3.connect(file_path + 'tutk_vpg_data.db')
    c = conn.cursor()

    sqlite_cmd_list = []
    vpg_list = []

    if (hostlist == 0):
        vpg = vid+":"+pid+":"+gid
        vpg_list.append(vpg)
    else:
        file = open(file_path+"hostlist/"+hostlist, mode = 'r', encoding = 'utf-8-sig')
        lines = file.readlines()
        file.close()

        for line in lines:
            vpg = line[0:14]
            vpg_list.append(vpg)

    for index in range(len(vpg_list)):
        vpg = vpg_list[index]
        vid = vpg.split(":",3)[0]
        pid = vpg.split(":",3)[1]
        gid = vpg.split(":",3)[2]
        print ("Insert db vpg:",vid,":",pid,":",gid)

        if (update_vpg_inventory_service_mode == "start_date"):
            print ("start_date:"+str(start_date))
            sqlite_cmd = "UPDATE customer_vpg_inventory_table SET start_date="+str(start_date)+" WHERE vid='"+str(vid)+"' and pid='"+str(pid)+"' and gid='"+str(gid)+"';"
        
        elif (update_vpg_inventory_service_mode == "expiration_date"):
            print ("expiration_date:"+str(expiration_date))
            sqlite_cmd = "UPDATE customer_vpg_inventory_table SET expiration_date="+str(expiration_date)+" WHERE vid='"+str(vid)+"' and pid='"+str(pid)+"' and gid='"+str(gid)+"';"

        elif (update_vpg_inventory_service_mode == "server_bandwidth_service_level"):  
            print ("server_bandwidth_service_level:"+str(server_bandwidth_service_level))
            sqlite_cmd = "UPDATE customer_vpg_inventory_table SET server_bandwidth_service_level="+str(server_bandwidth_service_level)+" WHERE vid='"+str(vid)+"' and pid='"+str(pid)+"' and gid='"+str(gid)+"';"

        sqlite_cmd_list.append(sqlite_cmd)

    for index in range(len(sqlite_cmd_list)):
        print (sqlite_cmd_list[index])
        sqlite_cmd = sqlite_cmd_list[index]
        cursor = c.execute(sqlite_cmd)

    conn.commit()
    conn.close()
    print ("update vpg inventory service success!")

def update_vpg_uid_number():
    conn = sqlite3.connect(file_path + 'tutk_vpg_data.db')
    c = conn.cursor()
    sqlite_cmd = "SELECT vid,pid,gid FROM customer_vpg_inventory_table;"
    cursor = c.execute(sqlite_cmd)

    sqlite_cmd_list = []
    for row in cursor:
        vid_str = row[0]
        pid_str = row[1]
        gid_str = row[2]
       
        vid = int(vid_str,16)
        pid = int(pid_str,16)
        gid = int(gid_str,16)
        print (vid_str," ", pid_str," ", gid_str)
        db = MySQLdb.connect(db='urp',host='192.168.5.213',user='analysis',passwd='eEtm9a3jHK9m6Umc',port=3306,charset='utf8')
        cursor = db.cursor()
        cmd = "select count(uid) from urp_uid where active_vid="+str(vid)+" and active_pid="+str(pid)+" and active_gid="+str(gid)+";"
        cursor.execute(cmd)
        return_value = cursor.fetchone()

        uid_count = return_value[0]
        print (uid_count)
        sqlite_cmd = "UPDATE customer_vpg_inventory_table SET uid_count="+str(uid_count)+" WHERE vid='"+str(vid_str)+"' and pid='"+str(pid_str)+"' and gid='"+str(gid_str)+"';"
        sqlite_cmd_list.append(sqlite_cmd)

    for index in range(len(sqlite_cmd_list)):
        print (sqlite_cmd_list[index])
        sqlite_cmd = sqlite_cmd_list[index]
        cursor = c.execute(sqlite_cmd)
    
    conn.commit()
    conn.close()
    print ("update vpg uid number success!")

def parser_master_log(master_domain):
    p2p_domain = ""
    sqlite_cmd_list = []
    conn = sqlite3.connect(file_path + 'tutk_vpg_data.db')
    c = conn.cursor()

    master= master_domain.split(".",3)[0]
    csv_file  = open(file_path + "master_vpg_logintime_csv/" + master + "_vpg_logintime.csv", "w", newline='')
    master_vpg_logintime_csv_writer = csv.writer(csv_file)
    master_vpg_logintime_csv_writer.writerow(['p2p_domain','vid','pid','gid','login_time_year','login_time_month','login_time_day','login_time_hour','login_time_minute','login_time_sec'])

    if (master_domain == "m4.tutk.com"):
        master_domain = "120.79.219.241"
    elif (master_domain == "m8.tutk.com"):
        master_domain = "114.67.78.89"

    db = MySQLdb.connect(host=master_domain, user='watchdog', passwd='**29045478**', db='IOTCMasterDB_R')
    cursor = db.cursor()
    cmd = "select * from SID_IP_Table WHERE LoginTime > NOW() - INTERVAL 12 HOUR;"
    cursor.execute(cmd)
    rows = cursor.fetchall()
    for return_value in rows:
        vid = hex(return_value[1]).split("0x",2)[1].zfill(4)
        pid = hex(return_value[2]).split("0x",2)[1].zfill(4)
        gid = hex(return_value[3]).split("0x",2)[1].zfill(4)
        p2p_ip_address = str(return_value[4])
        login_time_year = str(return_value[6]).split(" ",2)[0].split("-",3)[0]
        login_time_month = str(return_value[6]).split(" ",2)[0].split("-",3)[1]
        login_time_day = str(return_value[6]).split(" ",2)[0].split("-",3)[2]
        login_time_hour = str(return_value[6]).split(" ",2)[1].split(":",3)[0]
        login_time_minute = str(return_value[6]).split(" ",2)[1].split(":",3)[1]
        login_time_sec = str(return_value[6]).split(" ",2)[1].split(":",3)[2]

        sqlite_cmd = "SELECT p2p_domain FROM p2pdomain_sessionkey_mapping_table where p2p_ip_address='"+p2p_ip_address+"'"
    
        cursor = c.execute(sqlite_cmd)
        for row in cursor:
            p2p_domain = row[0]
            master_vpg_logintime_csv_writer.writerow([p2p_domain, vid.upper(),pid.upper(),gid.upper(),login_time_year,login_time_month,login_time_day,login_time_hour,login_time_minute,login_time_sec])

    conn.commit()
    conn.close()

def update_master_vpg_login_time():
    for index in range(len(master_list)):
        master_domain = master_list[index] + ".tutk.com"
        print (master_domain)

        parser_master_log(master_domain)

        sqlite_cmd_list = []
        conn = sqlite3.connect(file_path + 'tutk_vpg_data.db')
        c = conn.cursor()
    
        master_name= master_domain.split(".",3)[0]
    
        sqlite_table_name = master_name + "_vpg_logintime_status_table"
        sqlite_cmd = "SELECT p2p_domain,vid,pid,gid,login_time FROM " + sqlite_table_name + ";"
        cursor = c.execute(sqlite_cmd)

        sqlite_cmd = ""
        for row in cursor:
            sqlite_db_p2p_domain = row[0]
            sqlite_db_vid = row[1]
            sqlite_db_pid = row[2]
            sqlite_db_gid = row[3]

            csv_file = file_path + "master_vpg_logintime_csv/" + master_name + "_vpg_logintime.csv"
            master_vpg_logintime = pd.read_csv(csv_file)

            for csv_index in range(len(master_vpg_logintime)):
                csv_p2p_domain = master_vpg_logintime['p2p_domain'][csv_index]
                csv_vid = master_vpg_logintime['vid'][csv_index]
                csv_pid = master_vpg_logintime['pid'][csv_index]
                csv_gid = master_vpg_logintime['gid'][csv_index]

                if (csv_p2p_domain == sqlite_db_p2p_domain and csv_vid == sqlite_db_vid and csv_pid == sqlite_db_pid and csv_gid == sqlite_db_gid):
                    login_time_year = master_vpg_logintime['login_time_year'][csv_index]
                    login_time_month = master_vpg_logintime['login_time_month'][csv_index]
                    login_time_day = master_vpg_logintime['login_time_day'][csv_index]
                    login_time_hour = master_vpg_logintime['login_time_hour'][csv_index]
                    login_time_minute = master_vpg_logintime['login_time_minute'][csv_index]
                    login_time_sec = master_vpg_logintime['login_time_sec'][csv_index]
                    login_time = str(login_time_year)+"-"+str(login_time_month)+"-"+str(login_time_day)+"-"+str(login_time_hour)+"-"+str(login_time_minute)+"-"+str(login_time_sec)

                    sqlite_cmd = "UPDATE "+sqlite_table_name+" SET login_time='"+str(login_time)+"'"+" WHERE vid='"+str(csv_vid)+"' and pid='"+str(csv_pid)+"' and gid='"+str(csv_gid)+"';"
                    sqlite_cmd_list.append(sqlite_cmd)

        for index in range(len(sqlite_cmd_list)):
            sqlite_cmd = sqlite_cmd_list[index]
            cursor = c.execute(sqlite_cmd)

        conn.commit()
        conn.close()
        print ("master_vpg_status_check success!")

def scp_master_vpg_not_login_list_t_master():
    for index in range(len(master_list)):
        master_domain = master_list[index]

        if (master_domain == "m4.tutk.com"):
            master_domain = "120.79.219.241"
        elif (master_domain == "m8.tutk.com"):
            master_domain = "114.67.78.89"
 
        sqlite_cmd = "scp "+file_path+"master_vpg_not_login_list_csv/"+master_domain+"_vpg_not_login_list.csv ubuntu@"+master_domain+".tutk.com:/home/ubuntu"

        print (sqlite_cmd)
        os.system(sqlite_cmd)

def create_master_vpg_not_login_list():
    conn = sqlite3.connect(file_path + 'tutk_vpg_data.db')
    c = conn.cursor()

    for index in range(len(master_list)):
        master_name = master_list[index]
        print (master_name)

        csv_file  = open(file_path + "master_vpg_not_login_list_csv/" + master_name + "_vpg_not_login_list.csv", "w", newline='')
        master_vpg_not_login_list_csv_writer = csv.writer(csv_file)
        master_vpg_not_login_list_csv_writer.writerow(['p2p_domain','vid','pid','gid','login_time'])

        sqlite_table_name = master_name + "_vpg_logintime_status_table"
        sqlite_cmd = "SELECT p2p_domain,vid,pid,gid,login_time FROM " + sqlite_table_name + ";"
        cursor = c.execute(sqlite_cmd)

        for row in cursor:
            sqlite_db_p2p_domain = row[0]
            sqlite_db_vid = row[1]
            sqlite_db_pid = row[2]
            sqlite_db_gid = row[3]
            login_time = row[4]

            if (login_time is None):
                print ("login time is None")
            else:
                login_time_year = login_time.split("-",6)[0]
                login_time_month = login_time.split("-",6)[1]
                login_time_day = login_time.split("-",6)[2]
                login_time_hour = login_time.split("-",6)[3]
                login_time_minute = login_time.split("-",6)[4]
                login_time_sec = login_time.split("-",6)[5]
                time_gap = datetime.datetime.now() - datetime.datetime(int(login_time_year),int(login_time_month),int(login_time_day),int(login_time_hour),int(login_time_minute),int(login_time_sec))

            print (sqlite_db_vid," ", sqlite_db_pid," ",sqlite_db_gid," ",login_time)

            if (login_time is None):
                master_vpg_not_login_list_csv_writer.writerow([sqlite_db_p2p_domain,sqlite_db_vid,sqlite_db_pid,sqlite_db_gid,"Not login time"])
            
            elif (time_gap.seconds/3600 > vpg_login_time_threshold):
                time = str(login_time_year)+"-"+str(login_time_month)+"-"+str(login_time_day)+"-"+str(login_time_hour)+":"+str(login_time_minute)+":"+str(login_time_sec)
                master_vpg_not_login_list_csv_writer.writerow([sqlite_db_p2p_domain,sqlite_db_vid,sqlite_db_pid,sqlite_db_gid,time])

    conn.commit()
    conn.close()

def check_vpg_inventory(vid, pid, gid):
    vpg = vid + ":" + pid + ":" + gid
    print (vpg)

    for index in range(len(master_list)):
        master_domain = master_list[index] + ".tutk.com"
        print (master_domain)

        parser_master_log(master_domain)

        sqlite_cmd_list = []
        conn = sqlite3.connect(file_path + 'tutk_vpg_data.db')
        c = conn.cursor()

        master_name= master_domain.split(".",3)[0]

        sqlite_table_name = master_name + "_vpg_logintime_status_table"
        sqlite_cmd = "SELECT p2p_domain,vid,pid,gid,login_time FROM " + sqlite_table_name + " WHERE vid='"+vid+"' and pid='"+pid+"' and gid='"+gid+"';"
        cursor = c.execute(sqlite_cmd)

        for row in cursor:
            print (row)

    conn.commit()
    conn.close()

def migrate_vpg(vid, pid, gid, hostlist, src_p2p_domain, dst_p2p_domain, service_mode):
    db = MySQLdb.connect(db='urp',host='192.168.5.213',user='analysis',passwd='eEtm9a3jHK9m6Umc',port=3306,charset='utf8')
    cursor = db.cursor()

    conn = sqlite3.connect(file_path + 'tutk_vpg_data.db')
    c = conn.cursor()

    vpg_list = []
    sqlite_cmd_list = []
    mysql_cmd_list = []

    if (service_mode == "vpg"):
        vpg = vid+":"+pid+":"+gid
        vpg_list.append(vpg)

    elif (service_mode == "vpg_list"):
        file = open(file_path+"hostlist/"+hostlist, mode = 'r', encoding = 'utf-8-sig')
        lines = file.readlines()
        file.close()

        for line in lines:
            vpg = line[0:14]
            vpg_list.append(vpg)

    for index in range(len(vpg_list)):
        vpg = vpg_list[index]
        vid = vpg.split(":",3)[0]
        pid = vpg.split(":",3)[1]
        gid = vpg.split(":",3)[2]
        print ("Insert db vpg:",vid,":",pid,":",gid)

        sqlite_cmd = "UPDATE customer_vpg_inventory_table SET p2p_domain='"+str(dst_p2p_domain)+"' WHERE p2p_domain='"+str(src_p2p_domain)+"' and vid='"+str(vid)+"' and pid='"+str(pid)+"' and gid='"+str(gid)+"';"
        sqlite_cmd_list.append(sqlite_cmd)

        mysql_cmd = "UPDATE vpg_info SET p2p_domain='"+str(dst_p2p_domain)+"' WHERE p2p_domain='"+str(src_p2p_domain)+"' and vid='"+str(vid)+"' and pid='"+str(pid)+"' and gid='"+str(gid)+"';"
        mysql_cmd_list.append(mysql_cmd)

        for index in range(len(master_list)):
            sqlite_table_name = master_list[index] + "_vpg_logintime_status_table"
            sqlite_cmd = "UPDATE "+sqlite_table_name+" SET p2p_domain='"+str(dst_p2p_domain)+"'"+" WHERE p2p_domain='"+str(src_p2p_domain)+"' and vid='"+str(vid)+"' and pid='"+str(pid)+"' and gid='"+str(gid)+"';"
            sqlite_cmd_list.append(sqlite_cmd)

    for index in range(len(sqlite_cmd_list)):
        cursor = c.execute(sqlite_cmd_list[index])
        print (sqlite_cmd_list[index])

    for index in range(len(mysql_cmd_list)):
        cursor.execute(mysql_cmd_list[index])
        db.commit()

    conn.commit()
    conn.close()

def delete_vpg(vid, pid, gid, hostlist, delete_mode):
    db = MySQLdb.connect(db='urp',host='192.168.5.213',user='analysis',passwd='eEtm9a3jHK9m6Umc',port=3306,charset='utf8')
    cursor = db.cursor()

    conn = sqlite3.connect(file_path + 'tutk_vpg_data.db')
    c = conn.cursor()

    vpg_list = []
    sqlite_cmd_list = []
    mysql_cmd_list = []

    if (service_mode == "vpg"):
        vpg = vid+":"+pid+":"+gid
        vpg_list.append(vpg)

    elif (service_mode == "vpg_list"):
        file = open(file_path+"hostlist/"+hostlist, mode = 'r', encoding = 'utf-8-sig')
        lines = file.readlines()
        file.close()

        for line in lines:
            vpg = line[0:14]
            vpg_list.append(vpg)

    for index in range(len(vpg_list)):
        vpg = vpg_list[index]
        vid = vpg.split(":",3)[0]
        pid = vpg.split(":",3)[1]
        gid = vpg.split(":",3)[2]
        print ("Delete db vpg:",vid,":",pid,":",gid)

        sqlite_cmd = "DELETE from customer_vpg_inventory_table WHERE vid='"+str(vid)+"' and pid='"+str(pid)+"' and gid='"+str(gid)+"';"
        sqlite_cmd_list.append(sqlite_cmd)

        mysql_cmd = "DELETE FROM vpg_info where vid='" + str(vid)+"' and pid='"+str(pid)+"' and gid='"+str(gid)+"';"
        mysql_cmd_list.append(mysql_cmd)

        for index in range(len(master_list)):
            sqlite_table_name = master_list[index] + "_vpg_logintime_status_table"
            sqlite_cmd = "DELETE from "+sqlite_table_name+" WHERE vid='"+str(vid)+"' and pid='"+str(pid)+"' and gid='"+str(gid)+"';"
            sqlite_cmd_list.append(sqlite_cmd)

    for index in range(len(sqlite_cmd_list)):
        cursor = c.execute(sqlite_cmd_list[index])
        print (sqlite_cmd_list[index])

    for index in range(len(mysql_cmd_list)):
        cursor.execute(mysql_cmd_list[index])
        db.commit()

    conn.commit()
    conn.close()

if __name__ == "__main__":
    if (len(sys.argv) == 1):
        while True:
            try:
                print ("\033[0;31m%s\033[0m" % "[Service mode]")
                for index in range(len(service_mode_list)):
                    print ("\033[0;31m%s\033[0m" % service_mode_list[index])

                service_mode = str(input("\033[0;34m%s\033[0m" % "Please input service mode [chose 1 to 7] (e.g. 1): "))

                #add_sessionkey
                if (service_mode == "1"):
                    p2p_domain = str(input("\033[0;34m%s\033[0m" % "Please input p2p domain (e.g.e0): "))
                    p2p_ip_address = str(input("\033[0;34m%s\033[0m" % "Please input p2p server ip address: "))
                    session_key = str(input("\033[0;34m%s\033[0m" % "Please input session key: "))
                    add_sessionkey(p2p_domain, p2p_ip_address, session_key)

                #create_vpg_inventory
                elif (service_mode == "2"):
                    count = 1
                    p2p_domain_count = str(input("\033[0;34m%s\033[0m" % "Please input p2p domain count(e.g.3): "))
                    p2p_domain_list = []
                    while count <= int(p2p_domain_count):
                        p2p_domain = str(input("\033[0;34m%s\033[0m" % "Please input p2p domain (e.g.e0): "))
                        p2p_domain_list.append(p2p_domain)
                        count = count + 1

                    print ("\033[0;31m%s\033[0m" % "[Start date]")
                    start_date_year = str(input("\033[0;34m%s\033[0m" % "Please input start date (year) (e.g.2020): "))
                    start_date_month = str(input("\033[0;34m%s\033[0m" % "Please input start date (month) (e.g.7): "))
                    start_date_day = str(input("\033[0;34m%s\033[0m" % "Please input start date (day) (e.g.5): "))
                    start_date = str(start_date_year)+"-"+str(start_date_month)+"-"+str(start_date_day)

                    print ("\033[0;31m%s\033[0m" % "[Expiration date]")
                    expiration_date_year = str(input("\033[0;34m%s\033[0m" % "Please input start date (year) (e.g.2020): "))
                    expiration_date_month = str(input("\033[0;34m%s\033[0m" % "Please input start date (month) (e.g.7): "))
                    expiration_date_day = str(input("\033[0;34m%s\033[0m" % "Please input start date (day) (e.g.5): "))
                    expiration_date = str(start_date_year)+"-"+str(start_date_month)+"-"+str(start_date_day)

                    print ("\033[0;31m%s\033[0m" % "[Server Bandwidth Service Level]")
                    for index in range(len(server_bandwidth_service_level_list)):
                        print ("\033[0;31m%s\033[0m" % server_bandwidth_service_level_list[index])
                    
                    server_bandwidth_service_level_number = str(input("\033[0;34m%s\033[0m" % "Please input server bandwidth service level [chose 1 to 7] (e.g. 1): "))

                    server_bandwidth_service_level = ""
                    if (server_bandwidth_service_level_number == "1"):
                        server_bandwidth_service_level = "A"
                    elif (server_bandwidth_service_level_number == "2"):
                        server_bandwidth_service_level = "B"
                    elif (server_bandwidth_service_level_number == "3"):
                        server_bandwidth_service_level = "C"
                    elif (server_bandwidth_service_level_number == "4"):
                        server_bandwidth_service_level = "D"
                    elif (server_bandwidth_service_level_number == "5"):
                        server_bandwidth_service_level = "E"
                    elif (server_bandwidth_service_level_number == "6"):
                        server_bandwidth_service_level = "F"
                    elif (server_bandwidth_service_level_number == "7"):
                        server_bandwidth_service_level = "G"

                    print ("\033[0;31m%s\033[0m" % "[VPG service mode]")
                    for index in range(len(create_vpg_mode_list)):
                        print ("\033[0;31m%s\033[0m" % create_vpg_mode_list[index])

                    service_mode_number = str(input("\033[0;34m%s\033[0m" % "Please input vpg service mode [chose 1 to 2] (e.g. 1): "))
                    buy_uid_count = str(input("\033[0;34m%s\033[0m" % "Please input buy_uid_count: "))

                    if (service_mode_number == "1"):
                        service_mode = "vpg"
                        vid = str(input("\033[0;34m%s\033[0m" % "Please input vid (Hex) (capital letter): "))
                        pid = str(input("\033[0;34m%s\033[0m" % "Please input pid (Hex) (capital letter): "))
                        gid = str(input("\033[0;34m%s\033[0m" % "Please input gid (Hex) (capital letter): "))
                        create_vpg_inventory(p2p_domain_list, 0, vid, pid, gid, start_date, expiration_date, server_bandwidth_service_level, service_mode, buy_uid_count)

                    elif (service_mode_number == "2"):
                        service_mode = "vpg_list"
                        allFileList = os.listdir(file_path + "hostlist/")
                        for index in range(len(allFileList)):
                            string = "[" + str(index+1) + "] " + allFileList[index]
                            print ("\033[0;31m%s\033[0m" %  string)

                        host_list_index = str(input("\033[0;34m%s\033[0m" % "Please input hostlist file name [chose number] (e.g. 1): "))
                        
                        create_vpg_inventory(p2p_domain_list, allFileList[int(host_list_index)-1], 0, 0, 0, start_date, expiration_date, server_bandwidth_service_level, service_mode, buy_uid_count)
                    else:
                        print ("service mode error!")

                #update_vpg_inventory
                elif (service_mode == "3"):
                    start_date = ""
                    expiration_date = ""
                    server_bandwidth_service_level = ""

                    print ("\033[0;31m%s\033[0m" % "[Update vpg inventory service mode]")
                    for index in range(len(update_vpg_inventory_service_mode_list)):
                        print ("\033[0;31m%s\033[0m" % update_vpg_inventory_service_mode_list[index])

                    update_vpg_inventory_service_mode_number = str(input("\033[0;34m%s\033[0m" % "Please input update vpg inventory service mode [chose 1 to 3] (e.g. 1): "))

                    #start_date
                    if (update_vpg_inventory_service_mode_number == "1"):
                        update_vpg_inventory_service_mode = "start_date"
                        print ("\033[0;31m%s\033[0m" % "[Start date]")
                        start_date_year = str(input("\033[0;34m%s\033[0m" % "Please input start date (year) (e.g.2020): "))
                        start_date_month = str(input("\033[0;34m%s\033[0m" % "Please input start date (month) (e.g.7): "))
                        start_date_day = str(input("\033[0;34m%s\033[0m" % "Please input start date (day) (e.g.5): "))
                        start_date = str(start_date_year)+"-"+str(start_date_month)+"-"+str(start_date_day)

                    #expiration_date
                    elif (update_vpg_inventory_service_mode_number == "2"):
                        update_vpg_inventory_service_mode = "expiration_date"
                        print ("\033[0;31m%s\033[0m" % "[Expiration date]")
                        expiration_date_year = str(input("\033[0;34m%s\033[0m" % "Please input start date (year) (e.g.2020): "))
                        expiration_date_month = str(input("\033[0;34m%s\033[0m" % "Please input start date (month) (e.g.7): "))
                        expiration_date_day = str(input("\033[0;34m%s\033[0m" % "Please input start date (day) (e.g.5): "))
                        expiration_date = str(expiration_date_year)+"-"+str(expiration_date_month)+"-"+str(expiration_date_day)

                    #server_bandwidth_service_level
                    elif (update_vpg_inventory_service_mode_number == "3"):
                        update_vpg_inventory_service_mode = "server_bandwidth_service_level"
                        print ("\033[0;31m%s\033[0m" % "[Server Bandwidth Service Level]")
                        for index in range(len(server_bandwidth_service_level_list)):
                            print ("\033[0;31m%s\033[0m" % server_bandwidth_service_level_list[index])
                        
                        server_bandwidth_service_level = str(input("\033[0;34m%s\033[0m" % "Please input server bandwidth service level: "))

                    else:
                        print ("service mode error!")

                    print ("\033[0;31m%s\033[0m" % "[VPG service mode]")
                    for index in range(len(create_vpg_mode_list)):
                        print ("\033[0;31m%s\033[0m" % create_vpg_mode_list[index])

                    service_mode_number = str(input("\033[0;34m%s\033[0m" % "Please input vpg service mode [chose 1 to 2] (e.g. 1): "))


                    if (service_mode_number == "1"):

                        vid = str(input("\033[0;34m%s\033[0m" % "Please input vid (Hex) (capital letter): "))
                        pid = str(input("\033[0;34m%s\033[0m" % "Please input pid (Hex) (capital letter): "))
                        gid = str(input("\033[0;34m%s\033[0m" % "Please input gid (Hex) (capital letter): "))

                        update_vpg_inventory_service(0, vid, pid, gid, start_date, expiration_date, server_bandwidth_service_level, update_vpg_inventory_service_mode)
                    
                    elif (service_mode == "vpg_list"):
                        allFileList = os.listdir(file_path + "hostlist/")
                        for index in range(len(allFileList)):
                            string = "[" + str(index+1) + "] " + allFileList[index]
                            print ("\033[0;31m%s\033[0m" %  string)

                        host_list_index = str(input("\033[0;34m%s\033[0m" % "Please input hostlist file name [chose number] (e.g. 1): "))
                        
                        update_vpg_inventory_service(allFileList[int(host_list_index)-1], 0, 0, 0, start_date, expiration_date, server_bandwidth_service_level, update_vpg_inventory_service_mode)
                    
                    else:
                        print ("service mode error!")

                #check_vpg_inventory
                elif (service_mode == "4"):
                    vid = str(input("\033[0;34m%s\033[0m" % "Please input vid (Hex) (capital letter): "))
                    pid = str(input("\033[0;34m%s\033[0m" % "Please input pid (Hex) (capital letter): "))
                    gid = str(input("\033[0;34m%s\033[0m" % "Please input gid (Hex) (capital letter): "))
                    check_vpg_inventory(vid, pid, gid)

                #migrate_vpg
                elif (service_mode == "5"):
                    print ("\033[0;31m%s\033[0m" % "[VPG service mode]")
                    for index in range(len(create_vpg_mode_list)):
                        print ("\033[0;31m%s\033[0m" % create_vpg_mode_list[index])

                    service_mode_number = str(input("\033[0;34m%s\033[0m" % "Please input vpg service mode [chose 1 to 2] (e.g. 1): "))

                    if (service_mode_number == "1"):
                        service_mode = "vpg"
                        vid = str(input("\033[0;34m%s\033[0m" % "Please input vid (Hex) (capital letter): "))
                        pid = str(input("\033[0;34m%s\033[0m" % "Please input pid (Hex) (capital letter): "))
                        gid = str(input("\033[0;34m%s\033[0m" % "Please input gid (Hex) (capital letter): "))
                        src_p2p_domain = str(input("\033[0;34m%s\033[0m" % "Please input migrate src p2p domain (e.g.e0): "))
                        dst_p2p_domain = str(input("\033[0;34m%s\033[0m" % "Please input migrate dst p2p domain (e.g.e0): "))
                        migrate_vpg(vid, pid, gid, 0, src_p2p_domain, dst_p2p_domain, service_mode)

                    elif (service_mode_number == "2"):
                        service_mode = "vpg_list"

                        allFileList = os.listdir(file_path + "hostlist/")
                        for index in range(len(allFileList)):
                            string = "[" + str(index+1) + "] " + allFileList[index]
                            print ("\033[0;31m%s\033[0m" %  string)

                        host_list_index = str(input("\033[0;34m%s\033[0m" % "Please input hostlist file name [chose number] (e.g. 1): "))

                        src_p2p_domain = str(input("\033[0;34m%s\033[0m" % "Please input migrate src p2p domain (e.g.e0): "))
                        dst_p2p_domain = str(input("\033[0;34m%s\033[0m" % "Please input migrate dst p2p domain (e.g.e0): "))
                        migrate_vpg(0, 0, 0, allFileList[int(host_list_index)-1], src_p2p_domain, dst_p2p_domain, service_mode)

                #delete_vpg
                elif (service_mode == "6"):
                    print ("\033[0;31m%s\033[0m" % "[VPG service mode]")
                    for index in range(len(create_vpg_mode_list)):
                        print ("\033[0;31m%s\033[0m" % create_vpg_mode_list[index])

                    service_mode_number = str(input("\033[0;34m%s\033[0m" % "Please input vpg service mode [chose 1 to 2] (e.g. 1): "))

                    if (service_mode_number == "1"):
                        service_mode = "vpg"
                        vid = str(input("\033[0;34m%s\033[0m" % "Please input vid (Hex) (capital letter): "))
                        pid = str(input("\033[0;34m%s\033[0m" % "Please input pid (Hex) (capital letter): "))
                        gid = str(input("\033[0;34m%s\033[0m" % "Please input gid (Hex) (capital letter): "))
                        delete_vpg(vid, pid, gid, 0, service_mode)

                    elif (service_mode_number == "2"):
                        service_mode = "vpg_list"
                        allFileList = os.listdir(file_path + "hostlist/")
                        for index in range(len(allFileList)):
                            string = "[" + str(index+1) + "] " + allFileList[index]
                            print ("\033[0;31m%s\033[0m" %  string)

                        host_list_index = str(input("\033[0;34m%s\033[0m" % "Please input hostlist file name [chose number] (e.g. 1): "))
                        delete_vpg(0, 0, 0, allFileList[int(host_list_index)-1], service_mode)

                #create_vpg_inventory_test
                elif (service_mode == "7"):
                    p2p_domain = str(input("\033[0;34m%s\033[0m" % "Please input p2p domain (e.g.e0): "))
                    create_vpg_inventory_test(p2p_domain)

                else:
                    print ("service mode error!")

            except ValueError:
                continue
            else:
                break
 
    else:
        if (sys.argv[1] == "update_vpg_uid_number"):
            update_vpg_uid_number()

        elif (sys.argv[1] == "update_master_vpg_login_time"):
            update_master_vpg_login_time()

        elif (sys.argv[1] == "create_master_vpg_not_login_list"):
            create_master_vpg_not_login_list()
            scp_master_vpg_not_login_list_t_master()
