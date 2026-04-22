from flask import Flask, render_template, request, redirect
import uuid
import os
app = Flask(__name__)  

@app.route('/')  
def main():  
    return ('test')

@app.route('/upload')  
def upload():  
    return render_template("upload.html") 


@app.route('/fileparse', methods = ['POST'])  
def parsefile():  
    if request.method == 'POST':  
        f = request.files['file']
        fname, ext = os.path.splitext(f.filename)
        if ext !='.pdf':
            return redirect('/upload')
        else:
            f.save('uploads/' + str(uuid.uuid4()) + '.pdf')  
            return render_template("parsing.html", name = f.filename)  

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)