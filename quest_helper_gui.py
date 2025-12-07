# quest_helper_gui.py (editable meta / requirements / rewards)
import os
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
import xml.etree.ElementTree as ET

import quest_helper  # make sure quest_helper.py is in the same folder

SCRIPT_DIR = quest_helper.get_script_dir()
QUESTINFO_PATH = os.path.join(SCRIPT_DIR, "QuestInfo.img.xml")
CHECK_PATH = os.path.join(SCRIPT_DIR, "Check.img.xml")
ACT_PATH = os.path.join(SCRIPT_DIR, "Act.img.xml")


def load_xml(path):
    """Load an XML file and return (tree, root), or (None, None) if missing."""
    if not os.path.isfile(path):
        return None, None
    tree = ET.parse(path)
    root = tree.getroot()
    return tree, root


def load_questinfo():
    return load_xml(QUESTINFO_PATH)


def get_questinfo_node(root, quest_id: int):
    if root is None:
        return None
    return root.find(f"./imgdir[@name='{quest_id}']")


def get_imgdir(root, quest_id: int):
    if root is None:
        return None
    return root.find(f"./imgdir[@name='{quest_id}']")


def extract_text_from_questinfo(node):
    """Return (name, summary, rewardSummary) from a QuestInfo node."""
    if node is None:
        return ("<not found>", "", "")
    name = ""
    summary = ""
    reward = ""
    for child in node:
        if child.tag != "string":
            continue
        n = child.get("name")
        v = child.get("value", "")
        if n == "name":
            name = v
        elif n in ("summary", "0"):
            if not summary:
                summary = v
        elif n == "rewardSummary":
            reward = v
    return name, summary, reward


def extract_meta_from_questinfo(node):
    meta = dict(
        area=None,
        type=None,
        autoStart=None,
        autoComplete=None,
        parent=None,
        order=None,
        demandSummary=None,
    )
    if node is None:
        return meta

    for child in node:
        tag = child.tag
        name = child.get("name")
        val = child.get("value")
        if tag == "int":
            if name in ("area", "order", "autoStart", "autoComplete"):
                try:
                    v = int(val)
                except (TypeError, ValueError):
                    continue
                if name in ("autoStart", "autoComplete"):
                    meta[name] = bool(v)
                else:
                    meta[name] = v
        elif tag == "string":
            if name in ("type", "parent", "demandSummary"):
                meta[name] = val
    return meta


def apply_meta_to_questinfo(node, meta):
    """Write meta fields into a QuestInfo <imgdir> node."""
    if node is None or meta is None:
        return

    def set_int(name, value):
        if value is None or value == "":
            return
        try:
            v = int(value)
        except ValueError:
            return
        child = node.find(f"./int[@name='{name}']")
        if child is None:
            child = ET.SubElement(node, "int", name=name, value=str(v))
        else:
            child.set("value", str(v))

    def set_bool_as_int(name, value):
        if value is None:
            return
        v = 1 if value else 0
        child = node.find(f"./int[@name='{name}']")
        if child is None:
            child = ET.SubElement(node, "int", name=name, value=str(v))
        else:
            child.set("value", str(v))

    def set_string(name, value):
        if value is None or value == "":
            return
        child = node.find(f"./string[@name='{name}']")
        if child is None:
            child = ET.SubElement(node, "string", name=name, value=value)
        else:
            child.set("value", value)

    set_int("area", meta.get("area"))
    set_int("order", meta.get("order"))
    set_bool_as_int("autoStart", meta.get("autoStart"))
    set_bool_as_int("autoComplete", meta.get("autoComplete"))
    set_string("type", meta.get("type"))
    set_string("parent", meta.get("parent"))
    set_string("demandSummary", meta.get("demandSummary"))


