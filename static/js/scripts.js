document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  handleFlashMessages();
  autoFillStudentName();
  initAttendanceForm();
  initDeleteAllButton();
  initColorPickers();
  setupClassParameters();
  setTodayDate();
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
      Swal.fire(texts.great, texts.attendanceRecorded.replace("{student_name}", data.student_name), "success").then(() => {
        document.getElementById("studentName").value = "";
      });
    } else {
      // Obtener el mensaje de error desde el servidor o un mensaje genérico
      const errorMsg = data.message || (data.error_type === "main_class_restriction"
        ? texts.sundayClassRestriction
        : texts.alreadyRegistered.replace("{sunday_date}", data.sunday_date || "unknown"));
    
      Swal.fire(texts.errorTitle, errorMsg, "error");
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

// ----------- Configuración de parámetros de clase desde URL -----------
function setupClassParameters() {
  const urlParams  = new URLSearchParams(window.location.search);
  const className  = urlParams.get("class_name");
  const classCode  = urlParams.get("class");
  const sundayCode = urlParams.get("code");
  const unitNumber = urlParams.get("unit");

  if (className) {
    document.getElementById("classNameDisplay").textContent =  className;
    document.getElementById("className").value = decodeURIComponent(className);
    document.getElementById("classCode").value = classCode;
    document.getElementById("sundayCode").value = sundayCode;
    document.getElementById("unitNumber").value = unitNumber;

    const listGroupItems = document.querySelectorAll('.list-group-item');
    listGroupItems.forEach(item => {
        if (item.textContent.trim() === decodedClassName) {
            item.classList.add('active');
        } else {
            item.classList.remove('active'); // Asegurarse de que los demás elementos no estén activos
        }
    });



  } else {
    // Traducción de mensajes estáticos
    document.getElementById("classNameDisplay").textContent = 'Choose a Class';
    document.getElementById("button-addon2").disabled = true;
    document.getElementById("studentName").disabled = true;
  }
}

// ----------- Establecer la fecha actual -----------
function setTodayDate() {
  document.getElementById("date").value = new Date().toISOString().split("T")[0];
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


document.addEventListener('DOMContentLoaded', () => {
  const generateButton = document.getElementById('generate-extra-pdfs-btn');
  const extraClassForm = document.getElementById('extra-class-form');
  const dateInput      = document.getElementById('extra-class-date');

  generateButton.addEventListener('click', async (event) => {
      event.preventDefault(); // Evitar el envío automático del formulario

      const texts = await fetch('/get_swal_texts').then(response => response.json());

      // Mostrar SweetAlert2 para seleccionar la fecha
      const { value: selectedDate } = await Swal.fire({
          title: texts.selectDateExtraClasses,
          input: 'date',
          inputAttributes: {
              min: new Date().toISOString().split('T')[0] // Fechas desde hoy en adelante
          },
          showCancelButton: true,
          confirmButtonText: texts.confirm,
          cancelButtonText: texts.cancel,
          inputValidator: (value) => {
              if (!value) {
                  return texts.mustSelectDate;
              }
          }
      });

      if (selectedDate) {
          // Guardar la fecha en el campo oculto del formulario y enviarlo
          dateInput.value = selectedDate;
          extraClassForm.submit();
      } else {
          // Mostrar mensaje de cancelación
          Swal.fire(texts.actionCanceled, texts.noQrGenerated, 'info');
      }
  });
});


async function confirmDelete(entityType, entityId) {
  const formId = `deleteForm-${entityType}-${entityId}`; // Formulario con id basado en el tipo de entidad y su ID

  // Obtener los textos localizados para SweetAlert
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
      document.getElementById(formId).submit(); // Envía el formulario correspondiente
    }
  });
}

function changeLanguage(lang) {
  const currentUrl = window.location.href.split('?')[0];
  window.location.href = `${currentUrl}?lang=${lang}`;
}