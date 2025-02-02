
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  handleFlashMessages();
  autoFillStudentName();
  initAttendanceForm();
  initDeleteAllButton();
  initColorPickers();

});

// ----------- Módulo de tema (Dark/Light Mode) -----------
function initTheme() {
  const themeSwitcher = document.getElementById("themeSwitcher");
  const body          = document.body;
  const currentTheme  = localStorage.getItem("theme") || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");

  const updateTheme = () => {
    body.setAttribute("data-bs-theme", currentTheme);
    themeSwitcher.innerHTML = currentTheme === "dark" ? '<i class="bi bi-moon-stars"></i>' : '<i class="bi bi-brightness-high"></i>';
  };

  updateTheme();

  themeSwitcher.addEventListener("click", () => {
    const newTheme = currentTheme === "dark" ? "light" : "dark";
    localStorage.setItem("theme", newTheme);
    updateTheme();
  });
}

// ----------- Manejo de mensajes flash -----------
function handleFlashMessages() {
  const flashMessages = document.getElementById("flash-messages");
  if (flashMessages) {
    setTimeout(() => (flashMessages.style.display = "none"), 3000);
  }
}


// ----------- Rellenar nombre del estudiante automáticamente -----------
function autoFillStudentName() {
  const studentNameInput = document.getElementById("studentName");
  const savedName        = localStorage.getItem("studentName");
  const isLoggedIn       = document.body.classList.contains("logged-in");

  if (!isLoggedIn && savedName) {
    studentNameInput.value = savedName;
    sendAttendanceForm(new FormData(document.getElementById("attendanceForm")));
  }
}

// ----------- Inicializar el formulario de asistencia -----------
async function initAttendanceForm() {
  const attendanceForm = document.getElementById("attendanceForm");
  if (!attendanceForm) return;

  attendanceForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const studentName = document.getElementById("studentName").value.trim();
    const regex       = /^[^\s]+ [^\s]+$/;
    if (!regex.test(studentName)) {
      const texts = await fetch('/get_swal_texts').then(response => response.json());
      Swal.fire(texts.warningTitle, texts.nameFormatText, "warning");
      return;
    }

    if (!document.body.classList.contains("logged-in")) {
      localStorage.setItem("studentName", studentName);
    }

    sendAttendanceForm(new FormData(attendanceForm));
  });
}

async function sendAttendanceForm(formData) {
  try {
    const response = await fetch("/registrar", { method: "POST", body: formData });
    const data     = await response.json();
    const texts    = await fetch('/get_swal_texts').then(response => response.json());

    if (response.ok && data.success) {
      Swal.fire({
        title            : texts.great,
        text             : texts.attendanceRecorded.replace("{student_name}", data.student_name),
        icon             : "success",
        confirmButtonText: "OK"
      }).then((result) => { 
        if (result.isConfirmed) {
          const isLoggedIn = document.body.classList.contains("logged-in");
          if (!isLoggedIn) { // Usuario NO logueado
            let savedName = localStorage.getItem("studentName");
            if (!savedName) {
              localStorage.setItem("studentName", data.student_name);
            }
            window.location.href = "https://www.churchofjesuschrist.org";
          } else { // Usuario logueado
            document.getElementById("studentName").value = "";
          }
        }
      });
    } else {
      const errorMsg = data.message || (data.error_type === "main_class_restriction"
          ? texts.sundayClassRestriction
          : texts.alreadyRegistered.replace("{sunday_date}", data.sunday_date || "unknown"));
  
      Swal.fire({
          title: texts.errorTitle,
          text: errorMsg,
          icon: "error",
          confirmButtonText: "OK"
      }).then((result) => {
          if (result.isConfirmed) {
              const isLoggedIn = document.body.classList.contains("logged-in");
  
              if (!isLoggedIn && localStorage.getItem("studentName")) {
                  // Si el usuario NO está logueado y tiene un nombre guardado, redirigirlo
                  window.location.href = "https://www.churchofjesuschrist.org/";
              } else {
                  // Si el usuario está logueado, limpiar el campo de nombre
                  document.getElementById("studentName").value = "";
              }
          }
      });
    }
  } catch (error) {
    const texts = await fetch('/get_swal_texts').then(response => response.json());
    Swal.fire(texts.errorTitle, texts.connectionError, "error");
  }
}


// ----------- Botón para eliminar todos los registros -----------
function initDeleteAllButton() {
  const deleteAllButton = document.getElementById("delete_all");
  if (!deleteAllButton) return;

  deleteAllButton.addEventListener("click", async () => {
    const texts = await fetch('/get_swal_texts').then(response => response.json());

    Swal.fire({
      title             : texts.confirmDelete,
      text              : texts.yesDeleteEverything,
      icon              : "warning",
      showCancelButton  : true,
      confirmButtonColor: "#d33",
      cancelButtonColor : "#3085d6",
      confirmButtonText : texts.yesDeleteEverything,
      cancelButtonText  : texts.cancel,
    }).then((result) => {
      if (result.isConfirmed) {
        document.getElementById("deleteAllForm").submit();
      }
    });
  });
}


