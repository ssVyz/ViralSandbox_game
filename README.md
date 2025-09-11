# Virus Sandbox Prototype

This repository hosts an experimental Python application that models basic viral mechanics using discrete turn-based simulation. The project is an unfinished prototype and not a complete game.

## Status

- Prototype quality; many features are incomplete or missing.
- Data formats and interfaces are unstable and may change.

## Architecture

- Single-file implementation: `viralsandbox.py`.
- Simulation rules and entities are described in JSON.
- Uses only Python standard library modules (Tkinter for GUI, json for storage, etc.).

## Requirements

- Python 3.8 or newer.
- Tkinter library (bundled with most Python installations).

## Running

```bash
python viralsandbox.py
```

On first run, choose **Create Sample Database** to generate example genes and entities.

## Project Layout

- `viralsandbox.py` – main application.
- `requirements.txt` – list of used Python modules.
- `250817_virsim_default_24.json` – example database produced by the prototype.

## Development Notes

This repository is intended for experimentation and further development. Code lacks automated tests and extensive validation; contributions should focus on improving simulation accuracy, modular design, or data handling.

## License

Provided as-is for educational and research purposes.
