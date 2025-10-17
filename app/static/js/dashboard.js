document.addEventListener('DOMContentLoaded', async function () {
    const employeeSelect = document.getElementById('employee-select');
    const calendarEl = document.getElementById('calendar');
    const detailsContent = document.getElementById('details-content');

    // =============================
    // 📅 Inicializar FullCalendar
    // =============================
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'timeGridWeek',
        slotMinTime: "06:00:00",
        slotMaxTime: "20:00:00",
        locale: 'es',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek'
        },
        height: 'auto',
        events: [],
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

            employeeSelect.innerHTML = '';

            empleados.forEach(emp => {
                const option = document.createElement('option');
                option.value = emp.id;
                option.textContent = emp.name;
                option.setAttribute('data-tipo', emp.tipo);
                employeeSelect.appendChild(option);
            });

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
                const horarios = {
                    manana: "07:10:00",
                    tarde: "13:10:00",
                    noche: "18:10:00"
                };

                const jornada = data.jornada?.toLowerCase() || "manana";
                const limite = horarios[jornada];

                const eventosPorDia = {};
                data.eventos.forEach(ev => {
                    const fecha = ev.extendedProps.fecha;
                    if (!eventosPorDia[fecha]) eventosPorDia[fecha] = [];
                    eventosPorDia[fecha].push(ev);
                });

                const evaluaciones = Object.entries(eventosPorDia).map(([fecha, eventos]) => {
                    const ingresos = eventos.filter(e => e.tipo === "ingreso" && e.extendedProps.hora);
                    const ausente = eventos.some(e => e.tipo === "ausencia" || e.extendedProps.estado === "Ausente");

                    if (ausente) {
                        return { title: "❌ Ausente", start: fecha, allDay: true, className: "absent", extendedProps: { fecha, estado: "Ausente" } };
                    }

                    if (ingresos.length === 0) {
                        return { title: "❌ Falta", start: fecha, allDay: true, className: "absent", extendedProps: { fecha, estado: "Falta" } };
                    }

                    ingresos.sort((a, b) => a.extendedProps.hora.localeCompare(b.extendedProps.hora));
                    const primerIngreso = ingresos[0];

                    if (primerIngreso.extendedProps.hora <= limite) {
                        return { title: "✅ Asistencia", start: fecha, allDay: true, className: "on-time", extendedProps: { fecha, hora: primerIngreso.extendedProps.hora, estado: "Asistencia" } };
                    } else {
                        return { title: "⚠️ Retardo", start: fecha, allDay: true, className: "late", extendedProps: { fecha, hora: primerIngreso.extendedProps.hora, estado: "Retardo" } };
                    }
                });

                const ingresosYsalidas = data.eventos
                    .filter(ev => ev.extendedProps.hora)
                    .map(ev => {
                        const fechaHora = `${ev.extendedProps.fecha}T${ev.extendedProps.hora}`;
                        return {
                            title: ev.tipo === "ingreso"
                                ? `Ingreso: ${ev.extendedProps.hora}`
                                : `Salida: ${ev.extendedProps.hora}`,
                            start: fechaHora,
                            className: ev.tipo === "ingreso" ? "ingreso-event" : "salida-event",
                            extendedProps: ev.extendedProps
                        };
                    });

                const todosEventos = [...ingresosYsalidas, ...evaluaciones];

                calendar.removeAllEvents();
                calendar.addEventSource(todosEventos);

                resetDetailsPanel();
                updateSummary(evaluaciones, userId, tipo);
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

    // =============================
    // 📊 Resumen + botones
    // =============================
    function updateSummary(eventos, empleadoId, tipo) {
        let asistencias = 0, retardos = 0, faltas = 0;

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
            <div style="margin-top:10px;">
                <button id="btn-modificar" class="btn warning">Modificar empleado</button>
                <button id="btn-eliminar" class="btn danger">Eliminar empleado</button>
            </div>
        `;

        document.getElementById('summary-content').innerHTML = resumenHTML;

        document.getElementById('btn-eliminar').addEventListener('click', () => eliminarEmpleado(empleadoId, tipo));
        document.getElementById('btn-modificar').addEventListener('click', () => abrirModalEdicion(empleadoId, tipo));
    }

    // =============================
    // 🎯 Cambio de empleado
    // =============================
    employeeSelect.addEventListener('change', (e) => {
        actualizarCalendario(e.target.value);
    });

    // =============================
    // 🚀 Inicializar
    // =============================
    cargarEmpleados();

    // =============================
    // 📤 Exportar Excel
    // =============================
    document.getElementById('export-details-btn').addEventListener('click', async function () {
        const tipo = employeeSelect.options[employeeSelect.selectedIndex].getAttribute('data-tipo');
        const userId = employeeSelect.value;
        window.location.href = `/api/exportar_excel/${tipo}/${userId}`;
    });
});

// =============================
// 🗑️ Eliminar empleado
// =============================
async function eliminarEmpleado(id, tipo) {
    if (!confirm("¿Seguro que deseas eliminar este empleado? Esta acción no se puede deshacer.")) return;
    const resp = await fetch(`/api/empleado/${tipo}/${id}`, { method: "DELETE" });
    const data = await resp.json();
    alert(data.message);
    if (data.success) location.reload();
}

// =============================
// ✏️ Modal de edición con datos reales
// =============================
async function abrirModalEdicion(id, tipo) {
    const modal = document.createElement('div');
    modal.classList.add('modal');
    modal.innerHTML = `
        <div class="modal-content">
            <span id="close-modal" class="close-btn">&times;</span>
            <h3>Editar Empleado</h3>
            <label>Usuario:</label>
            <input type="text" id="edit-username">
            <label>Documento:</label>
            <input type="text" id="edit-document">
            <label>Teléfono:</label>
            <input type="text" id="edit-phone">
            <label>Email:</label>
            <input type="email" id="edit-email">
            <label>Horario:</label>
            <select id="edit-horario">
                <option value="Mañana">Mañana</option>
                <option value="Tarde">Tarde</option>
                <option value="Noche">Noche</option>
            </select>
            <label>Nueva contraseña (opcional):</label>
            <input type="password" id="edit-password">
            <div class="modal-actions">
                <button id="save-changes" class="btn success">Guardar</button>
                <button id="cancel-edit" class="btn danger">Cancelar</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);

    // 🔹 Cargar datos reales
    const resp = await fetch(`/api/empleado/${tipo}/${id}`);
    const data = await resp.json();
    if (!data.success) {
        alert('Error cargando datos del empleado');
        return modal.remove();
    }

    const emp = data.empleado;
    document.getElementById('edit-username').value = emp.username || '';
    document.getElementById('edit-document').value = emp.document || '';
    document.getElementById('edit-phone').value = emp.phone || '';
    document.getElementById('edit-email').value = emp.email || '';
    document.getElementById('edit-horario').value = emp.horario || 'Mañana';

    // 🔹 Eventos de cierre y guardado
    document.getElementById('close-modal').onclick = () => modal.remove();
    document.getElementById('cancel-edit').onclick = () => modal.remove();

    document.getElementById('save-changes').onclick = async () => {
        const payload = {
            username: document.getElementById('edit-username').value,
            document: document.getElementById('edit-document').value,
            phone: document.getElementById('edit-phone').value,
            email: document.getElementById('edit-email').value,
            horario: document.getElementById('edit-horario').value,
            password: document.getElementById('edit-password').value
        };

        const resp = await fetch(`/api/empleado/${tipo}/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const result = await resp.json();
        alert(result.message);
        if (result.success) {
            modal.remove();
            location.reload();
        }
    };
}
