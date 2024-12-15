document.addEventListener("DOMContentLoaded", function() {
    // Code to be executed when the DOM is ready
});

/*** търсене в DOM  ***/
let quantity = $(this).closest('tr').find('a.updateProduct').attr('data-quantity');

/*** извличане на данните от селектирани чекбоксове ***/
const checkboxes = document.querySelectorAll('input[data-user-id]:checked');
//# създава масив от обекти, базиран на селектираните чекбоксове
const selectedData = Array.from(checkboxes).map(checkbox => ({
    day: checkbox.getAttribute('data-day'),
    hours: document.querySelector('input[name="hours"]').value,
}));

/*** keep restful url ***/
const generateUrl = () => {
    let url = new URL(window.location);
    let params = new URLSearchParams();
    let users = [];
    params.set('fromDate', fromDate.value);
    params.set('toDate', toDate.value);
    if (details.checked) params.set('details', '');
    // for (const uid of document.querySelectorAll("[name^='uid.']:checked")) {
    //     params.set(uid.name, '');
    // }
    for (const uid of document.querySelectorAll("[data-user-id]:checked")) {
        users.push(uid.dataset.userId);
    }
    params.set('users', users.join('-'));
    url.search = params;
    window.location = url.toString();
}   

function camelCaseToText(text) {
  return text.replace(/([A-Z])/g, " $1");
}

/*** export a html table to csv ***/
function downloadCSV(csv, filename) {
    var csvFile = new Blob([csv], {type: "text/csv"});
    var downloadLink = $('<a></a>').attr({
        'download': filename,
        'href': window.URL.createObjectURL(csvFile),
        'target': '_blank',
        'style': 'display:none'
    }).appendTo('body');
    
    downloadLink[0].click();
    downloadLink.remove();
}

function exportTableToCSV(filename) {
    var csv = [];
    $("table tr").each(function() {
        var row = [];
        $(this).find('td, th').each(function() {
            row.push($(this).text());
        });
        csv.push(row.join(","));
    });

    downloadCSV(csv.join("\n"), filename);
}

// Бутон или линк:
// <button onclick="exportTableToCSV('filename.csv')">Export to CSV</button>

/*** Паралелно изпълнение на js ***/
    // Използване на Promise.all за паралелно изпълнение на всички fetch операции
    const results = await Promise.all(selectedData.map(item =>
        fetch('/order/validate', {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
            },
            body: JSON.stringify(item)
        })
    ));

    // Обработване на всеки резултат
    for (const result of results) {
        const data = await result.json();
        if (!data.success) {
            isValid = false;
            const errorValues = Object.values(data.errors);
            const newErrorMessage = '<ul>' + errorValues.map(error => `<li>${error}</li>`).join('') + '</ul>';
            if (!errorMessages.includes(newErrorMessage)) {
                errorMessages.push(newErrorMessage);
            }
        }
    }

/*** save data ***/
const saveData = async (selectedData, button) => {
    try {
        // Заключване на бутона за да се предотврати повторно изпращане
        button.disabled = true;
        button.classList.add('loading');

        const response = await fetch('/order/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify(selectedData)
        });

        // Проверка за HTTP грешки
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Проверка за успешен отговор
        if (data.success) {
            clearCheckedCheckboxes();
            displayMessage('success', "Успешно записахте данните.");
            await reloadTable();
        } else {
            handleErrors(data.errors);
        }
    } catch (error) {
        console.error('Save data:', error);
        displayMessage('error', "Възникна грешка при обработката на заявката.");
    } finally {
        // Отключване на бутона
        button.disabled = false;
        button.classList.remove('loading');
    }
};

const clearCheckedCheckboxes = () => {
    const checkboxes = document.querySelectorAll('input[data-product-id]:checked');
    checkboxes.forEach(checkbox => checkbox.checked = false);
};

const displayMessage = (type, message) => {
    const messageTextElement = document.getElementById(`${type}MessageText`);
    const messageElement = document.getElementById(`${type}Message`);
    messageTextElement.textContent = message;
    messageElement.style.display = "block";
};

const handleErrors = (errors) => {
    if (errors && errors.hours) {
        displayMessage('error', errors.hours);
    } else {
        displayMessage('error', "Възникна грешка при обработката на заявката.");
    }
};

const reloadTable = async () => {
    try {
        const response = await fetch(current_table);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const html = await response.text();
        document.getElementById('datatable_ajax').innerHTML = html;

        // Добавяне на събития за клик и промяна на новите елементи в таблицата
        $("td, th").click(handleCellClick);
        $('.productsSelectColumn_action').change(selectColumn);
    } catch (error) {
        console.error('Error loading link:', error);
        swal('Възникна грешка при зареждане на данните.', '', 'error');
    }
};

//# css
button.loading {
    cursor: not-allowed;
    opacity: 0.5;
}
