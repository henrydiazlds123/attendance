from flask                   import Blueprint
from flask_babel             import gettext as _
from utils                   import *

bp_swal = Blueprint('swal', __name__)

# =============================================================================================
@bp_swal.route('/get_swal_texts', methods=['GET'])
def get_swal_texts():
    return {    
        'actionCanceled'          : _("Action canceled"),
        'alreadyRegistered'       : _("You already have registered assistance on {sunday_date}."),
        'atention'                : _("Attention"),
        'attendance_label'        : _("Attendance"),
        'attendance_unit'         : _("attendance(s)"),
        'attendance_value_label'  : _("Attendance"),
        'attendanceRecorded'      : _("¡{student_name}, your attendance was recorded!"),
        'cancel'                  : _("Cancel"),
        'cancelled'               : _("Cancelled"),
        'cancelledMessage'        : _("No correction has been made."),
        'chooseClass'             : _("Choose a Class"),
        'classesLabel'            : _("Classes"),
        'classesNumber'           : _("Number of Classes"),
        'classesTitle'            : _("Frequency of Classes per Month"),
        'cleared'                 : _("Cleared!"),
        'colorErrorText'          : _("There was a problem resetting the color."),
        'colorResetText'          : _("This will reset the class color to black."),
        'colorSuccessText'        : _("The color has been successfully restored."),
        'confirm'                 : _("Confirm"),
        'confirmDelete'           : _("You \'re sure?"),
        'confirmRegisterCancel'   : _("No, cancel!"),
        'confirmRegisterText'     : _("Do you want to register attendance for the selected students?"),
        'confirmRegisterTitle'    : _("Confirm Attendance Registration"),
        'confirmRegisterYes'      : _("Yes, register it!"),
        'confirmRegSuccessText'   : _("Attendance has been registered successfully."),
        'confirmRegSuccessTitle'  : _("Success"),
        'confirmSave'             : _("Confirm"),
        'connectionError'         : _("There was a problem connecting to the server."),
        'deleteConfirmationText'  : _("This action will delete all records and cannot be undone."),
        'deleteOneRecordText   '  : _("This record will be deleted."),
        'errorMessage'            : _("There was a problem saving the correction"),
        'errorTitle'              : _("Error"),
        'great'                   : _("Great!"),
        'incorrectPatternLabel'   : _("Incorrect format"),
        'incorrectPatternText'    : _("The name must be in the format 'Last Name, First Name', separated by a comma."),
        'members_label'           : _("members"),
        'monthly_attendance'      : _("Monthly Attendance"),
        'monthlyAttendancePerc'   : _("Monthly Attendance Percentage"),
        'months_label'            : _("Months"),
        'mustSelectDate'          : _("You must select a date!"),
        'nameFormatText'          : _("Please enter your name in \'First Name Last Name\' format."),
        'nameNotRemoved'          : _("Your name was not removed."),
        'nameRemoved'             : _("The name has been removed."),
        'noNameFound'             : _("No Name Found"),
        'noNameSaved'             : _("No name is currently saved."),
        'noQrGenerated'           : _("QR codes were not generated"),
        'promotionConfirmation'   : _("Yes, Do it!"),
        'promotionText'           : _("Do you want to promote \'{user_name}\' as a Power User?"),
        'promotionTitle'          : _("You 're sure?"),
        'registrationCancel'      : _("Attendance registration cancelled."),
        'registrationError'       : _("There was an error registering attendance."),
        'resetStudentName'        : _("Reset Student Name"),
        'revertConfirmButton'     : _("Revert"),
        'revertTitle'             : _("Are you sure you want to revert this correction?"),
        'savedNameText'           : _("The saved name is: \'{name}\'. Do you want to clear it?"),
        'selectDateExtraClasses'  : _("Select a date for Extra classes"),
        'successMessage'          : _("The name has been corrected"),
        'successTitle'            : _("¡Success"),
        'sundayClassRestriction'  : _("You cannot register a \'Sunday Class\' outside of Sunday."),
        'validationError'         : _("Error, There was a problem validating the attendance."),
        'warningTitle'            : _("warning"),
        'weeks_label'             : _("Weeks with attendance"),       
        'wrongNameLabel'          : _("Correct Format: Last Name, First Name"),
        'wrongNamePlaceholder'    : _("Enter the new name"),
        'wrongNameText'           : _("Please enter the correct name for "),
        'wrongNameTitle'          : _("Please enter the correct name"),
        'yes'                     : _("Yes"),
        'yesClearIt'              : _("Yes, clear it!"),
        'yesDeleteEverything'     : _("Yes, delete everything"),
        'yesDeleteIt'             : _("Yes, Delete it!"),
        'yesResetIt'              : _("Yes, Reset it!"),
    }