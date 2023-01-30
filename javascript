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
