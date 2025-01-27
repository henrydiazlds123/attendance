document.addEventListener("DOMContentLoaded", () => {

  const attendanceForm = document.getElementById("attendanceForm");
  const studentNameInput = document.getElementById("studentName");

  // Detect system preference and user setting
  const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const storedTheme = localStorage.getItem('theme');
  const currentTheme = storedTheme || (systemPrefersDark ? 'dark' : 'light');
  const themeSwitcher = document.getElementById('themeSwitcher');

  // Verifica si el usuario está autenticado usando la variable de sesión proporcionada por el servidor
  const isLoggedIn = document.body.classList.contains("logged-in"); // Asegúrate de agregar esta clase si el usuario ha iniciado sesión
  const savedName = localStorage.getItem("studentName");


  document.documentElement.setAttribute('data-bs-theme', currentTheme);

  // Toggle button functionality
  themeSwitcher.addEventListener('click', () => {
    const newTheme = document.documentElement.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-bs-theme', newTheme);
    localStorage.setItem('theme', newTheme);
  });

  // ------------------------------------------------------------
  setTimeout(() => {
    const flashMessages = document.getElementById('flash-messages');
    if (flashMessages) {
      flashMessages.style.display = 'none';
    }
  }, 5000); // Oculta los mensajes flash después de 5 segundos


  // ------------------------------------------------------------
  if (!isLoggedIn && savedName) {
    studentNameInput.value = savedName;
    sendAttendanceForm(new FormData(attendanceForm));
  }

  if (attendanceForm) {
    attendanceForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      const studentName = studentNameInput.value.trim();
      const regex = /^[^\s]+ [^\s]+$/;
      if (!regex.test(studentName)) {
        Swal.fire(
          "Advertencia",
          "Por favor, ingresa tu nombre en el formato de 'Nombre Apellido'. Ejemplo: 'Pedro Perez'.",
          "warning"
        );
        return;
      }
      if (!isLoggedIn) {
        localStorage.setItem("studentName", studentName);
      }
      sendAttendanceForm(new FormData(this));
    });
  }


  // ------------------------------------------------------------
  async function sendAttendanceForm(formData) {
    try {
      const response = await fetch("/registrar", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      console.log("Respuesta del servidor:", data); // Depuración

      const showSwal = (title, text, icon, redirectUrl) => {
        Swal.fire({
          title: title,
          text: text,
          icon: icon,
          confirmButtonText: "OK",
        }).then((result) => {
          if (result.isConfirmed) {
            studentNameInput.value = "";
            window.close();
            if (redirectUrl) {
              window.location.href = redirectUrl;
            }
          }
        });
      };
  
      if (response.ok && data.success) {
        showSwal(
          "Éxito",
          `¡${data.student_name}, tu asistencia a la clase de ${data.class_name} ha sido registrada!`,
          "success",
          savedName ? "https://www.churchofjesuschrist.org/my-home?lang=spa" : ""
        );
      } else {
        // Verifica el tipo de error
        let studentName = data.student_name || data.nombre || "Desconocido";
        let errorMessage = "";
        if (data.error_type === "main_class_restriction") {
          errorMessage = `${studentName}! No se puede registrar asistencia para una clase Main fuera del domingo.`;
        } else {
          errorMessage = `${data.nombre || data.student_name}! Ya tienes una asistencia registrada para el domingo ${data.sunday_date || 'desconocido'}!`;
        }
        Swal.fire({
          title: "Error",
          text: errorMessage,
          icon: "error",
          confirmButtonText: "OK",
        }).then((result) => {
          if (result.isConfirmed) {
            window.close();
            if (savedName) {
              window.location.href = "https://www.churchofjesuschrist.org/my-home?lang=spa";
            }
          }
        });
  
        showSwal("Error", errorMessage, "error", savedName ? "https://www.churchofjesuschrist.org/my-home?lang=spa" : "");
      }
  
    } catch (error) {
      console.error("Error:", error);
      Swal.fire(
        "Error",
        "Hubo un problema al conectar con el servidor.",
        "error"
      );
    }
  }

});

// ------------------------------------------------------------
const deleteAllButton = document.getElementById("delete_all");
if (deleteAllButton) {
  deleteAllButton.addEventListener("click", function () {
    Swal.fire({
      title: "¿Estás seguro?",
      text: "Esta acción eliminará todos los registros y no se puede deshacer.",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: "#d33",
      cancelButtonColor: "#3085d6",
      confirmButtonText: "Sí, eliminar todo",
      cancelButtonText: "Cancelar",
    }).then((result) => {
      if (result.isConfirmed) {
        document.getElementById("deleteAllForm").submit();
      }
    });
  });
}


