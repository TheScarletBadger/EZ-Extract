from flask import Flask, render_template, request, redirect
import uuid
import os
import pdfplumber
import json

app = Flask(__name__)

def pdfextract(file):
    outdict = {}
    with pdfplumber.open(file) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            outdict[f'Page {idx} text'] = page.extract_text()
            outdict[f'Table {idx}'] = page.extract_tables()
    json_string = json.dumps(outdict, indent=2)
    return(json_string)

@app.route('/')  
def main():  
    return ('test')

@app.route('/ui/upload')  
def upload():  
    return render_template("upload.html") 

@app.route('/ui/fileparse', methods = ['POST'])  
def parsefile():    
    f = request.files['file']
    fname, ext = os.path.splitext(f.filename)
    if ext !='.pdf':
        return redirect('/upload')
    else:
        newname = str(uuid.uuid4())
        f.save('uploads/' + newname + '.pdf') 
        return render_template("parsing.html", name = f.filename)


@app.route('/api/upload', methods = ['POST'])  
def apiupload():  
    f = request.files['file']
    fname, ext = os.path.splitext(f.filename)
    if ext !='.pdf':
        return redirect('/upload')
    else:
        newname = str(uuid.uuid4())
        f.save('uploads/' + newname + '.pdf') 
        return(pdfextract('uploads/' + newname + '.pdf'))




        


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)