# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 22:21:14 2026

@author: Barry
"""

import pdfplumber
import json

outdict = {}

with pdfplumber.open("uploads/75b7e169-947b-4525-821c-b8c424b2c23a.pdf") as pdf:
    for idx, page in enumerate(pdf.pages, start=1):
        outdict[f'Page {idx} text'] = page.extract_text()
        outdict[f'Table {idx}'] = page.extract_tables()

json_string = json.dumps(outdict, indent=2)
print(json_string)