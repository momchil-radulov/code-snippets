$(document).ready(function() {
    // Code to be executed when the DOM is ready
});
document.addEventListener("DOMContentLoaded", function() {
    // Code to be executed when the DOM is ready
});

location.reload();
location.href = location.href;
window.location OR location

readyFn( { title: '', message: data.message, result: 'success|error', time: '10' } );

/*** сигурно сетване на property базирано на върнат резултат  ***/
if (typeof data.is_ratings !== 'undefined' && data.is_ratings !== null) {
    var surveyCheckbox = $('#is_ratings');
    if (surveyCheckbox.length) {
        surveyCheckbox.prop('checked', parseInt(data.is_ratings, 10) > 0);
    }
}

/*** търсене в DOM  ***/
const textarea = document.getElementById('елемент–съсед-на-търсения');
const iframe = textarea.parentElement.querySelector('iframe.wysihtml5-sandbox');
const targetElement = iframe.contentDocument.querySelector('body.wysihtml5.form-control.input-sm.about.wysihtml5-editor');
// jQuery
const textarea = $('#елемент–съсед-на-търсения');
const iframe = textarea.parent().find('iframe.wysihtml5-sandbox');
const targetElement = iframe.contents().find('body.wysihtml5.form-control.input-sm.about.wysihtml5-editor');
targetElement.text('some text');

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

function toggleFavorite(modulKey, menuTitle) {
    let favContainer = document.getElementById("favoriteLinks");
    let existingLink = document.getElementById("fav-" + modulKey);

    if (existingLink) {
        // Ако линкът вече е в "Любими", премахни го
        favContainer.removeChild(existingLink);
    } else {
        // Добави нов любим линк
        let newLink = document.createElement("a");
        newLink.href = "/base_url/" + modulKey;
        newLink.innerText = menuTitle;
        newLink.id = "fav-" + modulKey;
        newLink.style = "display: block; margin: 5px; color: red; font-weight: bold;";
        favContainer.appendChild(newLink);
    }
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

# Последно посетени страници
function loadVisited() {
    // Показване на списъка в HTML
    let listContainer = document.getElementById("pagesList");
    listContainer.innerHTML = ""; // Изчиства преди обновяване

    visitedPages.forEach(page => {
        let listItem = document.createElement("li");
        let link = document.createElement("a");
        link.href = page;
        link.textContent = page;
        listItem.appendChild(link);
        listContainer.appendChild(listItem);
    });
}
function saveVisited() {
    const maxPages = 10; // Запазва последните 10 страници
    let visitedPages = JSON.parse(localStorage.getItem("visitedPages")) || [];

    const currentPage = window.location.href;

    if (!visitedPages.includes(currentPage)) {
        visitedPages.unshift(currentPage); // Добавя текущата страница най-отпред
        if (visitedPages.length > maxPages) {
            visitedPages.pop(); // Премахва най-стария запис
        }
        localStorage.setItem("visitedPages", JSON.stringify(visitedPages));
    }
}
