document.addEventListener("DOMContentLoaded", () => {


  // Detect system preference and user setting
  const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const storedTheme = localStorage.getItem('theme');
  const currentTheme = storedTheme || (systemPrefersDark ? 'dark' : 'light');
  
  document.documentElement.setAttribute('data-bs-theme', currentTheme);

  // Toggle button functionality
  const themeSwitcher = document.getElementById('themeSwitcher');
  themeSwitcher.addEventListener('click', () => {
      const newTheme = document.documentElement.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-bs-theme', newTheme);
      localStorage.setItem('theme', newTheme);
  });











  
  const attendanceForm   = document.getElementById("attendanceForm");
  const studentNameInput = document.getElementById("studentName");

// ------------------------------------------------------------
  setTimeout(() => {
    const flashMessages = document.getElementById('flash-messages');
    if (flashMessages) {
      flashMessages.style.display = 'none';
    }
  }, 5000); // Oculta los mensajes flash después de 5 segundos


// ------------------------------------------------------------
  // Verifica si el usuario está autenticado usando la variable de sesión proporcionada por el servidor
  const isLoggedIn = document.body.classList.contains("logged-in"); // Asegúrate de agregar esta clase si el usuario ha iniciado sesión
  const savedName  = localStorage.getItem("studentName");

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
        console.log("Respuesta del servidor:", data);  // Depuración

        if (response.ok && data.success) {
            Swal.fire({
                title: "Éxito",
                text: `¡${data.student_name}, tu asistencia a la clase de ${data.class_name} ha sido registrada!`,
                icon: "success",
                confirmButtonText: "OK",
            }).then((result) => {
                if (result.isConfirmed) {
                  studentNameInput.value = ""
                    window.close();
                    if (savedName) {
                        window.location.href = "https://www.churchofjesuschrist.org/?lang=spa";
                    }
                }
            });
        } else {
            Swal.fire({
                title: "Error",
                text: `${data.nombre}! Ya tienes una asistencia registrada para el domingo ${data.sunday_date || 'desconocido'}!`,
                icon: "error",
                confirmButtonText: "OK",
            }).then((result) => {
                if (result.isConfirmed) {
                    window.close();
                    if (savedName) {
                        window.location.href = "https://www.churchofjesuschrist.org/?lang=spa";
                    }
                }
            });
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
  const formId = `deleteForm-${entityType}-${entityId}`;  // Formulario con id basado en el tipo de entidad y su ID

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
      document.getElementById(formId).submit();  // Envía el formulario correspondiente
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
