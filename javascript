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
const generateUrl = function() {
    let url = new URL(window.location);
    let params = new URLSearchParams();
    params.set('fromDate', fromDate.value);
    params.set('toDate', toDate.value);
    if (details.checked) params.set('details', '');
    for (const uid of document.querySelectorAll("[name^='uid#']:checked")) {
        params.set(uid.name, '');
    }
    url.search = params;
    window.location = url.toString();
}   
