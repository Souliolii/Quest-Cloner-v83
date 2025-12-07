# quest_helper.py
import os
import shutil
import xml.etree.ElementTree as ET

FILES = [
    "Act.img.xml",
    "Check.img.xml",
    "Exclusive.img.xml",
    "PQuest.img.xml",
    "QuestInfo.img.xml",
    "Say.img.xml",
]

def get_script_dir() -> str:
    # Folder where this .py file lives
    return os.path.dirname(os.path.abspath(__file__))

def clone_node(root, base_id, new_id):
    # <imgdir name="QuestInfo.img"> -> <imgdir name="1000"> stuff
    xpath = f"./imgdir[@name='{base_id}']"
    base = root.find(xpath)
    if base is None:
        return None, f"[WARN] Base ID {base_id} not found."
    # Check if target already exists
    existing = root.find(f"./imgdir[@name='{new_id}']")
    if existing is not None:
        return None, f"[WARN] Target ID {new_id} already exists, skipping."

    # Deep copy
    new = ET.fromstring(ET.tostring(base))
    new.set("name", str(new_id))
    root.append(new)
    return new, "[OK] Cloned."

def update_questinfo_text(node, new_name, new_summary, new_reward):
    if node is None:
        return
    for child in node:
        if child.tag != "string":
            continue
        n = child.get("name")
        if n == "name" and new_name:
            child.set("value", new_name)
        if n in ("summary", "0") and new_summary:
            child.set("value", new_summary)
        if n == "rewardSummary" and new_reward:
            child.set("value", new_reward)

def main():
    script_dir = get_script_dir()
    os.chdir(script_dir)  # <-- THIS fixes the System32 problem

    print("=== Maple Quest Helper ===")
    print(f"Working folder: {script_dir}")
    print("Make sure this script and all *.img.xml files are together.\n")

    base_id = input("Base quest ID to copy FROM (existing ID): ").strip()
    new_id = input("New quest ID to create: ").strip()

    if not base_id.isdigit() or not new_id.isdigit():
        print("Base ID and New ID must be numbers.")
        input("Press Enter to exit...")
        return

    base_id = int(base_id)
    new_id = int(new_id)

    print("\nNow enter any new text you want for QuestInfo.img.xml.")
    print("Leave blank to keep the original text from the base quest.\n")

    new_name = input("New quest NAME (blank = keep original): ").strip()
    new_summary = input("New quest SUMMARY (blank = keep original): ").strip()
    new_reward = input("New quest REWARD SUMMARY (blank = keep original): ").strip()

    print("\nCloning quest:")
    print(f"  Base ID: {base_id}")
    print(f"  New  ID: {new_id}\n")

    for fname in FILES:
        path = os.path.join(script_dir, fname)
        if not os.path.isfile(path):
            print(f"[INFO] {fname} not found here, skipping.")
            continue

        print(f"[INFO] Processing {fname} ...")
        # Backup
        backup_path = path + ".bak"
        shutil.copy2(path, backup_path)

        tree = ET.parse(path)
        root = tree.getroot()

        new_node, msg = clone_node(root, base_id, new_id)
        print("       ", msg)

        # Only tweak text inside QuestInfo
        if fname == "QuestInfo.img.xml" and new_node is not None:
            update_questinfo_text(new_node, new_name, new_summary, new_reward)
            print("        [OK] Updated QuestInfo text for new quest.")

        # Write back
        tree.write(path, encoding="utf-8", xml_declaration=True)

    print("\nDone. If something broke, restore the *.bak files.")
    input("Press Enter to close...")

if __name__ == "__main__":
    main()
