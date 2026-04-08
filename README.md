# StreamSync

## Requirements
- Python 3.12

## Install Python 3.12
### Linux
sudo apt update
sudo apt install python3.12

### Windows
winget install -e --id Python.Python.3.12

### macOS
brew install python@3.12

## Quickstart
### Create virtual environment
python -m venv .venv

### Activate virtual environment
#### Windows (CMD)
.venv\Scripts\activate

#### Windows PowerShell
.\.venv\Scripts\Activate.ps1

#### macOS / Linux
source .venv/bin/activate

### Install dependencies
python -m pip install -r requirements.txt

### Run migrations
python manage.py migrate

## Run server
python manage.py runserver

## Web link
[Render link](https://streamsync-bhmx.onrender.com/)

## Contributing providers
See [CONTRIBUTING_PROVIDERS.md](CONTRIBUTING_PROVIDERS.md) for instructions on adding new streaming services.
