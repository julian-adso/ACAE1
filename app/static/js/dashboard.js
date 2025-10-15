document.addEventListener('DOMContentLoaded', async function () {
    const employeeSelect = document.getElementById('employee-select');
    const calendarEl = document.getElementById('calendar');
    const detailsContent = document.getElementById('details-content');

    // =============================
    // 📅 Inicializar FullCalendar
    // =============================
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek', // vista semanal con horas
        slotMinTime: "06:00:00",     // inicio horario visible
        slotMaxTime: "20:00:00",     // fin horario visible
        locale: 'es',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek'
        },
        height: 'auto',
        events: [], // se llenará dinámicamente
        eventClick: function (info) {
            updateDetailsPanel(info.event.extendedProps);
        }
    });
    calendar.render();

    // =============================
    // 👥 Cargar lista de empleados
    // =============================
    async function cargarEmpleados() {
        try {
            const res = await fetch('/api/empleados');
            const empleados = await res.json();

            // limpiar select antes de llenarlo
            employeeSelect.innerHTML = '';

            empleados.forEach(emp => {
            const option = document.createElement('option');
            option.value = emp.id;
            option.textContent = emp.name;
            option.setAttribute('data-tipo', emp.tipo);  // ✅ agrega esto
            employeeSelect.appendChild(option);
        });


            // seleccionar primer empleado por defecto
            if (empleados.length > 0) {
                employeeSelect.value = empleados[0].id;
                actualizarCalendario(empleados[0].id);
            }
        } catch (error) {
            console.error("Error cargando empleados:", error);
        }
    }

    // =============================
    // ⏰ Cargar asistencias al calendario
    // =============================
    async function actualizarCalendario(userId) {
    try {
        const selectedOption = employeeSelect.options[employeeSelect.selectedIndex];
        const tipo = selectedOption.getAttribute('data-tipo');
        const res = await fetch(`/api/empleado/${tipo}/${userId}/asistencia`);

        const data = await res.json();

        if (data.success) {
            // Definir límites de hora por jornada
            const horarios = {
                manana: "07:10:00",
                tarde: "13:10:00",
                noche: "18:10:00"
            };

            const jornada = data.jornada?.toLowerCase() || "manana";
            const limite = horarios[jornada];

            // 1️⃣ Agrupar eventos por fecha
            const eventosPorDia = {};
            data.eventos.forEach(ev => {
                const fecha = ev.extendedProps.fecha;
                if (!eventosPorDia[fecha]) {
                    eventosPorDia[fecha] = [];
                }
                eventosPorDia[fecha].push(ev);
            });

            // 2️⃣ Evaluaciones solo con ingresos
            const evaluaciones = Object.entries(eventosPorDia).map(([fecha, eventos]) => {
                const ingresos = eventos.filter(e => e.tipo === "ingreso" && e.extendedProps.hora);
                const ausente = eventos.some(e => e.tipo === "ausencia" || e.extendedProps.estado === "Ausente");

                if (ausente) {
                    return {
                        title: "❌ Ausente",
                        start: fecha,
                        allDay: true,
                        className: "absent",
                        extendedProps: { fecha, estado: "Ausente" }
                    };
                }

                if (ingresos.length === 0) {
                    return {
                        title: "❌ Falta",
                        start: fecha,
                        allDay: true,
                        className: "absent",
                        extendedProps: { fecha, estado: "Falta" }
                    };
                }

                ingresos.sort((a, b) => a.extendedProps.hora.localeCompare(b.extendedProps.hora));
                const primerIngreso = ingresos[0];

                if (primerIngreso.extendedProps.hora <= limite) {
                    return {
                        title: "✅ Asistencia",
                        start: fecha,
                        allDay: true,
                        className: "on-time",
                        extendedProps: { fecha, hora: primerIngreso.extendedProps.hora, estado: "Asistencia" }
                    };
                } else {
                    return {
                        title: "⚠️ Retardo",
                        start: fecha,
                        allDay: true,
                        className: "late",
                        extendedProps: { fecha, hora: primerIngreso.extendedProps.hora, estado: "Retardo" }
                    };
                }
            });

            // 3️⃣ Normalizar ingresos y salidas para el calendario
            const ingresosYsalidas = data.eventos
                .filter(ev => ev.extendedProps.hora) // 🔹 Solo eventos con hora válida
                .map(ev => {
                    const fechaHora = `${ev.extendedProps.fecha}T${ev.extendedProps.hora}`;

                    // Log de debug para ver qué llega
                    console.log("Evento normalizado:", ev.tipo, fechaHora);

                    return {
                        title: ev.tipo === "ingreso"
                            ? `Ingreso: ${ev.extendedProps.hora}`
                            : `Salida: ${ev.extendedProps.hora}`,
                        start: fechaHora,
                        className: ev.tipo === "ingreso" ? "ingreso-event" : "salida-event",
                        extendedProps: ev.extendedProps
                    };
            });

            // 4️⃣ Combinar todo → ingresos + salidas + evaluaciones
            const todosEventos = [...ingresosYsalidas, ...evaluaciones];

            // 5️⃣ Refrescar calendario
            calendar.removeAllEvents();
            calendar.addEventSource(todosEventos);

            resetDetailsPanel();
            updateSummary(evaluaciones);
        } else {
            console.warn("Error:", data.message);
        }
    } catch (error) {
        console.error("Error cargando asistencias:", error);
    }
}

    // =============================
    // 📌 Panel de detalles (lado derecho)
    // =============================
    function updateDetailsPanel(props) {
        let content = `<div><strong>Fecha:</strong> ${props.fecha}</div>`;
        if (props.hora_salida || props.hora) {
            content += `<div><strong>Salida:</strong> ${props.hora_salida || props.hora}</div>`;
        }
        if (props.estado) content += `<div><strong>Estado:</strong> ${props.estado}</div>`;
        if (props.motivo) content += `<div><strong>Motivo:</strong> ${props.motivo}</div>`;

        detailsContent.innerHTML = content;
    }

    function resetDetailsPanel() {
        detailsContent.innerHTML = '<p>Seleccione un evento en el calendario para ver los detalles.</p>';
        document.getElementById('summary-content').innerHTML = '<p>Resumen no disponible.</p>';
    }

    function updateSummary(eventos) {
        let asistencias = 0;
        let retardos = 0;
        let faltas = 0;

        eventos.forEach(ev => {
            if (ev.className === 'on-time') asistencias++;
            else if (ev.className === 'late') retardos++;
            else if (ev.className === 'absent') faltas++;
        });

        const resumenHTML = `
            <h4>📊 Resumen de asistencia</h4>
            <div><strong>✅ Asistencias:</strong> ${asistencias}</div>
            <div><strong>⚠️ Retardos:</strong> ${retardos}</div>
            <div><strong>❌ Faltas:</strong> ${faltas}</div>
        `;

        document.getElementById('summary-content').innerHTML = resumenHTML;
    }

    // =============================
    // 🎯 Cambio de empleado en select
    // =============================
    employeeSelect.addEventListener('change', (e) => {
        actualizarCalendario(e.target.value);
    });

    // =============================
    // 🚀 Inicializar al cargar
    // =============================
    cargarEmpleados();

    // =============================
    // 📝 Exportar detalles del mes en Excel
    // =============================
    document.getElementById('export-details-btn').addEventListener('click', async function () {
        const tipo = employeeSelect.options[employeeSelect.selectedIndex].getAttribute('data-tipo');
        const userId = employeeSelect.value;
        window.location.href = `/api/exportar_excel/${tipo}/${userId}`;
    });


});