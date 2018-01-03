# app/main/views.py
from werkzeug.datastructures import Headers
from werkzeug.wrappers import Response

#///////////////////
from flask import render_template, session, redirect , url_for, current_app, stream_with_context

from . import main
from .forms import YoutubeForm
from .comment_loader import yt
import pandas as pd

@main.route('/', methods=['GET', 'POST'])
def index(): 
    form = YoutubeForm()
    
    if form.validate_on_submit():
        old_url = session.get('url')
        old_fileType = session.get('fileType')
        old_output = session.get('output')

        session['url'] = form.video_url.data
        session['fileType'] = form.downloadFileType.data
        session['output'] =form.outputFileNmae.data
        form.video_url.data= ''
        form.outputFileNmae.data = ''

        if session['url'] != None:
            v_id = session['url'].split('v=')[1]
            df = yt(v_id)
            
            def generate():
                for index, row in df.iterrows():
                    temp = row.str.encode('utf-8').str.decode('utf-8')
                    print(temp)
                    yield ','.join(temp) + '\n'

        output = session['output'] + '.csv'
        # add a filename
        headers = Headers()
        headers.set('Content-Disposition', 'attachment', filename=output)

        return Response(generate(),
        mimetype='text/csv', headers=headers)

    else:
        return render_template('yt.html', form=form)


