# app/routes/hymns.py
from flask import Blueprint, render_template, request, redirect, url_for
from app.models import db, Hymns

bp_hymns = Blueprint('hymns', __name__)

@bp_hymns.route('/')
def hymns():
    hymns = Hymns.query.all()
    return render_template('/hymns/list.html', hymns=hymns)

@bp_hymns.route('/add', methods=['GET', 'POST'])
def add_hymn():
    if request.method == 'POST':
        number = request.form['number']
        title = request.form['title']
        
        new_hymn = Hymns(number=number, title=title)
        db.session.add(new_hymn)
        db.session.commit()
        return redirect(url_for('hymns.hymns'))
    
    return render_template('/hymns/add.html')
