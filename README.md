# Quest-Cloner v83 — AdventureMS
### MapleStory Quest XML Cloner & Professional GUI Editor

A modern, fully graphical tool for cloning, editing, and managing MapleStory quests using Classic XML exports (Act.img.xml, Check.img.xml, QuestInfo.img.xml, etc.).

This project replaces manual XML editing and HaRepacker copy‑paste with a clean, automated workflow.

---

# 🚀 Recommended: Use the EXE Release
Most users **do NOT need Python anymore**.

Download the latest release EXE, place it in the same folder as your exported `.img.xml` files, and run it.  
The EXE automatically detects its working directory and loads/saves XML files correctly.

Python scripts are included only for developers who want to modify the tool.

---

# ✨ Features

### 🔍 Quest Browser + Search
- Search quests in **QuestInfo.img.xml** by ID or name  
- Instant filtered results  
- Click any quest to load it into the Base Quest panel  
- View full structured data: text, logs, requirements, rewards  

### 📚 Quest Cloning
- Clone any quest ID to a new custom quest ID
- Automatically updates:
  - `name`
  - `summary`
  - `rewardSummary`
- Copies all logs, requirements, and rewards
- Fully editable before saving
- Prevents invalid or accidental overwrites

### 📝 Quest Editing (GUI)
- Edit all QuestInfo fields  
- Edit requirements from Check.img:
  - Start NPC
  - End NPC
  - Level minimum  
  - Required items  
  - Required mobs  
  - Required prerequisite quests  
- Edit Act.img rewards:
  - EXP
  - Items gained
  - Items consumed  
- **Automatic reward correction**  
  Ensures EXP/items are placed in stage `1` (completion)  
  and never incorrectly inside stage `0`.

### 🗑 Quest Deletion
- Delete a quest by:
  - Selecting it in the left quest list, OR  
  - Typing the ID manually  
- Deletes across all XML files
- Creates `.bak` backups automatically

### 🎨 GUI Features
- Dark theme  
- Fully scrollable editor  
- 3‑column structured layout  
- Copy Base → New button  
- Clear New Quest Form button  
- No auto-fill of New ID (prevents mistakes)

---

# 📁 Required Files

These must be exported from **HaRepacker**:

```
Act.img.xml
Check.img.xml
Exclusive.img.xml
PQuest.img.xml
QuestInfo.img.xml
Say.img.xml
```

Export using:

**File → Export → Classic XML**

Place the EXE or Python scripts in the same folder as these XMLs.

---

# ⚙️ Running the Tool

## ✅ GUI / EXE Version (Recommended)
Just double‑click:

```
quest_helper_gui.exe
```

The EXE must be in the same folder as your `.img.xml` files.

No Python required.

---

## 🐍 Python Version (Developer Use Only)

### Run:
```
python quest_helper_gui.py
```

or command-line version:

```
python quest_helper.py
```

---

# 🧠 Usage Overview

1. Select a base quest in the left search panel  
2. Enter a **New Quest ID**  
3. (Optional) Edit fields you want to change  
4. Press **Clone / Save**  
5. The tool updates all relevant XML files and creates backups  

To delete a quest:  
- Select it in the left list → click **Delete Quest**

---

# 🔄 How It Works (Internals)

For each XML file, the tool:

1. Locates `<imgdir name="BaseID">`
2. Deep‑clones it
3. Renames clone to `<imgdir name="NewID">`
4. Applies overrides from UI (QuestInfo, requirements, rewards)
5. Writes back to file
6. Creates a `.bak` backup before modifying

---

# 🔧 Reimporting Into MapleStory Client

1. Open **Quest.wz** in HaRepacker  
2. Import XML:
   - Act.img.xml  
   - Check.img.xml  
   - QuestInfo.img.xml  
   - Exclusive.img.xml  
   - PQuest.img.xml  
   - Say.img.xml  
3. Save Quest.wz  
4. Replace your client’s Quest.wz with the new one

Your custom quest now exists in-game.

---

# 🖥 Server-Side Requirements

The **server must also contain** the same quest ID.

If your client has:

```
3000
```

Your server must also define:

- Check data  
- Act rewards  
- Info text  

Otherwise quests will:
- Not track kills  
- Not give rewards  
- Not complete properly  

---

# ❗ Troubleshooting

### ⚠️ “Act.img.xml not found”
You ran the EXE in the wrong folder.  
Place it next to your `.img.xml` files.

### ⚠️ “QuestInfo.img.xml not found”
You placed the EXE in a folder with `.img` files, not `.img.xml` files.

### ⚠️ Quest does not give rewards
Server-side Act data for the new quest ID is missing.

### ⚠️ Quest does not track kills
Server-side Check data for the quest is missing.

### ⚠️ The quest does not appear
The base quest ID you tried to clone does not exist.  
Search for its `<imgdir name="ID">` in QuestInfo.img.xml.

---

# 📜 License
MIT License  
Use freely in private or commercial MapleStory servers.

