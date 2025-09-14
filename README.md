# SongSearch2

## Purpose
SongSearch2 is an experimental tool for searching and organizing songs by leveraging audio and metadata information.

## Prerequisites
- Python 3.x
- System libraries required by the dependencies listed in `requirements.txt`

## Installation
Install the Python dependencies:

```bash
pip install -r requirements.txt
```

## Usage
Run the application from the project root:

```bash
python -m songsearch
```

## macOS auto-start
To have SongSearch2 launch automatically when you log in on macOS, run:

```bash
./scripts/install_macos_launch_agent.sh
```

This script creates a `LaunchAgent` that starts the app at login and keeps it running.

## Running Tests
Execute the test suite with:

```bash
pytest
```

## Contributing
Contributions are welcome! Please open an issue or submit a pull request. Make sure to run the tests before submitting your changes.
