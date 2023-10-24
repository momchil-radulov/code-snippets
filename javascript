### TypeScript ###
# check code
tsc --noEmit


# prettier (code formatter)
npm install --save-dev --save-exact prettier  # install prettier
npx prettier --check .  # only check
npx prettier --write .  # write formatting
npx prettier --write `git diff --name-only master...`  # format files on you branch
npx prettier --write $(git diff --name-only main...)  # format files on you branch

# OAK - middleware framework for Deno's http server, including a router middleware
https://github.com/oakserver/oak - за deno

// Timing
app.use(async (ctx, next) => {
  const start = Date.now();
  await next();
  const ms = Date.now() - start;
  ctx.response.headers.set("X-Response-Time", `${ms}ms`);
});
// Error handling
app.use(async (ctx, next) => {
  try {
    await next();
  } catch (err) {
    //Resolve error here
  }
});

# javascript
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

# export a html table to csv
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
