📘 Quest-Cloner v83 — AdventureMS
MapleStory Quest XML Cloner

A simple Python utility that duplicates MapleStory quest entries across exported Classic XML files (Act, Check, QuestInfo, Say, etc.).
This removes the need to manually copy/paste quest blocks in HaRepacker.

✨ Features

🔁 Clone an existing quest ID to a new quest ID

📝 Automatically updates QuestInfo fields:

name

summary

rewardSummary

📂 Works across all major quest XMLs:

Act.img.xml

Check.img.xml

Exclusive.img.xml

PQuest.img.xml

QuestInfo.img.xml

Say.img.xml

💾 Creates automatic .bak backups before modifying anything

🔍 Optional debug mode to show all operations

🧑‍💻 Fully interactive — no arguments needed

📦 Requirements

Python 3.8+

Folder containing the exported Classic XML quest files:

Act.img.xml
Check.img.xml
Exclusive.img.xml
PQuest.img.xml
QuestInfo.img.xml
Say.img.xml
quest_helper.py


These files come from HaRepacker → Export as Classic XML.

📥 Setup

Export Quest.wz as Classic XML using HaRepacker.

Place all exported .xml files in a single folder.

Put quest_helper.py into that folder.

(Optional): Create a run script to ensure the tool runs from the correct directory:

run_quest_helper.bat

@echo off
cd /d "%~dp0"
python quest_helper.py
pause

▶️ Usage

Run from Command Prompt:

cd /d "path\to\your\QuestXML"
python quest_helper.py


Or double-click run_quest_helper.bat.

You will be prompted for:

Base Quest ID – the quest you want to duplicate (must exist)

New Quest ID – the quest ID you want to create

Optional fields:

New quest name

New quest summary

New quest reward summary

Leave any of these blank to keep the original text.

Example
Base quest ID to copy FROM (existing ID): 20011
New quest ID to create: 9000001

New quest NAME: My Custom Quest
New quest SUMMARY: Talk to NPC to begin.
New quest REWARD SUMMARY: Adventure begins!

🔧 What the Script Does

For each quest XML file:

Locates the <imgdir name="<QuestID>"> block.

Deep-clones it.

Renames it to the new quest ID.

If editing QuestInfo.img.xml, updates:

name

summary

rewardSummary

Saves the updated XML.

Creates a safety backup:

filename.xml.bak

🔄 After Editing (Client-Side)

Open Quest.wz in HaRepacker.

Right-click → Import XML.

Select the modified XML files.

Save Quest.wz.

Place the updated Quest.wz in your MapleStory client folder.

Your new quest now appears in-game and can be accepted.

⚠️ Important — Step 4 (Server-Side Quest Data!)

If your server does not load the updated quest files,
the new quest will not track kills, rewards, or progress, even if the client shows it correctly.

When cloning quests (e.g., 1037 → 3000):

✔️ Client must contain quest 3000
✔️ Server must ALSO contain quest 3000

This means:

Duplicate the same quest structures on the server side:

Check (kill requirements)

Act (rewards)

Info (QuestInfo)

Your server must load these updated WZ/XML files OR use its own quest data definitions.

Without this step:

The quest will accept but will not track mob kills or complete properly.

🧰 Troubleshooting
❌ "Act.img.xml not found in this folder, skipping."

You ran the script in the wrong directory.
Use the .bat launcher or navigate to the XML folder manually.

❌ New quest not created

Confirm the base quest ID exists. Search inside your XML for:

<imgdir name="1037">

Quest accepts but does not track kills

Your server does not contain the new quest’s mob requirement.
See Step 4 above.

📄 License

MIT License — free to use, modify, and redistribute.
