import pandas as pd
import numpy as np
import bokeh
import holoviews as hv
hv.extension('bokeh')

from time import sleep

PLOT_WIDTH, PLOT_HEIGHT = 600, 300


def run_inference(job_id, csv_filename, exhauster, agregat):
    """Вынес сюда "настоящий" код"""
    xlsx_df = pd.read_csv(csv_filename)
    # Now we may work with the uploaded Excel file as a dataframe
    print(xlsx_df.head(10))  # This makes no sense, but still

    pointsize = 3
    # Plotting a scatterplot
    df = pd.DataFrame({'Adasfadfds': [1, 2, 3, 4], 'Bdasdsads': [7, 8, 9, 1]})
    scatter = hv.Scatter(df).opts(width=PLOT_WIDTH, height=PLOT_HEIGHT, xlabel=df.columns[0], ylabel=df.columns[1],
                                  size=pointsize,
                                  title="my label", tools=['hover'])
    scatter = scatter * hv.Curve(df)

    scatter_script, scatter_div = bokeh.embed.components(hv.render(scatter))

    # table_attributes = 'class="table"'
    table_html = df.to_html(classes="table table-striped")

    sleep(2)

    return {'plot_script': [scatter_script],
            'plot_div': [scatter_div],
            'table_html': [table_html]}
