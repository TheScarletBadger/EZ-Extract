# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 11:01:07 2026

@author: Barry
"""

from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel, Field
import instructor
import uuid
import os
import pdfplumber
import json

app = FastAPI()

#LLM client
client = instructor.from_provider("ollama/qwen3:4b", mode=instructor.Mode.JSON)

sysprompt = """Extract the report. Return a JSON object matching this exact schema:
- title: string
- date: string
- Tables: list of objects, each with:
  - page_number: int
  - table_number: int
  - table_name: string
  - columns: list of plain strings (column names only, e.g. ["Category", "Answer"])
  - rows: list of lists of strings (each inner list is one row)
"""

class Table(BaseModel):
    page_number: int | None = Field(description='Page number where table came from, null if no table')
    table_number: int | None = Field(description='Number of table on page, null if no table')
    table_name: str | None = Field(description='Name / title of table, null if no table')
    columns: list[str] | None 
    rows: list[list[str | None]] 

class Report(BaseModel):
    title: str = Field(description='Title of document found at the beginning of page 1')
    date: str | None = Field(description='Documents date of publication if present null if not')
    Tables: list[Table]  = Field(description='List of tables extracted from document, empty list [] if document contained no tables')

def pdfextract(file):
    outdict = {}
    with pdfplumber.open(file) as pdf:
        for pageidx, page in enumerate(pdf.pages, start=1):
            outdict[f'Page {pageidx} text'] = page.extract_text()
            for tableidx, table in enumerate(page.extract_tables(), start=1):
                outdict[f'Page {pageidx} - Table {tableidx}'] = table
    json_string = json.dumps(outdict, indent=2)
    # Extract it from natural language
    llmoutput = client.chat.completions.create(
        response_model=Report,
        messages=[
            {"role": "system", "content": sysprompt},
            {"role": "user", "content": json_string}])
    return(llmoutput.model_dump())

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    fname, ext = os.path.splitext(file.filename)
    if ext != '.pdf':
        return {'Error':'Uploaded file was not .pdf'}
    else:
        newname = str(uuid.uuid4())
        filepath = f'uploads/{newname}.pdf'
        
        with open(filepath, 'wb') as f:
            f.write(await file.read())
        jstr = pdfextract(filepath)
        os.remove(filepath)
        return(jstr)