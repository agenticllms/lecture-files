# Deploying on Render

The app is `app.py`: your team from `bugteam/team.py` behind `bugteam_ui.py`. It imports your
`bugteam/` package, so it works once notebooks 01 and 02 pass their final cells, and not before.

Anyone with the URL can press "Fix", and every bug fixed is about 5 to 15 chat calls against your
Gemini key and half a minute of Daytona sandbox time per verification. Share the URL only in your
submission.

## Steps

1. Put the app in a GitHub repo of your own. It needs only these:

   ```
   app.py  bugteam_ui.py  bugteam/  repo/  issues.json  requirements.txt  render.yaml  .gitignore
   ```

   Your submission repository also holds the notebooks; Render ignores them. `.gitignore` keeps
   `.env` out. Check with `git status` that `.env` is not listed before you push.
2. On Render: **New +** > **Blueprint**, pick the repo. It reads `render.yaml`.
3. It will ask for the two `sync: false` variables, `GOOGLE_API_KEY` and `DAYTONA_API_KEY`. Paste
   them.
4. Deploy. The build installs `requirements.txt`, then runs `python app.py`. The first start takes
   a few minutes.

The sandboxes run on Daytona. Docker does not exist on Render, so do not set `SANDBOX=docker` there.

## Checking it

Open the URL Render gives you and log in. Fix #6, a bug: triage should say `bug`, the chat should
show the fixer handing its fix to the verifier and the verifier's decision, and the report should
appear at the bottom when the run finishes. Then fix #9, which is not a bug: triage should close it
without a fix.

Free instances sleep after 15 minutes without traffic and take about a minute to wake, so the first
request after a pause is slow. That is the instance, not your agents.

## When it fails

- **"No open ports detected."** `app.py` binds to `0.0.0.0` on `$PORT`. If you changed the launch
  line, change it back.
- **The app loads and every run is an error.** `GOOGLE_API_KEY` or `DAYTONA_API_KEY` is missing or
  wrong, or you have used the day's quota. The error in the app and the Render logs say which.
- **"NotImplementedError" in the app.** A function in `bugteam/` is still a stub. You ran the
  notebook but did not move your code into the module.
- **It works locally and not on Render.** Check that `.env` does not set `CHAT_BACKEND` or
  `SANDBOX`. Render uses Gemini and Daytona, and Ollama does not exist there.
- **Sandboxes left running after a crash.** Check the Daytona dashboard and delete them.