def extract_requirements(root, quest_id: int):
    """Return simple requirement fields + read-only text for other stuff."""
    info = dict(start_npc=None, end_npc=None, lvmin=None,
                items_text="", mobs_text="", quests_text="")
    node = get_imgdir(root, quest_id)
    if node is None:
        return info

    items_lines = []
    mobs_lines = []
    quest_lines = []

    for stage in node.findall("./imgdir"):
        stage_name = stage.get("name")
        for child in stage:
            if child.tag == "int":
                name = child.get("name")
                try:
                    val = int(child.get("value"))
                except (TypeError, ValueError):
                    continue
                if name == "npc":
                    if stage_name == "0":
                        info["start_npc"] = val
                    elif stage_name == "1":
                        info["end_npc"] = val
                elif name == "lvmin":
                    info["lvmin"] = val
            elif child.tag == "imgdir":
                cname = child.get("name")
                if cname == "item":
                    for itemdir in child.findall("./imgdir"):
                        item_id = None
                        count = 1
                        for i in itemdir.findall("./int"):
                            nm = i.get("name")
                            try:
                                v = int(i.get("value"))
                            except (TypeError, ValueError):
                                continue
                            if nm == "id":
                                item_id = v
                            elif nm == "count":
                                count = v
                        if item_id is not None:
                            items_lines.append(f"Item {item_id} x{count}")
                elif cname == "mob":
                    for mobdir in child.findall("./imgdir"):
                        mob_id = None
                        count = 1
                        for i in mobdir.findall("./int"):
                            nm = i.get("name")
                            try:
                                v = int(i.get("value"))
                            except (TypeError, ValueError):
                                continue
                            if nm == "id":
                                mob_id = v
                            elif nm == "count":
                                count = v
                        if mob_id is not None:
                            mobs_lines.append(f"Mob {mob_id} x{count}")
                elif cname == "quest":
                    for qdir in child.findall("./imgdir"):
                        q_id = None
                        state = None
                        for i in qdir.findall("./int"):
                            nm = i.get("name")
                            try:
                                v = int(i.get("value"))
                            except (TypeError, ValueError):
                                continue
                            if nm == "id":
                                q_id = v
                            elif nm == "state":
                                state = v
                        if q_id is not None:
                            quest_lines.append(f"Quest {q_id} (state {state})")

    info["items_text"] = "\n".join(items_lines)
    info["mobs_text"] = "\n".join(mobs_lines)
    info["quests_text"] = "\n".join(quest_lines)
    return info


def apply_requirements(root, quest_id: int, req):
    """Write simple requirement fields back to Check.img tree."""
    if root is None or req is None:
        return
    node = get_imgdir(root, quest_id)
    if node is None:
        return

    def ensure_stage(stage_name):
        st = node.find(f"./imgdir[@name='{stage_name}']")
        if st is None:
            st = ET.SubElement(node, "imgdir", name=stage_name)
        return st

    def set_int(stage, name, value):
        if value is None or value == "":
            return
        try:
            v = int(value)
        except ValueError:
            return
        child = stage.find(f"./int[@name='{name}']")
        if child is None:
            child = ET.SubElement(stage, "int", name=name, value=str(v))
        else:
            child.set("value", str(v))

    s0 = ensure_stage("0")
    s1 = ensure_stage("1")

    set_int(s0, "npc", req.get("start_npc"))
    set_int(s0, "lvmin", req.get("lvmin"))
    set_int(s1, "npc", req.get("end_npc"))


def extract_rewards(root, quest_id: int):
    """Return exp + text summaries for item changes."""
    info = dict(exp=None, items_gain_text="", items_lose_text="")
    node = get_imgdir(root, quest_id)
    if node is None:
        return info

    items_gain = []
    items_lose = []

    for stage in node.findall("./imgdir"):
        for child in stage:
            if child.tag == "int" and child.get("name") == "exp":
                try:
                    info["exp"] = int(child.get("value"))
                except (TypeError, ValueError):
                    pass
            elif child.tag == "imgdir" and child.get("name") == "item":
                for itemdir in child.findall("./imgdir"):
                    item_id = None
                    count = None
                    for i in itemdir.findall("./int"):
                        nm = i.get("name")
                        try:
                            v = int(i.get("value"))
                        except (TypeError, ValueError):
                            continue
                        if nm == "id":
                            item_id = v
                        elif nm == "count":
                            count = v
                    if item_id is not None and count is not None:
                        if count >= 0:
                            items_gain.append((item_id, count))
                        else:
                            items_lose.append((item_id, -count))

    info["items_gain_text"] = "\n".join(f"Item {i} x{c}" for i, c in items_gain)
    info["items_lose_text"] = "\n".join(f"Item {i} x{c}" for i, c in items_lose)
    return info


