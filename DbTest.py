# -*- coding: utf-8 -*-
"""
Created on Sun Apr 26 17:20:31 2026

@author: Barry
"""

import sqlite3

conn = sqlite3.connect("EZ-Extract.db")
cur = conn.cursor()
cur.execute("SELECT UUID FROM JOBS WHERE STATUS = 'Job Scheduled' LIMIT 1")
rows = cur.fetchall()
if rows:
    jobid = rows[0][0]
    print(jobid)
    cur.execute(
                "UPDATE JOBS SET JSON_IN = ?, STATUS = ? WHERE UUID = ?",
                ("test", "Preprocessing Complete", jobid)
            )
    conn.commit()


conn.close()