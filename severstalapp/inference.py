import pandas as pd
import numpy as np
import bokeh
import holoviews as hv
import os
import catboost
import Levenshtein
hv.extension('bokeh')

from time import sleep

import glob

basedir = os.path.abspath(os.path.dirname(__file__))
PLOT_WIDTH, PLOT_HEIGHT = 800, 500


def find_most_similar_str(desired_filename, model_filenames):
    lev_distances = [Levenshtein.distance(desired_filename, x) for x in model_filenames]
    min_dist_i = 0
    for i in range(1, len(lev_distances)):
        if lev_distances[i] < lev_distances[min_dist_i]:
            min_dist_i = i
    return model_filenames[min_dist_i]

def run_inference(job_id, csv_filename, exhauster, agregat):
    """Вынес сюда "настоящий" код"""
    exhN = exhauster[-1]

    ml_models_path = os.path.join(basedir, f'ml_models/{exhN}/')
    ml_model_filenames = os.listdir(ml_models_path)
    ml_model_m1_filename = find_most_similar_str(exhauster+'__'+agregat+'__M1', ml_model_filenames)
    ml_model_m3_filename = find_most_similar_str(exhauster+'__'+agregat+'__M3', ml_model_filenames)

    # ЭКСГАУТЕРx__АГРЕГАТ__Mx_15
    # ЭКСГАУТЕРx__АГРЕГАТ__Mx_30
    # ЭКСГАУТЕРx__АГРЕГАТ__Mx_45
    # ЭКСГАУТЕРx__АГРЕГАТ__Mx_60
    # ЭКСГАУТЕРx__АГРЕГАТ__Mx_75
    # ЭКСГАУТЕРx__АГРЕГАТ__Mx_90
    # ЭКСГАУТЕРx__АГРЕГАТ__Mx_105
    # ЭКСГАУТЕРx__АГРЕГАТ__Mx_120

    X_train = pd.read_csv(csv_filename, parse_dates=True)
    X_train = X_train.set_index("DT")

    model_m1 = catboost.CatBoostClassifier()
    model_m1.load_model(os.path.join(ml_models_path, ml_model_m1_filename))
    proba_m1 = model_m1.predict_proba(X_train.values)

    model_m3 = catboost.CatBoostClassifier()
    model_m3.load_model(os.path.join(ml_models_path, ml_model_m3_filename))
    proba_m3 = model_m3.predict_proba(X_train.values)

    plot_script, plot_div, tables = [], [], []

    df_m = pd.DataFrame({
        'Время': X_train.index,
        'Вероятность M1': [x[1] for x in proba_m1],
        'Вероятность M3': [x[1] for x in proba_m3],
    })
    plot_title = ""

    df_m1 = df_m.iloc[:, [0, 1]]
    df_m3 = df_m.iloc[:, [0, 2]]

    # Visualization
    pointsize = 3
    scatter = hv.Scatter(df_m1).opts(width=PLOT_WIDTH, height=PLOT_HEIGHT, xlabel=df_m1.columns[0], ylabel=df_m1.columns[1],
                                  size=pointsize, xrotation = 90,
                                  title=plot_title, tools=['hover'])
    scatter = scatter * hv.Curve(df_m1)
    scatter = scatter * hv.Scatter(df_m3).opts(width=PLOT_WIDTH, height=PLOT_HEIGHT, xlabel=df_m3.columns[0], ylabel=df_m3.columns[1],
                                  size=pointsize, xrotation = 90,
                                  title=plot_title, tools=['hover'])
    scatter = scatter * hv.Curve(df_m3)
    scatter_script, scatter_div = bokeh.embed.components(hv.render(scatter))

    plot_script.append(scatter_script)
    plot_div.append(scatter_div)

    table_html = df_m.set_index('Время').to_html(classes="table table-striped")
    tables.append(table_html)

    # Here comes another table

    return {'exhauster': exhauster, 'agregat': agregat,
            'plot_script': plot_script,
            'plot_div': plot_div,
            'table_html': tables}
