"""
Must install:
pip install flask
pip install holoviews
# pip install openpyxl
pip install Flask-Celery
pip install catboost
pip install gunicorn
pip install levenshtein
"""
import pandas as pd
from flask import Flask, render_template, flash, request, redirect, url_for
import os
import secrets
from werkzeug.utils import secure_filename
from inference import run_inference
from celery import Celery, shared_task
import bokeh
import json
from datetime import datetime

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'media')
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['CELERY']=dict(
        broker_url='amqp://admin:???iko?????@31.13.134.173:5672/my_vhost',
        # result_backend='',
        task_ignore_result=True,
    )

celery_app = Celery(app.name)
celery_app.config_from_object(app.config)
app.extensions["celery"] = celery_app

TITLE = 'Модель раннего обнаружения неисправностей промышленного оборудования'

@celery_app.task
def ctask(job_id, csv_filename, exhauster, agregat):
    result = run_inference(job_id, csv_filename, exhauster, agregat)
    with open(get_job_filename(job_id), 'w', encoding='utf8') as f:
        json.dump(result, f, ensure_ascii=False)
    return None

def get_job_filename(job_id):
    return os.path.join(basedir, 'jobs', job_id+'.json')
def validate_input_csv(csv_filename):
    try:
        df = pd.read_csv(csv_filename, nrows=2) # Just read the very beginning of the file
    except:
        return 'Не удается прочитать csv-файл'
    columns = [
        "DT", "ТОК РОТОРА 1", "ТОК РОТОРА 2", "ТОК СТАТОРА", "ВИБРАЦИЯ НА ОПОРЕ 1", "ВИБРАЦИЯ НА ОПОРЕ 2",
        "ВИБРАЦИЯ НА ОПОРЕ 3", "ВИБРАЦИЯ НА ОПОРЕ 3. ПРОДОЛЬНАЯ", "ВИБРАЦИЯ НА ОПОРЕ 4", "ВИБРАЦИЯ НА ОПОРЕ 4. ПРОДОЛЬНАЯ",
        "ТЕМПЕРАТУРА ПОДШИПНИКА НА ОПОРЕ 1", "ТЕМПЕРАТУРА ПОДШИПНИКА НА ОПОРЕ 2", "ТЕМПЕРАТУРА ПОДШИПНИКА НА ОПОРЕ 3",
        "ТЕМПЕРАТУРА ПОДШИПНИКА НА ОПОРЕ 4", "ТЕМПЕРАТУРА МАСЛА В МАСЛОБЛОКЕ", "ТЕМПЕРАТУРА МАСЛА В СИСТЕМЕ", "ДАВЛЕНИЕ МАСЛА В СИСТЕМЕ"
    ]
    if len(df.columns) != len(columns):
        return f"Количество колонок в csv-файле должно быть равно {len(columns)}"
    for col1, col2 in zip(df.columns, columns):
        if col1 != col2:
            return f"В csv-файле название колонки: {col1}; требуется: {col2}"
    return None

@app.route('/result', methods=['GET', 'POST'])
def result_page():
    if not ('job_id' in request.args):
        return redirect(url_for('index_page'))
    job_id = request.args.get('job_id')
    json_filename = get_job_filename(job_id)
    if not os.path.isfile(json_filename):
        return render_template('job_pending.html',
                           title=TITLE,
                           job_id=job_id)
    with open(json_filename) as f:
        result = json.load(f)

    return render_template('job_result.html',
                        bokeh_version=bokeh.__version__,
                        title=TITLE,
                        job_id=job_id,
                        result=result)


@app.route('/', methods=['GET', 'POST'])
def index_page():
    exhauster, agregat = "", ""
    if request.method == 'POST':
        exhauster = request.form.get('exhauster')
        agregat = request.form.get('agregat')

        if 'file' not in request.files:
           flash('Файл не выбран')
           return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
           flash('Файл не выбран')
           return redirect(request.url)
        if exhauster.strip() == '':
           flash('Эксгаустер не указан')
           return redirect(request.url)
        if agregat.strip() == '':
           flash('Агрегат не указан')
           return redirect(request.url)
        csv_filename = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
        file.save(csv_filename)
        validation_result = validate_input_csv(csv_filename)
        if validation_result:
            flash(validation_result)
            return redirect(request.url)

        # Run function that does the actual job:
        job_id = secure_filename('_'.join(['job', datetime.now().strftime("%Y.%m.%d_%H:%M:%S")]))
        ctask.run(job_id, csv_filename, exhauster, agregat)

        return redirect(url_for('result_page', job_id=job_id))

    return render_template('severstal.html',
                           title=TITLE,
                           bokeh_version=bokeh.__version__,
                           exhauster=exhauster, agregat=agregat)

if __name__ == '__main__':
    # app.run(debug=False, host="31.13.134.173", port=5678)
    app.run(debug=True, port=5678)

