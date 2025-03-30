# app/routes/bussines.py
from flask import Blueprint, flash, render_template, redirect, url_for
from app.models import db, WardBusiness
from app.forms import WardBusinessForm

# Creamos el Blueprint
bp_bussines = Blueprint('bussines', __name__)

@bp_bussines.route('/new', methods=['GET', 'POST'])
def new_ward_business():
    form = WardBusinessForm()

    if form.validate_on_submit():
        ward_business = WardBusiness(
            agenda_id             = form.agenda_id.data ,
            type                  = form.type.data ,
            member_id             = form.member_id.data if form.member_id.data else None ,
            calling_name          = form.calling_name.data ,
            baby_name             = form.baby_name.data if form.type.data              == 'baby_blessing' else None,
            blessing_officiant_id = form.blessing_officiant_id.data if form.type.data  == 'baby_blessing' else None
        )

        db.session.add(ward_business)
        db.session.commit()
        flash('Ward business saved successfully!', 'success')
        return redirect(url_for('business.list'))

    return render_template('/business/add.html', form=form)