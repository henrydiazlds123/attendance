from flask import Blueprint

from .pdf_route               import bp_pdf
from .auth_route              import bp_auth
from .swal_route              import bp_swal
from .users_route             import bp_users
from .admin_route             import bp_admin
from .stats_route             import bp_stats
from .classes_route           import bp_classes
from .register_route          import bp_register
from .bishopric_route         import bp_bishopric
from .attendance_route        import bp_attendance
from .organization_route      import bp_organization
from .import_member           import bp_import
from .name_correction_route   import bp_correction
from .centers_route           import bp_meeting_center
from .hymns_route             import bp_hymns
from .members_route           import bp_members
from .speakers_route          import bp_speakers
from .bussines_route          import bp_bussines
from .announcements_route     import bp_announcements
from .agendas_route           import bp_agenda


def register_blueprints(app):
    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_pdf, url_prefix='/pdf')
    app.register_blueprint(bp_swal, url_prefix='/swal')
    app.register_blueprint(bp_stats, url_prefix='/stats')
    app.register_blueprint(bp_admin, url_prefix='/admin')
    app.register_blueprint(bp_users, url_prefix='/users')
    app.register_blueprint(bp_import, url_prefix='/import')
    app.register_blueprint(bp_classes, url_prefix='/classes')
    app.register_blueprint(bp_register, url_prefix='/register')
    app.register_blueprint(bp_bishopric, url_prefix='/bishopric')
    app.register_blueprint(bp_attendance, url_prefix='/attendance')
    app.register_blueprint(bp_correction, url_prefix='/name_correction')
    app.register_blueprint(bp_organization, url_prefix='/organizations')
    app.register_blueprint(bp_meeting_center, url_prefix='/meeting_center')
    app.register_blueprint(bp_hymns, url_prefix='/hymns')
    app.register_blueprint(bp_members, url_prefix='/members')
    app.register_blueprint(bp_speakers, url_prefix='/speakers')
    app.register_blueprint(bp_bussines, url_prefix='/bussines')
    app.register_blueprint(bp_announcements, url_prefix='/announcements')
    app.register_blueprint(bp_agenda, url_prefix='/agenda')
