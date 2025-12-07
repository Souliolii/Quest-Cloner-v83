# Quest-Cloner-v83-AdventureMS

MapleStory Quest XML Cloner

A simple Python tool to duplicate MapleStory quest entries across the exported Classic XML files (Act.img.xml, Check.img.xml, QuestInfo.img.xml, etc.).
This removes the need to manually copy/paste quest blocks inside HaRepacker.

✨ Features

Clone an existing quest ID into a new custom quest ID

Automatically updates QuestInfo fields:

name

summary

rewardSummary

Works across all quest XMLs at once:

Act.img.xml

Check.img.xml

Exclusive.img.xml

PQuest.img.xml

QuestInfo.img.xml

Say.img.xml

Creates automatic .bak backups before modifying anything

Interactive prompts — no command-line arguments needed

Debug-friendly: prints out every file it touches

📂 Requirements

Python 3.8+

A folder containing:

Act.img.xml

Check.img.xml

Exclusive.img.xml

PQuest.img.xml

QuestInfo.img.xml

Say.img.xml

quest_helper.py (this tool)

These XML files come from HaRepacker → Export as Classic XML.

📥 Setup

Export your Quest.wz contents as Classic XML using HaRepacker.

Put all exported XMLs in one folder.

Place quest_helper.py in that same folder.

(Optional) Create a run_quest_helper.bat:

@echo off
cd /d "%~dp0"
python quest_helper.py
pause


This ensures Windows runs the script in the correct directory.

▶️ Usage

Run the script from Command Prompt:

cd /d "path\to\your\QuestXML"
python quest_helper.py


Or double-click run_quest_helper.bat.

The program will ask:

Base quest ID → ID you want to copy from (must already exist)

New quest ID → The new quest ID you want to create

Optional:

New quest name

New quest summary

New quest rewardSummary
(Leave blank to keep original text)

It will then clone the quest into every XML file that contains quest entries.

Example:

Base quest ID to copy FROM (existing ID): 20011
New quest ID to create: 9000001

New quest NAME (blank = keep original): My Custom Quest
New quest SUMMARY (blank = keep original): Talk to NPC to begin.
New quest REWARD SUMMARY (blank = keep original): Adventure begins!

🔧 What the script does

For each .img.xml file:

Searches for <imgdir name="BASE_ID">

Deep-clones it

Renames to <imgdir name="NEW_ID">

If file is QuestInfo.img.xml, updates its strings

Writes changes back

Creates a filename.xml.bak backup

🔄 After Editing

Re-import the edited XMLs into HaRepacker:

Open Quest.wz in HaRepacker

Right-click → Import XML

Select your modified files

Save Quest.wz

Place the updated WZ in your MapleStory client folder

Your new quest now exists and can be scripted on the server normally.

🧰 Troubleshooting
Script says:
Act.img.xml not found in this folder, skipping.


→ You ran the script from the wrong folder.
Use the .bat launcher or make sure CMD is in the same directory as the XMLs.

New quest not created?

Confirm the base quest ID actually exists in your XML files.
Open the XML and search for:

<imgdir name="YOUR_BASE_ID">

📄 License

MIT — free to use, modify, and redistribute.
