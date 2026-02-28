# RCO SE Logic HUD
![License](https://img.shields.io/badge/license-MIT-green)

**Raw Cast Orbital — Engineering Tools Division**

A lightweight blueprint logic viewer for Space Engineers.

See all Timer and Event automation in one organized report.

Just:

Block → Action → Target

Signal over greeble.

## What This Is

RCO SE Logic HUD is a standalone tool that reads a Space Engineers blueprint file (bp.sbc) and generates a clean, human-readable automation snapshot.

It is not a diagram generator.
It does not rewrite your logic.
It does not modify your blueprint.

It simply shows you what your automation is doing.

In one scrollable document.

What It Does

Given a bp.sbc file, the tool:

Extracts all Timer Blocks

Extracts all Event Controllers

Parses toolbar actions

Resolves targets by block name (not Entity ID)

Flags missing targets

Splits missing targets into:

Likely Detached AQR Module

Likely Broken Links

Generates a versioned Markdown report

Writes a detailed run log

Everything visible. Nothing hidden.

## Why This Exists

Space Engineers automation scales quickly.

Maintaining logic requires constant UI bouncing:

Terminal → Search → Toolbar
Event Controller → Block → Search
AI Recorder → Waypoints → Actions

After a while, it becomes friction.

This tool eliminates that friction.

You get a full automation snapshot in one document.

It exists to restore clarity.

(And possibly to give its author meaning in life.)

## Download

# Windows Users (Recommended for Most Players)

Go to the Releases section of this repository.

Download the latest:

RCO_SE_Logic_HUD.exe

No installation required.

# Finding Your Blueprint (Windows – Steam)

Space Engineers stores blueprint files here:

Local Blueprints
%AppData%\SpaceEngineers\Blueprints\local

Workshop Blueprints
%AppData%\SpaceEngineers\Blueprints\workshop

Quick Method

Press Win + R

Paste:Quick Method

Press Win + R

Paste: %AppData%\SpaceEngineers\Blueprints\local

Press Enter

Open your blueprint folder

Drag bp.sbc onto RCO_SE_Logic_HUD.exe

That’s it.

The report will generate in the same folder where the EXE is located
(usually your Downloads folder).

No file copying required.


## Executing (Linux / Python)

Download:

se_logic_hud_v1_05.py

Requires:

Python 3.8+

From the directory containing bp.sbc after liberating from Windows run: python3 se_logic_hud_v1_05.py bp.sbc
Or from anywhere: python3 /path/to/se_logic_hud_v1_05.py /path/to/bp.sbc

The report will be generated beside the script.

No GUI.
No installer.
No registry.
Just execution.

## What to Expect

After running the tool, you will see:
SE_Logic_HUD_<BlueprintName>_<YYYYMMDD-HHMM>.md
SE_Logic_HUD_<BlueprintName>_<YYYYMMDD-HHMM>.log.txt

## Output Contents


The generated HUD includes:

Timer Blocks (A→Z)

Event Controllers (A→Z)

Repair List (Missing Targets)

Slot-by-slot action mapping

Parameter values (angles, speeds, speeds, overrides, etc.)

Detached vs Broken classification

Everything visible in one document.


## Logging

Each run creates a timestamped log file.

The log records:

Load status

XML parse result

Block indexing count

Timer and Event counts

Missing target summary

Success / Failure state

This ensures transparency and traceability.


## Versioning

Output filenames include:

Blueprint Title + Date + Time

This prevents accidental overwrite and supports revision tracking.


## Philosophy


Raw Cast Orbital tools follow:

KISS principles

No hidden behavior

No external dependencies

Clear output

Transparent logic

Signal over greeble

Clarity is the product.

Powered by Raw Cast Labs
A division of Raw Cast Orbital (RCO)

Engineering over noise.

