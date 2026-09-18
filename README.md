# Agentic AI — Lecture Files

Notebooks and code from class, one folder per session (W02b, W03a, ...).

This repo is meant to live inside your course project folder:

```
agentic-ai-course/
├── .venv/            your environment (created once, see the setup guide)
├── .env              your API keys (copy from example.env)
├── lecture-files/    this repo, one folder per class day (read-only)
│   └── W02b/
└── W02b/             your working copy of a day's files
```

Setup instructions: see the Week 2b setup guide on the course site.

To get each day's files, pull and then work in a copy:

```bash
cd lecture-files
git pull
cd ..
cp -r lecture-files/W03a W03a   # then open the copy, not the original
```

Treat this repo as read-only. Running a notebook saves outputs into it, which
counts as a local edit and will block a future pull. If that happens:
`git restore .` from inside lecture-files, then pull again.
