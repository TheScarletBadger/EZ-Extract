# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 22:21:14 2026

@author: Barry
"""

from flask import Flask, render_template, request, redirect
from pydantic import BaseModel
import instructor
import uuid
import os
import pdfplumber
import json
import jsonify
app = Flask(__name__)

#LLM client
client = instructor.from_provider("ollama/qwen3:4b")

# Define response model
class report(BaseModel):
    title: str
    date: str
    wind: str

outdict = {}

with pdfplumber.open("uploads/eh-mwi-wm14455_2026-04-18_160011_4353.pdf") as pdf:
    for idx, page in enumerate(pdf.pages, start=1):
        outdict[f'Page {idx} text'] = page.extract_text()
        outdict[f'Table {idx}'] = page.extract_tables()



json_string = json.dumps(outdict, indent=2)

# Extract it from natural language
llmoutput = client.chat.completions.create(
    response_model=report,
    messages=[{"role": "user", "content": json_string}],
)

print(llmoutput.model_dump())