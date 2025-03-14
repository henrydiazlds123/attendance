
```
attendance
├─ app
│  ├─ babel.cfg
│  ├─ config
│  │  ├─ base.py
│  │  ├─ development.py
│  │  ├─ production.py
│  │  └─ __init__.py
│  ├─ forms
│  │  ├─ announcement.py
│  │  ├─ attendance.py
│  │  ├─ auth.py
│  │  ├─ business.py
│  │  ├─ clase.py
│  │  ├─ hymn.py
│  │  ├─ meeting_center.py
│  │  ├─ member.py
│  │  ├─ organization.py
│  │  ├─ sacrament_meeting.py
│  │  ├─ speaker.py
│  │  ├─ user.py
│  │  └─ __init__.py
│  ├─ messages.pot
│  ├─ models
│  │  ├─ announcements.py
│  │  ├─ attendances.py
│  │  ├─ base.py
│  │  ├─ bishoprics.py
│  │  ├─ business.py
│  │  ├─ classes.py
│  │  ├─ hymns.py
│  │  ├─ meeting_centers.py
│  │  ├─ members.py
│  │  ├─ organizations.py
│  │  ├─ sacrament_agendas.py
│  │  ├─ sacrament_meetings.py
│  │  ├─ speakers.py
│  │  ├─ users.py
│  │  └─ __init__.py
│  ├─ passenger_wsgi.py
│  ├─ requirements.txt
│  ├─ routes
│  │  ├─ admin.py
│  │  ├─ announcements.py
│  │  ├─ attendance.py
│  │  ├─ auth.py
│  │  ├─ bussines.py
│  │  ├─ centers.py
│  │  ├─ classes.py
│  │  ├─ hymns.py
│  │  ├─ members.py
│  │  ├─ name_correction.py
│  │  ├─ organizations.py
│  │  ├─ pdf.py
│  │  ├─ register.py
│  │  ├─ sacrament_meeting.py
│  │  ├─ speakers.py
│  │  ├─ stats.py
│  │  ├─ swal.py
│  │  ├─ users.py
│  │  └─ __init__.py
│  ├─ static
│  │  ├─ css
│  │  │  └─ styles.css
│  │  ├─ img
│  │  │  └─ flags
│  │  │     ├─ en.png
│  │  │     ├─ es.png
│  │  │     ├─ lang.svg
│  │  │     └─ pt.png
│  │  ├─ js
│  │  │  └─ scripts.js
│  │  └─ locales
│  │     ├─ pivot.cs.coffee
│  │     ├─ pivot.da.coffee
│  │     ├─ pivot.de.coffee
│  │     ├─ pivot.es.coffee
│  │     ├─ pivot.fr.coffee
│  │     ├─ pivot.it.coffee
│  │     ├─ pivot.jp.coffee
│  │     ├─ pivot.nl.coffee
│  │     ├─ pivot.pl.coffee
│  │     ├─ pivot.pt.coffee
│  │     ├─ pivot.ru.coffee
│  │     ├─ pivot.sq.coffee
│  │     ├─ pivot.tr.coffee
│  │     └─ pivot.zh.coffee
│  ├─ templates
│  │  ├─ admin
│  │  │  ├─ admin.html
│  │  │  ├─ admin_script.html
│  │  │  ├─ name_correction.html
│  │  │  ├─ non_attendance.html
│  │  │  └─ with_attendance.html
│  │  ├─ agendas
│  │  │  ├─ add.html.html
│  │  │  └─ list.html
│  │  ├─ announcements
│  │  │  ├─ add.html
│  │  │  └─ list.html
│  │  ├─ attendance
│  │  │  ├─ attendance.html
│  │  │  ├─ check.html
│  │  │  ├─ check_script.html
│  │  │  ├─ list.html
│  │  │  ├─ list_script.html
│  │  │  ├─ list_table.html
│  │  │  ├─ manual.html
│  │  │  ├─ manual_script.html
│  │  │  ├─ report.html
│  │  │  ├─ report_script.html
│  │  │  └─ report_table.html
│  │  ├─ auth
│  │  │  ├─ login.html
│  │  │  └─ login_script.html
│  │  ├─ base.html
│  │  ├─ business
│  │  │  ├─ add.html
│  │  │  └─ list.html
│  │  ├─ classes
│  │  │  ├─ list.html
│  │  │  └─ list_script.html
│  │  ├─ errors
│  │  │  └─ 4xx.html
│  │  ├─ form
│  │  │  ├─ form.html
│  │  │  └─ macros.html
│  │  ├─ hymns
│  │  │  ├─ add.html
│  │  │  └─ list.html
│  │  ├─ index.html
│  │  ├─ layout.html
│  │  ├─ meeting_centers
│  │  │  └─ list.html
│  │  ├─ members
│  │  │  ├─ add.html
│  │  │  ├─ list.html
│  │  │  ├─ list_script.html
│  │  │  └─ pivot.html
│  │  ├─ organizations
│  │  │  └─ list.html
│  │  ├─ partials
│  │  │  ├─ flashes.html
│  │  │  ├─ footer.html
│  │  │  ├─ form_filter.html
│  │  │  ├─ head.html
│  │  │  ├─ navbar.html
│  │  │  └─ scripts
│  │  │     └─ bottom.html
│  │  ├─ pdfs
│  │  │  ├─ list.html
│  │  │  └─ list_script.html
│  │  ├─ reset_name.html
│  │  ├─ sacrament_meetings
│  │  │  ├─ add.html
│  │  │  ├─ edit.html
│  │  │  └─ list.html
│  │  ├─ speakers
│  │  │  ├─ add.html
│  │  │  └─ list.html
│  │  ├─ stats
│  │  │  ├─ stats.html
│  │  │  └─ stats_script.html
│  │  └─ users
│  │     └─ list.html
│  ├─ translations
│  │  ├─ es
│  │  │  └─ LC_MESSAGES
│  │  │     ├─ messages.mo
│  │  │     └─ messages.po
│  │  └─ pt
│  │     └─ LC_MESSAGES
│  │        ├─ messages.mo
│  │        └─ messages.po
│  ├─ utils.py
│  └─ __init__.py
├─ instance
│  ├─ attendance.db
│  ├─ attendance_dev.db
│  └─ attendance_dev_519.db
├─ routes.py
└─ run.py

```