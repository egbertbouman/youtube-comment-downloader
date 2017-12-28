# app/main/views.py
import csv
from datetime import datetime
from io import StringIO
import codecs
from werkzeug.datastructures import Headers
from werkzeug.wrappers import Response

#///////////////////
from flask import render_template, session, redirect , url_for, current_app, stream_with_context
from flask_login import login_required, current_user

from . import main
from .forms import YoutubeForm
from .commet_loader import yt
import pandas as pd


# from .comment_loader import yt

# @main.route('/')
# def index():
#     return render_template('index.html')

@main.route('/', methods=['GET', 'POST'])
def index(): 
    a = None
    choice = None
    data_list = None
    output = None
    df = None
    form = YoutubeForm()
    
    if form.validate_on_submit():
        a = form.video_url.data
        choice = form.downloadFileType.data
        output = form.outputFileNmae.data
        form.video_url.data = ''
        
    if a!= None:
        l = []
        output = output + '.xlsx'
        v_id = a.split('v=')[1]
        l.append(v_id)
        l.append(choice)
        df = yt(v_id,output)
        print('done')

        def generate():
            data = StringIO()
            w = csv.writer(data)
            # write header
            w.writerow(tuple(df.columns.values))
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

            # write each log item
            for index, row in df.iterrows():
                w.writerow(row)
                yield data.getvalue()
                data.seek(0)
                data.truncate(0)
    #     return render_template('yt.html', form=form, data_list=l ,tables=[df.to_html(classes='test')],
    # titles = ['test'])
        # add a filename
        headers = Headers()
        headers.set('Content-Disposition', 'attachment', filename='test.csv')

        return Response(
        stream_with_context(generate()),
        mimetype='text/csv', headers=headers
    )
    else:
        return render_template('yt.html', form=form)

@main.route('/test')
def download_log():
    def generate():
        data = StringIO()
        w = csv.writer(data)

        # write header
        w.writerow(('action', 'timestamp'))
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)

        # write each log item
        for item in log:
            w.writerow((
                item[0],
                item[1].isoformat()  # format datetime as string
            ))
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    # add a filename
    headers = Headers()
    headers.set('Content-Disposition', 'attachment', filename='log.csv')

    # stream the response as the data is generated
    return Response(
        stream_with_context(generate()),
        mimetype='text/csv', headers=headers
    )
        

