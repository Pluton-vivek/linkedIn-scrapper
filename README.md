# LinkedIn Profile to ATS-Friendly Resume

This project provides a small Python CLI that:

1. Scrapes/parses LinkedIn profile content (from a URL or saved HTML).
2. Extracts structured profile data.
3. Generates an ATS-friendly resume in Markdown and plain text.

> ⚠️ Note: LinkedIn pages are often authentication-gated and may block automated scraping. For reliable usage, export/save your own profile HTML and parse that file.

## Features

- Parse profile from:
  - `--html-file` (recommended)
  - `--profile-url` (best-effort public scraping)
- Extract common sections:
  - Name, headline, location, summary
  - Experience
  - Education
  - Skills
- Generate ATS resume files:
  - `resume.md`
  - `resume.txt`

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Option 1: Parse saved LinkedIn HTML

```bash
python linkedin_ats_resume.py --html-file /path/to/linkedin_profile.html --out-dir output
```

### Option 2: Best-effort scrape from public profile URL

```bash
python linkedin_ats_resume.py --profile-url "https://www.linkedin.com/in/your-handle/" --out-dir output
```

## Output

Generated files in `--out-dir`:

- `profile_data.json`
- `resume.md`
- `resume.txt`

## Run tests

```bash
python -m unittest -v
```
