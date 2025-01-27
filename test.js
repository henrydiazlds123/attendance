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
        ¡${data.student_name}, tu asistencia a la clase de ${data.class_name} ha sido registrada!,
        "success",
        savedName ? "https://www.churchofjesuschrist.org/my-home?lang=spa" : ""
      );
    } else {
      // Verifica el tipo de error
      let studentName = data.student_name || data.nombre || "Desconocido";
      let errorMessage = "";
      if (data.error_type === "main_class_restriction") {
        errorMessage = ${studentName}! No se puede registrar asistencia para una clase Main fuera del domingo.;
      } else {
        errorMessage = ${data.nombre || data.student_name}! Ya tienes una asistencia registrada para el domingo ${data.sunday_date || 'desconocido'}!;
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