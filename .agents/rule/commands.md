# Common Commands

Run in Jetson/Robotic Arm environment:

```bash
python agent.py
```

Run a single command-line instruction:

```bash
python agent2.py "Grab the red block and show it to me"
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run tests:

```bash
python -m pytest
```

> [!IMPORTANT]
> **OS Target**: This project is exclusively designed to be run in a **Linux/Jetson environment**. It will NOT be run on Windows. Do not write or suggest Windows-specific scripts or PowerShell commands.