def apply_rewards(root, quest_id: int, rewards):
    """Write EXP back to Act.img tree (items stay as-is)."""
    if root is None or rewards is None:
        return
    node = get_imgdir(root, quest_id)
    if node is None:
        return

    exp_val = rewards.get("exp")
    if exp_val is None or exp_val == "":
        return

    try:
        exp_int = int(exp_val)
    except ValueError:
        return

    # Find an existing exp field, or create one on stage 1 / 0.
    target_int = None
    for stage in node.findall("./imgdir"):
        for child in stage.findall("./int"):
            if child.get("name") == "exp":
                target_int = child
                break
        if target_int is not None:
            break

    if target_int is not None:
        target_int.set("value", str(exp_int))
    else:
        stage = node.find("./imgdir[@name='1']") or node.find("./imgdir[@name='0']")
        if stage is None:
            stage = ET.SubElement(node, "imgdir", name="0")
        ET.SubElement(stage, "int", name="exp", value=str(exp_int))


class QuestHelperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Maple Quest Helper - GUI")

        # Load XMLs
        try:
            self.qtree, self.qroot = load_questinfo()
            if self.qroot is None:
                raise FileNotFoundError("QuestInfo.img.xml not found.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load QuestInfo.img.xml:\n{e}")
            self.qtree, self.qroot = None, None

        self.check_tree, self.check_root = load_xml(CHECK_PATH)
        self.act_tree, self.act_root = load_xml(ACT_PATH)

        self.create_widgets()
        if self.qroot is not None:
            self.populate_listbox()

    # ----------------------- UI creation -----------------------

    def create_widgets(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill="both", expand=True)

        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=3)
        main.rowconfigure(1, weight=1)
        main.rowconfigure(2, weight=1)

        # Left: quest list
        left = ttk.Frame(main)
        left.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=(0, 10))
        left.rowconfigure(1, weight=1)

        ttk.Label(left, text="Quests in QuestInfo.img.xml").grid(row=0, column=0, sticky="w")
        self.quest_list = tk.Listbox(left, width=30, height=30)
        self.quest_list.grid(row=1, column=0, sticky="nsew")
        self.quest_list.bind("<<ListboxSelect>>", self.on_list_select)

        # Top-right: IDs + buttons
        top = ttk.Frame(main)
        top.grid(row=0, column=1, sticky="we", pady=(0, 5))
        for i in range(6):
            top.columnconfigure(i, weight=0)
        top.columnconfigure(3, weight=1)

        ttk.Label(top, text="Base ID:").grid(row=0, column=0, sticky="e")
        self.base_id_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.base_id_var, width=8).grid(row=0, column=1, sticky="w", padx=(3, 10))

        ttk.Label(top, text="New ID:").grid(row=0, column=2, sticky="e")
        self.new_id_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.new_id_var, width=8).grid(row=0, column=3, sticky="w", padx=(3, 10))

        ttk.Button(top, text="Preview IDs", command=self.preview_ids).grid(row=0, column=4, padx=(5, 0))
        ttk.Button(top, text="Clone / Save", command=self.clone_quest).grid(row=0, column=5, padx=(5, 0))

        # Middle-right: base vs new text
        mid = ttk.Frame(main)
        mid.grid(row=1, column=1, sticky="nsew")
        mid.columnconfigure(0, weight=1)
        mid.columnconfigure(1, weight=1)

        # Base
        base_frame = ttk.LabelFrame(mid, text="Base Quest (source)")
        base_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        for i in range(6):
            base_frame.rowconfigure(i, weight=0)
        base_frame.rowconfigure(3, weight=1)

        ttk.Label(base_frame, text="Name:").grid(row=0, column=0, sticky="w")
        self.base_name = tk.Text(base_frame, height=2, wrap="word")
        self.base_name.grid(row=1, column=0, sticky="nwe", pady=(0, 5))

        ttk.Label(base_frame, text="Summary:").grid(row=2, column=0, sticky="w")
        self.base_summary = tk.Text(base_frame, height=5, wrap="word")
        self.base_summary.grid(row=3, column=0, sticky="nsew", pady=(0, 5))

        ttk.Label(base_frame, text="Reward Summary:").grid(row=4, column=0, sticky="w")
        self.base_reward = tk.Text(base_frame, height=3, wrap="word")
        self.base_reward.grid(row=5, column=0, sticky="nwe")

        # New (editable)
        new_frame = ttk.LabelFrame(mid, text="New Quest (target, editable)")
        new_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        for i in range(6):
            new_frame.rowconfigure(i, weight=0)
        new_frame.rowconfigure(3, weight=1)

        ttk.Label(new_frame, text="Name:").grid(row=0, column=0, sticky="w")
        self.new_name_var = tk.StringVar()
        self.new_name_entry = ttk.Entry(new_frame, textvariable=self.new_name_var)
        self.new_name_entry.grid(row=1, column=0, sticky="we", pady=(0, 5))

        ttk.Label(new_frame, text="Summary:").grid(row=2, column=0, sticky="w")
        self.new_summary = tk.Text(new_frame, height=5, wrap="word")
        self.new_summary.grid(row=3, column=0, sticky="nsew", pady=(0, 5))

        ttk.Label(new_frame, text="Reward Summary:").grid(row=4, column=0, sticky="w")
        self.new_reward = tk.Text(new_frame, height=3, wrap="word")
        self.new_reward.grid(row=5, column=0, sticky="nwe")

        # Bottom-right: Meta / Requirements / Rewards for NEW quest (editable)
        bottom = ttk.Frame(main)
        bottom.grid(row=2, column=1, sticky="nsew", pady=(5, 0))
        bottom.rowconfigure(0, weight=1)
        bottom.columnconfigure(0, weight=1)

        self.info_notebook = ttk.Notebook(bottom)
        self.info_notebook.grid(row=0, column=0, sticky="nsew")

        # Meta tab
        meta_tab = ttk.Frame(self.info_notebook)
        meta_tab.columnconfigure(1, weight=1)

        ttk.Label(meta_tab, text="Type:").grid(row=0, column=0, sticky="e")
        self.meta_type_var = tk.StringVar()
        ttk.Entry(meta_tab, textvariable=self.meta_type_var).grid(row=0, column=1, sticky="we", padx=3, pady=2)

        ttk.Label(meta_tab, text="Area:").grid(row=1, column=0, sticky="e")
        self.meta_area_var = tk.StringVar()
        ttk.Entry(meta_tab, textvariable=self.meta_area_var, width=8).grid(row=1, column=1, sticky="w", padx=3, pady=2)

        ttk.Label(meta_tab, text="Parent:").grid(row=2, column=0, sticky="e")
        self.meta_parent_var = tk.StringVar()
        ttk.Entry(meta_tab, textvariable=self.meta_parent_var).grid(row=2, column=1, sticky="we", padx=3, pady=2)

        ttk.Label(meta_tab, text="Order:").grid(row=3, column=0, sticky="e")
        self.meta_order_var = tk.StringVar()
        ttk.Entry(meta_tab, textvariable=self.meta_order_var, width=8).grid(row=3, column=1, sticky="w", padx=3, pady=2)

        self.meta_auto_start_var = tk.BooleanVar(value=False)
        self.meta_auto_complete_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(meta_tab, text="Auto Start", variable=self.meta_auto_start_var).grid(row=4, column=0, sticky="w", padx=3, pady=2)
        ttk.Checkbutton(meta_tab, text="Auto Complete", variable=self.meta_auto_complete_var).grid(row=4, column=1, sticky="w", padx=3, pady=2)

        ttk.Label(meta_tab, text="Demand Summary:").grid(row=5, column=0, sticky="ne", pady=(4, 0))
        self.meta_demand = tk.Text(meta_tab, height=4, wrap="word")
        self.meta_demand.grid(row=5, column=1, sticky="nsew", padx=3, pady=(4, 0))

        meta_tab.rowconfigure(5, weight=1)

        # Requirements tab
        req_tab = ttk.Frame(self.info_notebook)
        req_tab.columnconfigure(1, weight=1)
        req_tab.rowconfigure(4, weight=1)

        ttk.Label(req_tab, text="Start NPC (stage 0):").grid(row=0, column=0, sticky="e")
        self.req_start_npc_var = tk.StringVar()
        ttk.Entry(req_tab, textvariable=self.req_start_npc_var, width=10).grid(row=0, column=1, sticky="w", padx=3, pady=2)

        ttk.Label(req_tab, text="End NPC (stage 1):").grid(row=1, column=0, sticky="e")
        self.req_end_npc_var = tk.StringVar()
        ttk.Entry(req_tab, textvariable=self.req_end_npc_var, width=10).grid(row=1, column=1, sticky="w", padx=3, pady=2)

        ttk.Label(req_tab, text="Min Level:").grid(row=2, column=0, sticky="e")
        self.req_lvmin_var = tk.StringVar()
        ttk.Entry(req_tab, textvariable=self.req_lvmin_var, width=10).grid(row=2, column=1, sticky="w", padx=3, pady=2)

        ttk.Label(req_tab, text="Other Requirements (read-only):").grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))
        self.req_other = tk.Text(req_tab, height=6, wrap="word")
        self.req_other.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=3, pady=(0, 0))
        self.req_other.config(state="disabled")

        # Rewards tab
        rew_tab = ttk.Frame(self.info_notebook)
        rew_tab.columnconfigure(1, weight=1)
        rew_tab.rowconfigure(3, weight=1)

        ttk.Label(rew_tab, text="EXP Reward:").grid(row=0, column=0, sticky="e")
        self.rew_exp_var = tk.StringVar()
        ttk.Entry(rew_tab, textvariable=self.rew_exp_var, width=10).grid(row=0, column=1, sticky="w", padx=3, pady=2)

        ttk.Label(rew_tab, text="Items gained (read-only):").grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))
        self.rew_items_gain = tk.Text(rew_tab, height=4, wrap="word")
        self.rew_items_gain.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=3, pady=(0, 0))
        self.rew_items_gain.config(state="disabled")

        ttk.Label(rew_tab, text="Items consumed (read-only):").grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))
        self.rew_items_lose = tk.Text(rew_tab, height=3, wrap="word")
        self.rew_items_lose.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=3, pady=(0, 0))
        self.rew_items_lose.config(state="disabled")

        self.info_notebook.add(meta_tab, text="Meta")
        self.info_notebook.add(req_tab, text="Requirements")
        self.info_notebook.add(rew_tab, text="Rewards")

    # ----------------------- helpers -----------------------

    def populate_listbox(self):
        self.quest_list.delete(0, tk.END)
        if self.qroot is None:
            return
        for imgdir in self.qroot.findall("./imgdir"):
            qid = imgdir.get("name")
            name, _, _ = extract_text_from_questinfo(imgdir)
            display = f"{qid}: {name}"
            self.quest_list.insert(tk.END, display)

    def on_list_select(self, event):
        if not self.quest_list.curselection():
            return
        idx = self.quest_list.curselection()[0]
        line = self.quest_list.get(idx)
        qid = line.split(":", 1)[0].strip()
        self.base_id_var.set(qid)
        if not self.new_id_var.get().strip():
            self.new_id_var.set(qid)
        self.preview_ids()

    def _set_readonly_text(self, widget, text):
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", text)
        widget.config(state="disabled")

    def preview_ids(self):
        if self.qroot is None:
            return

        base_id_str = self.base_id_var.get().strip()
        new_id_str = self.new_id_var.get().strip() or base_id_str

        if not base_id_str.isdigit() or not new_id_str.isdigit():
            messagebox.showwarning("Invalid IDs", "Base ID and New ID must be numbers.")
            return

        base_id = int(base_id_str)
        new_id = int(new_id_str)

        # Base quest text (read-only)
        base_node = get_questinfo_node(self.qroot, base_id)
        bname, bsum, brew = extract_text_from_questinfo(base_node)
        self._set_readonly_text(self.base_name, bname)
        self._set_readonly_text(self.base_summary, bsum)
        self._set_readonly_text(self.base_reward, brew)

        # New quest text (editable) – if target exists, load that, else copy base
        new_node = get_questinfo_node(self.qroot, new_id)
        if new_node is not None:
            nname, nsum, nrew = extract_text_from_questinfo(new_node)
        else:
            nname, nsum, nrew = bname, bsum, brew

        self.new_name_var.set(nname)
        self.new_summary.delete("1.0", tk.END)
        self.new_summary.insert("1.0", nsum)
        self.new_reward.delete("1.0", tk.END)
        self.new_reward.insert("1.0", nrew)

        # Meta / Requirements / Rewards for NEW quest (default from new if exists, else base)
        meta_node = get_questinfo_node(self.qroot, new_id) or base_node
        meta = extract_meta_from_questinfo(meta_node)

        self.meta_type_var.set(meta.get("type") or "")
        self.meta_area_var.set("" if meta.get("area") is None else str(meta.get("area")))
        self.meta_parent_var.set(meta.get("parent") or "")
        self.meta_order_var.set("" if meta.get("order") is None else str(meta.get("order")))
        self.meta_auto_start_var.set(bool(meta.get("autoStart")) if meta.get("autoStart") is not None else False)
        self.meta_auto_complete_var.set(bool(meta.get("autoComplete")) if meta.get("autoComplete") is not None else False)
        self.meta_demand.delete("1.0", tk.END)
        if meta.get("demandSummary"):
            self.meta_demand.insert("1.0", meta["demandSummary"])

        # Requirements (Check.img)
        req_source_id = new_id if get_imgdir(self.check_root, new_id) is not None else base_id
        req = extract_requirements(self.check_root, req_source_id)
        self.req_start_npc_var.set("" if req["start_npc"] is None else str(req["start_npc"]))
        self.req_end_npc_var.set("" if req["end_npc"] is None else str(req["end_npc"]))
        self.req_lvmin_var.set("" if req["lvmin"] is None else str(req["lvmin"]))

        other_lines = []
        if req["items_text"]:
            other_lines.append("Items:")
            other_lines.append(req["items_text"])
        if req["mobs_text"]:
            if other_lines:
                other_lines.append("")
            other_lines.append("Mobs:")
            other_lines.append(req["mobs_text"])
        if req["quests_text"]:
            if other_lines:
                other_lines.append("")
            other_lines.append("Prerequisite quests:")
            other_lines.append(req["quests_text"])
        other_text = "\n".join(other_lines) if other_lines else "No other requirements."
        self._set_readonly_text(self.req_other, other_text)

        # Rewards (Act.img)
        rew_source_id = new_id if get_imgdir(self.act_root, new_id) is not None else base_id
        rew = extract_rewards(self.act_root, rew_source_id)
        self.rew_exp_var.set("" if rew["exp"] is None else str(rew["exp"]))
        self._set_readonly_text(self.rew_items_gain, rew["items_gain_text"] or "No item gains.")
        self._set_readonly_text(self.rew_items_lose, rew["items_lose_text"] or "No item consumption.")

    def _collect_meta_from_ui(self):
        return dict(
            type=self.meta_type_var.get().strip() or None,
            area=self.meta_area_var.get().strip() or None,
            parent=self.meta_parent_var.get().strip() or None,
            order=self.meta_order_var.get().strip() or None,
            autoStart=self.meta_auto_start_var.get(),
            autoComplete=self.meta_auto_complete_var.get(),
            demandSummary=self.meta_demand.get("1.0", tk.END).strip() or None,
        )

    def _collect_requirements_from_ui(self):
        return dict(
            start_npc=self.req_start_npc_var.get().strip() or None,
            end_npc=self.req_end_npc_var.get().strip() or None,
            lvmin=self.req_lvmin_var.get().strip() or None,
        )

    def _collect_rewards_from_ui(self):
        return dict(
            exp=self.rew_exp_var.get().strip() or None,
        )

    def clone_quest(self):
        """Clone from base -> new and apply all editable fields."""
        base_id_str = self.base_id_var.get().strip()
        new_id_str = self.new_id_var.get().strip()

        if not base_id_str.isdigit() or not new_id_str.isdigit():
            messagebox.showwarning("Invalid IDs", "Base ID and New ID must be numbers.")
            return

        base_id = int(base_id_str)
        new_id = int(new_id_str)

        new_name = self.new_name_var.get().strip()
        new_summary = self.new_summary.get("1.0", tk.END).strip()
        new_reward = self.new_reward.get("1.0", tk.END).strip()

        meta = self._collect_meta_from_ui()
        req = self._collect_requirements_from_ui()
        rew = self._collect_rewards_from_ui()

        messages = []

        for fname in quest_helper.FILES:
            path = os.path.join(SCRIPT_DIR, fname)
            if not os.path.isfile(path):
                messages.append(f"[INFO] {fname} not found, skipping.")
                continue

            backup_path = path + ".bak"
            shutil.copy2(path, backup_path)

            tree = ET.parse(path)
            root = tree.getroot()

            new_node = None
            msg = ""
            if hasattr(quest_helper, "clone_node"):
                new_node, msg = quest_helper.clone_node(root, base_id, new_id)
                if msg:
                    messages.append(f"{fname}: {msg}")
            else:
                messages.append(f"{fname}: clone_node not found in quest_helper; only editing existing quest.")

            # QuestInfo: always update text + meta on the new quest node if it exists
            if fname == "QuestInfo.img.xml":
                if new_node is None:
                    new_node = get_questinfo_node(root, new_id)
                if new_node is not None:
                    if hasattr(quest_helper, "update_questinfo_text"):
                        quest_helper.update_questinfo_text(new_node, new_name, new_summary, new_reward)
                        messages.append("    QuestInfo text updated.")
                    apply_meta_to_questinfo(new_node, meta)
                    messages.append("    QuestInfo meta updated.")

            # Check: update simple requirements for new quest ID
            if fname == "Check.img.xml":
                apply_requirements(root, new_id, req)
                messages.append("    Check requirements updated (npc / lvmin).")

            # Act: update EXP for new quest ID
            if fname == "Act.img.xml":
                apply_rewards(root, new_id, rew)
                messages.append("    Act rewards updated (EXP).")

            tree.write(path, encoding="utf-8", xml_declaration=True)

        # Reload XMLs and refresh UI
        try:
            self.qtree, self.qroot = load_questinfo()
            self.check_tree, self.check_root = load_xml(CHECK_PATH)
            self.act_tree, self.act_root = load_xml(ACT_PATH)
            self.populate_listbox()
            self.preview_ids()
        except Exception:
            pass

        messagebox.showinfo("Clone / Save complete", "\n".join(messages))


if __name__ == "__main__":
    root = tk.Tk()
    app = QuestHelperGUI(root)
    root.mainloop()
