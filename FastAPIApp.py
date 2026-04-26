# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 11:01:07 2026

@author: Barry
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import instructor
import uuid
import os
import pdfplumber
import json
from openai import OpenAI
import sqlite3

#26/04/2026 introducing sqlite db to allow scheduling jobs

os.remove("EZ-Extract.db")
#Create sqlite db and jobs table
try:
    with sqlite3.connect("EZ-Extract.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS JOBS (
                UUID TEXT,
                JSON_OUT TEXT,
                STATUS);
            '''     
            )   
        conn.commit()
except sqlite3.OperationalError as e:
    print(e)
finally:    
    conn.close()


#create tempfile directory if missing
if not os.path.exists("uploads"):
    os.makedirs("uploads") 

app = FastAPI()

#25/04/26 switched from ollama to lmstudio for local LLM hosting
hosturl = "http://localhost:1234/v1"
mdl = "qwen-4b-saiga"
lm_studio_openai = OpenAI(
    base_url=hosturl,
    api_key="xxxxxx"
)
client = instructor.from_openai(lm_studio_openai, mode=instructor.Mode.JSON_SCHEMA)

#24/04/26 added system prompt, significantly improved response model adgerence when testing with Qwen3:4b
sysprompt = """Extract all data from the following document. Return a JSON object matching this exact schema:
- title: string
- date: string
- Tables: list of objects, each with:
  - page_number: int
  - table_number: int
  - table_name: string
  - columns: list of plain strings (column names only, e.g. ["Category", "Answer"])
  - rows: list of lists of strings (each inner list is one row)
"""

#Define response model
class Table(BaseModel):
    page_number: int | None = Field(description='Page number where table came from, null if no table')
    table_number: int | None = Field(description='Number of table on page, null if no table')
    table_name: str | None = Field(description='Name / title of table, null if no table')
    columns: list[str] | None 
    rows: list[list[str | None]] 

class Document(BaseModel):
    title: str = Field(description='Title of document found at the beginning of page 1')
    date: str | None = Field(description='Documents date of publication if present null if not')
    Tables: list[Table]  = Field(description='List of tables extracted from document, empty list [] if document contained no tables')


def pdfextract(file):
    '''
    Accepts file name with path as input, extracts text and tables with pdfplumber
    then processes with LLM using instructor library to constrain LLM responses to 
    structure defined in response model. Returns JSON.
    '''
    outdict = {}
    with pdfplumber.open(file) as pdf:
        for pageidx, page in enumerate(pdf.pages, start=1):
            outdict[f'Page {pageidx} text'] = page.extract_text()
            for tableidx, table in enumerate(page.extract_tables(), start=1):
                outdict[f'Page {pageidx} - Table {tableidx}'] = table
    json_string = json.dumps(outdict, indent=2)
    # Extract it from natural language
    llmoutput = client.chat.completions.create(
        model=mdl,
        response_model=Document,
        messages=[
            {"role": "system", "content": sysprompt},
            {"role": "user", "content": json_string}])
    return(llmoutput.model_dump())

def plumbpdf(file):
    '''
    Extracts text and tables with pdfplumber. Returns JSON.
    '''
    outdict = {}
    with pdfplumber.open(file) as pdf:
        for pageidx, page in enumerate(pdf.pages, start=1):
            outdict[f'Page {pageidx} text'] = page.extract_text()
            for tableidx, table in enumerate(page.extract_tables(), start=1):
                outdict[f'Page {pageidx} - Table {tableidx}'] = table
    return(json.dumps(outdict, indent=2))

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    fname, ext = os.path.splitext(file.filename)
    if ext != '.pdf':
        raise HTTPException(status_code=415, detail="Uploaded file was not .pdf")
    else:
        newname = str(uuid.uuid4())
        filepath = f'uploads/{newname}.pdf'
        with open(filepath, 'wb') as f:
            f.write(await file.read())
        try:
            jstr = pdfextract(filepath)
        except:
            raise HTTPException(status_code=500, detail="Error occured when parsing .pdf")
        finally:
            os.remove(filepath)
        return(jstr)

@app.post("/submitjob")
async def submit(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    fname, ext = os.path.splitext(file.filename)
    if ext != '.pdf':
        raise HTTPException(status_code=415, detail="Uploaded file was not .pdf")
    else:
        try:
            newname = str(uuid.uuid4())
            filepath = f'uploads/{newname}.pdf'
            with open(filepath, 'wb') as f:
                f.write(await file.read())
        except:
            raise HTTPException(status_code=500, detail="Error saving .pdf to server")
        try:
            with sqlite3.connect("EZ-Extract.db") as conn:
                cursor = conn.cursor()
                cursor.execute(f"INSERT INTO JOBS (UUID, STATUS) SELECT '{newname}', 'Job Scheduled'")   
                conn.commit()
                background_tasks.add_task(processjobs,newname)
                return({"Job UUID": newname})
        except:
            raise HTTPException(status_code=500, detail="Error writing to database")
            
def processjobs(jobid):           
    print(jobid)
    try:
        jstr = pdfextract(f"uploads/{jobid}.pdf")
        with sqlite3.connect("EZ-Extract.db") as conn:
            cur = conn.cursor()
            cur.execute(
                        "UPDATE JOBS SET JSON_OUT = ?, STATUS = ? WHERE UUID = ?",
                        (json.dumps(jstr), "Complete", jobid)
                    )
            conn.commit()
            os.remove(f"uploads/{jobid}.pdf")

    except sqlite3.OperationalError as e:
        print(e)