// ----------- Inicializar color pickers -----------
function initColorPickers() {
  const colorPickers = document.querySelectorAll('input[type="color"]');
  colorPickers.forEach((picker) => {
    const label = document.getElementById(`${picker.id}_label`);
    if (label) label.textContent = picker.value;
  });
}





// Agregar evento para manejar selección en list-group-item
document.addEventListener("DOMContentLoaded", () => {
  // Obtener todos los elementos de la lista
  const listGroupItems = document.querySelectorAll('.list-group-item');

  // Comprobar si hay un nombre de clase en la URL (decodificado)
  const className        = new URLSearchParams(window.location.search).get('class_name');
  const decodedClassName = className ? decodeURIComponent(className) : '';

  // Recorrer cada item y añadir o quitar la clase 'active'
  listGroupItems.forEach(item => {
    if (item.textContent.trim() === decodedClassName) {
      item.classList.add('active');
    } else {
      item.classList.remove('active'); // Asegurarse de que los demás elementos no estén activos
    }
  });
});


async function confirmDelete(entityType, entityId) {
  const formId = `deleteForm-${entityType}-${entityId}`;
  console.log(`Attempting to delete form with ID: ${formId}`);
  
  const formElement = document.getElementById(formId);
  if (!formElement) {
    Swal.fire({
      title: "Error",
      text : `The form with ID ${formId} does not exist.`,
      icon : "error",
    });
    return; // Salir si no encuentra el formulario
  }

  const texts = await fetch('/get_swal_texts').then(response => response.json());
  Swal.fire({
    title             : texts.confirmDelete,
    text              : texts.deleteOneRecordText,
    icon              : "warning",
    showCancelButton  : true,
    confirmButtonColor: "#d33",
    cancelButtonColor : "#3085d6",
    confirmButtonText : texts.yesDeleteIt,
    cancelButtonText  : texts.cancel,
  }).then((result) => {
    if (result.isConfirmed) {
      console.log(`Submitting form ID: ${formId}`);
      formElement.submit(); // Enviar el formulario
    }
  });
}

function changeLanguage(lang) {
  const currentUrl = window.location.href.split('?')[0];
  window.location.href = `${currentUrl}?lang=${lang}`;
}

// Definir la función correctName
async function correctName(checkbox) {
  // Obtener el nombre incorrecto y el ID del centro de reunión + textos para sweetalert
  const wrongName       = checkbox.getAttribute('data-wrong-name');
  const meetingCenterId = checkbox.getAttribute('data-meeting-center-id');
  const texts           = await fetch('/get_swal_texts').then(response => response.json());

  Swal.fire({
      title            : texts.wrongNameTitle,
      text             : texts.wrongNameText + wrongName,
      input            : 'text',
      inputLabel       : texts.wrongNameLabel,
      inputPlaceholder : texts.wrongNamePlaceholder,
      showCancelButton : true,
      confirmButtonText: texts.confirmSave,
  }).then((result) => {
      if (result.isConfirmed) {
          const correctName = result.value;

          // Verificar que el nombre tenga el formato "Apellido, Nombre"
          const namePattern = /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+,\s[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/;
          if (!namePattern.test(correctName)) {
            Swal.fire({
                icon : 'error',
                title: texts.incorrectPatternLabel,
                text : texts.incorrectPatternText,
            });
            return; // Detener la ejecución si el formato es incorrecto
        }

          // Enviar la corrección al servidor usando fetch
          fetch('/update_name_correction', {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                  wrong_name       : wrongName,
                  correct_name     : correctName,
                  meeting_center_id: meetingCenterId
              })
          })
          .then(response => response.json())
          .then(data => {
              if (data.success) {
                  Swal.fire(texts.successTitle, texts.successMessage, 'success');
                  // Deshabilitar el checkbox después de la corrección
                  checkbox.disabled = true;
              } else {
                  Swal.fire(texts.errorTitle, texts.errorMessage, 'error');
              }
          });
      } else {
          Swal.fire(texts.cancelledTitle, texts.cancelledMessage, 'info');
      }
  });
}

async function confirmRevert(id) {
  // Obtiene las traducciones de los textos desde el servidor
  const texts = await fetch('/get_swal_texts').then(response => response.json());

  // Muestra el SweetAlert con los textos traducidos
  const result = await Swal.fire({
      title: texts.revertTitle,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonText: texts.revertConfirmButton,
      cancelButtonText: texts.cancel,
  });

  // Si el usuario confirma, envía el formulario
  if (result.isConfirmed) {
      document.getElementById('revert-form-' + id).submit();
  }
}

