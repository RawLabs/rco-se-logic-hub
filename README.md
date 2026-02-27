# RCO SE Logic HUD

**Raw Cast Orbital — Engineering Tools Division**

SE Logic HUD generates a clean, human-readable snapshot of a Space Engineers blueprint’s automation logic.

No flow diagrams.  
No entity ID noise.  
Just: Block → Action → Target.

---

## What It Does

Given a `bp.sbc` file, this tool:

- Extracts all Timer Blocks  
- Extracts all Event Controllers  
- Parses toolbar actions  
- Resolves block targets by name (not Entity ID)  
- Flags missing targets  
- Splits missing targets into:  
  - Likely Detached AQR Module  
  - Likely Broken Links  
- Outputs a versioned Markdown report  
- Writes a detailed run log  

---

## Why This Exists

Space Engineers automation grows fast.

Maintaining logic requires constant UI bouncing:

- Terminal → Search → Toolbar  
- Event Controller → Block → Search  
- AI Recorder → Waypoints → Actions  

This tool eliminates that friction.

You get a full automation snapshot in one scrollable document.

---

# Step 1 — Export Your Blueprint

Inside Space Engineers:

1. Open the Blueprint Menu (`F10`)  
2. Select your blueprint  
3. Click **Open Blueprint Folder**  
4. Locate the blueprint directory  
5. Copy the file named:bp.sbc

This is the file the tool reads.

---

# Recommended Folder Structure

Create a working folder named after your blueprint:
PowerBattleCruiser/
├─ bp.sbc
├─ se_logic_hud_v1_05.py (Linux / Python users)
└─ RCO_SE_Logic_HUD.exe (Windows users)


Keep reports inside this folder.

This keeps logic reports versioned and clean.

---

# Linux / Python Users

## Requirements

- Python 3.8+

Check version: python3 --version


## Run

From inside your blueprint folder:python3 se_logic_hud_v1_05.py bp.sbc

## Output

The tool will generate:
SE_Logic_HUD_<BlueprintName><YYYYMMDD-HHMM>.md
SE_Logic_HUD<BlueprintName>_<YYYYMMDD-HHMM>.log.txt

---

# Windows Users (EXE Version)

Download the latest release from the GitHub Releases page.

## Drag & Drop Method (Recommended)

1. Place `RCO_SE_Logic_HUD.exe` inside your blueprint folder.  
2. Drag `bp.sbc` onto the EXE.  
3. The tool runs automatically.  
4. Output files appear in the same folder.  

No Python installation required.

---

# Output Contents

The generated HUD includes:

- Timer Blocks (A→Z)  
- Event Controllers (A→Z)  
- Repair List (Missing Targets)  
- Slot-by-slot action mapping  
- Parameter values (angles, speeds, etc.)  
- Detached vs Broken classification  

Everything visible in one document.

---

# Logging

Each run creates a timestamped log file.

The log records:

- Load status  
- XML parse result  
- Block indexing count  
- Timer and Event counts  
- Missing target summary  
- Success / Failure state  

This ensures transparency and traceability.

---

# Versioning

Output filenames include:

Blueprint Title + Date + Time

This prevents accidental overwrite and supports revision tracking.

---

# Philosophy

Raw Cast Orbital tools follow:

- KISS principles  
- No hidden behavior  
- No external dependencies  
- Clear output  
- Transparent logic  
- Signal over greeble  

---

**Powered by Raw Cast Labs**  
A division of Raw Cast Orbital (RCO)

Engineering over noise.


