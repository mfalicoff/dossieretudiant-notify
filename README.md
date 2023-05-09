# DossierEtudiant Notify

A lot of the code was inspired by https://github.com/mart123p/dossieretudiant-notify/tree/master, please do check it out.

The main motivation for this repo was to avoid using Azure + update some of the code that no longer works.

## Usage:

Copy the `.env.example` file to `.env` and fill in all the fields

Create your virtual environment:

```bash
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -r requirements.txt
```

The script can then be left to run in the background with `nohup`:

```bash
$ PYTHONUNBUFFERED=1 nohup python3 main.py > output.log &
```

