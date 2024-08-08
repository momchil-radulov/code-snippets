*** извличане на данните от селектирани чекбоксове ***
const checkboxes = document.querySelectorAll('input[data-user-id]:checked');
# създава масив от обекти, базиран на селектираните чекбоксове
const selectedData = Array.from(checkboxes).map(checkbox => ({
    day: checkbox.getAttribute('data-day'),
    hours: document.querySelector('input[name="hours"]').value,
}));

*** keep restful url ***
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

*** export a html table to csv ***
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

*** Паралелно изпълнение на js ***
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