// ------------------------------------------------------------
function confirmDelete(entityType, entityId) {
  const formId = `deleteForm-${entityType}-${entityId}`; // Formulario con id basado en el tipo de entidad y su ID

  Swal.fire({
    title: "¿Estás seguro?",
    text: "¡No podrás deshacer esta acción!",
    icon: "warning",
    showCancelButton: true,
    confirmButtonColor: "#d33",
    cancelButtonColor: "#3085d6",
    confirmButtonText: "Sí, eliminar",
    cancelButtonText: "Cancelar",
  }).then((result) => {
    if (result.isConfirmed) {
      document.getElementById(formId).submit(); // Envía el formulario correspondiente
    }
  });
}

// ------------------------------------------------------------
function clearName() {
  if (document.getElementById("chkNameClear") && document.getElementById("chkNameClear").checked) {
    localStorage.clear();
    console.log("Student name cleared!");
  }
}

// ------------------------------------------------------------
function confirmPromotion(userId, username) {
  Swal.fire({
    title: '¿Estás seguro?',
    text: `¿Deseas promover a ${username} a administrador?`,
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#28a745',
    cancelButtonColor: '#d33',
    confirmButtonText: 'Sí, promover'
  }).then((result) => {
    if (result.isConfirmed) {
      document.getElementById(`promoteForm-${userId}`).submit();
    }
  });
}

// ------------------------------------------------------------
const themeSwitcher = document.getElementById('themeSwitcher');
const body          = document.body;
const currentTheme  = localStorage.getItem('theme') || 'light'; // Cargar tema guardado o 'light' por defecto

// Función para actualizar el tema y el icono
function updateTheme() {
  if (currentTheme === 'dark') {
    body.setAttribute('data-bs-theme', 'dark');
    themeSwitcher.innerHTML = '<i class="bi bi-moon-stars"></i>'; // Cambiar a luna
  } else {
    body.setAttribute('data-bs-theme', 'light');
    themeSwitcher.innerHTML = '<i class="bi bi-brightness-high">'; // Cambiar a sol
  }
}

// Inicializar el tema al cargar la página
window.addEventListener('DOMContentLoaded', () => {
  updateTheme(); // Asegurar que el tema y el icono estén bien al cargar
});

// Cambiar el tema al hacer clic en el botón
themeSwitcher.addEventListener('click', () => {
  // Alternar entre dark y light
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
  localStorage.setItem('theme', newTheme); // Guardar el nuevo tema en localStorage
  updateTheme(); // Actualizar tema y icono
});



function updateColorLabel(input) {
  const label = document.getElementById(`${input.id}_label`);
  if (label) {
      label.textContent = input.value;
  }
}

// Inicializa los valores de los color pickers en caso de recargar el formulario
document.addEventListener("DOMContentLoaded", function () {
  const colorPickers = document.querySelectorAll('input[type="color"]');
  colorPickers.forEach(picker => {
      const label = document.getElementById(`${picker.id}_label`);
      if (label) {
          label.textContent = picker.value;
      }
  });
});


// Configuración para mostrar y establecer la clase
const urlParams  = new URLSearchParams(window.location.search);
const className  = urlParams.get('class_name');
const classCode  = urlParams.get('class');
const sundayCode = urlParams.get('code');
const unitNumber = urlParams.get('unit');

console.log("Parámetros de la URL:", { className, classCode, sundayCode, unitNumber, }); // Salida de depuración

// Asigna valores a los campos ocultos
if (className) {
    const decodedClassName = decodeURIComponent(className);
    document.getElementById('classNameDisplay').textContent = `Class: ${decodedClassName}`;
    document.getElementById('className').value = decodedClassName;
    document.getElementById('sundayCode').value = sundayCode;
    document.getElementById('unitNumber').value = unitNumber;
    document.getElementById('classCode').value = classCode;

    // Agregar clase .active al elemento correspondiente
    const listGroupItems = document.querySelectorAll('.list-group-item');
    listGroupItems.forEach(item => {
        if (item.textContent.trim() === decodedClassName) {
            item.classList.add('active');
        } else {
            item.classList.remove('active'); // Asegurarse de que los demás elementos no estén activos
        }
    });
} else {
    document.getElementById('classNameDisplay').textContent = 'Choose a Class';
    document.getElementById('button-addon2').disabled = true;
    document.getElementById('studentName').disabled = true;
}

// Establece la fecha actual
document.getElementById('date').value = new Date().toISOString().split('T')[0];