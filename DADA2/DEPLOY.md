# Deploying on Render

The app is `app.py`: the agent from `rag/agent.py` behind `agentui.py`, the
same Gradio UI as W03b, W05b and DADA1. It imports your `rag/` package, so it
works once notebooks 01 to 03 pass their final cells, and not before.

## The app searches. It never indexes.

You built the index in notebook 01. The deployed app embeds each question the
same way and searches that index; it never embeds the corpus.
`EMBEDDINGS=cloudflare`, which `render.yaml` already sets, is the same backend
you indexed with. If you indexed with the Ollama backup instead, the setting
is still `cloudflare`: it is the same model hosted, its vectors match, and it
searches the same `dada2-1024` index.

Everything else is the same code you ran in the notebooks.

## Steps

1. Put the app in a GitHub repo of your own. It needs only these:

   ```
   app.py  agentui.py  rag/  corpus/  eval/  requirements.txt  render.yaml  .gitignore
   ```

   Leave the notebooks out. `.gitignore` keeps `.env` out; check with
   `git status` that it is not listed before you push.
2. On Render: **New +** > **Blueprint**, pick the repo. It reads `render.yaml`.
3. It will ask for the four `sync: false` variables. Paste your keys. The
   Cloudflare token only needs Workers AI read permission.
4. Deploy. The build installs `requirements.txt`, then runs `python app.py`.
   The first start takes a few minutes.

## Checking it

Open the URL Render gives you and ask one of the example questions. Then ask
one the corpus cannot answer.

Free instances sleep after 15 minutes without traffic and take about a minute
to wake, so the first question after a pause is slow. That is the instance,
not your agent.

## When it fails

- **"No open ports detected."** `app.py` binds to `0.0.0.0` on `$PORT`. If you
  changed the launch line, change it back.
- **Build fails on a package.** You added something to `requirements.txt` that
  does not fit in 512 MB of memory.
- **The app loads and every answer is an error.** One of the four keys is
  missing or wrong. The Render logs say which call failed.
- **Answers are fine locally and empty on Render.** `CLOUDFLARE_API_TOKEN` or
  `COHERE_API_KEY` is missing, so the app cannot embed the question; or the
  index name does not match the one you built.
