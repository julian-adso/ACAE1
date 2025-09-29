document.addEventListener('DOMContentLoaded', () => {

    // --- DATOS DE EJEMPLO ---
    // En una aplicación real, estos datos vendrían de una base de datos.


    const HORA_ENTRADA_OFICIAL = '09:00';

    // --- ELEMENTOS DEL DOM ---
    const asistenciasCountEl = document.getElementById('asistencias-count');
    const fallasCountEl = document.getElementById('fallas-count');
    const historyTableBodyEl = document.querySelector('#history-table tbody');

    // --- LÓGICA ---
    let asistencias = 0;
    let fallas = 0;

    // Procesar datos y llenar la tabla
    attendanceData.forEach(record => {
        const row = document.createElement('tr');

        const fechaCell = document.createElement('td');
        fechaCell.textContent = record.date;
        row.appendChild(fechaCell);

        const horaCell = document.createElement('td');
        const estadoCell = document.createElement('td');
        const statusSpan = document.createElement('span');
        statusSpan.classList.add('status');
        
        if (record.entryTime) {
            asistencias++;
            horaCell.textContent = record.entryTime;
            
            if (record.entryTime > HORA_ENTRADA_OFICIAL) {
                statusSpan.textContent = 'Tarde';
                statusSpan.classList.add('status-tarde');
            } else {
                statusSpan.textContent = 'Puntual';
                statusSpan.classList.add('status-puntual');
            }
        } else {
            fallas++;
            horaCell.textContent = '---';
            statusSpan.textContent = 'Ausente';
            statusSpan.classList.add('status-ausente');
        }
        
        estadoCell.appendChild(statusSpan);
        row.appendChild(horaCell);
        row.appendChild(estadoCell);

        historyTableBodyEl.appendChild(row);
    });

    // Actualizar los contadores en las tarjetas
    asistenciasCountEl.textContent = asistencias;
    fallasCountEl.textContent = fallas;

});

