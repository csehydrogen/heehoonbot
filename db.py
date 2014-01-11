# -*- coding: utf-8 -*-

import sqlite3

class Handler:
    def __init__(self,db_path):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()

    def commit(self,query):
        self.cur.execute(query)
        self.conn.commit()

    def fetch(self,query):
        self.cur.execute(query)
        return self.cur.fetchall()
