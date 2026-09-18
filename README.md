# Agentic AI — Lecture Files

Notebooks and code from class, one folder per session (W02b, W03a, ...).

This repo is meant to live inside your course project folder:

```
your-course-folder/
├── .venv/            your environment (created once, see the setup guide)
├── .env              your API keys (copy from example.env)
└── lecture-files/    this repo
    └── W02b/         one folder per class day
```

Setup instructions: see the Week 2b setup guide on the course site.

To get each day's files:

```bash
cd lecture-files
git pull
```

Do not commit changes here; if you edit a notebook and a later pull conflicts,
copy your version elsewhere and run `git checkout .` to reset.
