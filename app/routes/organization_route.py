from flask                   import Blueprint, render_template, redirect, url_for, flash
from flask_babel             import gettext as _
from app.models              import db, Organization
from app.forms               import OrganizationForm
from app.utils                   import *

bp_organization = Blueprint('organization', __name__)


# =============================================================================================
@bp_organization.route('/', methods=['GET'])
@role_required('Owner')
def organizations():
    organizations = Organization.query.all()
    return render_template('organizations/list.html', organizations=organizations)


# =============================================================================================
@bp_organization.route('/new', methods=['GET', 'POST'])
@role_required('Owner')
def create_organization():
    form = OrganizationForm()
    if form.validate_on_submit():
        new_org = Organization(name=form.name.data)
        try:
            db.session.add(new_org)
            db.session.commit()
            flash(_('Organization created successfully!'), 'success')
            return redirect(url_for('organization.organizations'))
        except Exception as e:
            db.session.rollback()
            flash(_('Error: Organization name must be unique.'), 'danger')
            return redirect(url_for('organization.organizations'))
    return render_template('/form/form.html', form=form, title=_('Create new Organization'), submit_button_text=_('Create'), clas='warning')


# =============================================================================================
@bp_organization.route('/edit/<int:id>', methods=['GET', 'POST'])
@role_required('Owner')
def edit_organization(id):
    organization = Organization.query.get_or_404(id)
    form         = OrganizationForm(obj=organization)
    if form.validate_on_submit():
        organization.name = form.name.data
        try:
            db.session.commit()
            flash(_('Organization updated successfully!'), 'success')
            return redirect(url_for('organization.organizations'))
        except Exception as e:
            db.session.rollback()
            flash(_('Error: Organization name must be unique.'), 'danger')
    return render_template('/form/form.html', form=form, title=_('Edit Organization'), submit_button_text=_('Update'), clas='warning', organization=organization)


# =============================================================================================
@bp_organization.route('/delete/<int:id>', methods=['POST'])
@role_required('Owner')
def delete_organization(id):
    organization = Organization.query.get_or_404(id)
    try:
        db.session.delete(organization)
        db.session.commit()
        flash(_('Organization deleted successfully!'), 'success')
    except Exception as e:
        db.session.rollback()
        flash(_('Error: Could not delete organization.'), 'danger')
    return redirect(url_for('organization.organizations'))