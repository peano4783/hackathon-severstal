"""
Must install:
pip install flask
pip install holoviews
# pip install fastparquet
pip install openpyxl
pip install Flask-Celery
pip install gunicorn
pip install catboost
"""


from flask import Flask, render_template, flash, request, redirect, url_for
import os
import secrets
from werkzeug.utils import secure_filename
from inference import run_inference
from celery import Celery, shared_task
import bokeh
from time import sleep

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'media')
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['CELERY']=dict(
        broker_url='amqp://admin:yjdikoadmin@31.13.134.173:5672/my_vhost',
        # result_backend='amqp://admin:yjdikoadmin@31.13.134.173:5672',
        task_ignore_result=True,
    )
# app.config.from_prefixed_env()

celery_app = Celery(app.name)
celery_app.config_from_object(app.config)
app.extensions["celery"] = celery_app


# @shared_task
@celery_app.task
def ctask(job_id):
    sleep(5)
    with open('jobs/my_job.json','w') as f:
        f.write('Hello')
    return 42

@app.route('/', methods=['GET', 'POST'])
def index_page():
    # Setting default parameters
    agregat = ""

    result = {}
    if request.method == 'POST':
        # Reading default parameters from the web form when the user clicks on Submit
        agregat = request.form.get('agregat')

        #if 'file' not in request.files:
        #    flash('Файл не выбран')
        #    return redirect(request.url)
        #file = request.files['file']
        #if file.filename == '':
        #    flash('Файл не выбран')
        #    return redirect(request.url)
        #if agregat.strip() == '':
        #    flash('Агрегат не выбран')
        #    return redirect(request.url)
        #xlsx_filename = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
        #file.save(xlsx_filename)

        # Run function that does the actual job:
        ctask.delay(12)
        # result = run_inference(xlsx_filename, agregat)

    return render_template('severstal.html',
                           title='Модель раннего обнаружения неисправностей промышленного оборудования',
                           bokeh_version=bokeh.__version__,
                           agregat = agregat,
                           result=result)

if __name__ == '__main__':
    # app.run(debug=False, host="31.13.134.173", port=5678)
    app.run(debug=False, port=5678)

