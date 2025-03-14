from flask import Blueprint

from .pdf               import bp_pdf
from .auth              import bp_auth
from .swal              import bp_swal
from .users             import bp_users
from .admin             import bp_admin
from .stats             import bp_stats
from .classes           import bp_classes
from .register          import bp_register
from .attendance        import bp_attendance
from .organizations     import bp_organization
from .name_correction   import bp_correction
from .centers           import bp_meeting_center
from .hymns             import bp_hymns
from .members           import bp_members
from .speakers          import bp_speakers
from .bussines          import bp_bussines
from .announcements     import bp_announcements
from .sacrament_meeting import bp_sacrament_meeting

#bp = Blueprint('routes', __name__)

def register_blueprints(app):
    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_pdf, url_prefix='/pdf')
    app.register_blueprint(bp_swal, url_prefix='/swal')
    app.register_blueprint(bp_stats, url_prefix='/stats')
    app.register_blueprint(bp_admin, url_prefix='/admin')
    app.register_blueprint(bp_users, url_prefix='/users')
    app.register_blueprint(bp_classes, url_prefix='/classes')
    app.register_blueprint(bp_register, url_prefix='/register')
    app.register_blueprint(bp_attendance, url_prefix='/attendance')
    app.register_blueprint(bp_correction, url_prefix='/name_correction')
    app.register_blueprint(bp_organization, url_prefix='/organizations')
    app.register_blueprint(bp_meeting_center, url_prefix='/meeting_center')
    app.register_blueprint(bp_hymns, url_prefix='/hymns')
    app.register_blueprint(bp_members, url_prefix='/members')
    app.register_blueprint(bp_speakers, url_prefix='/speakers')
    app.register_blueprint(bp_bussines, url_prefix='/bussines')
    app.register_blueprint(bp_announcements, url_prefix='/announcements')
    app.register_blueprint(bp_sacrament_meeting, url_prefix='/sacrament_meetings')
