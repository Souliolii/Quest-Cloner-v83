import os
import sys
import shutil
import copy
import tkinter as tk
from tkinter import ttk, messagebox
import xml.etree.ElementTree as ET
import re

# Files we operate on
FILES = [
    "Act.img.xml",
    "Check.img.xml",
    "Exclusive.img.xml",
    "PQuest.img.xml",
    "QuestInfo.img.xml",
    "Say.img.xml",
]

# When frozen as an EXE, use the folder of the executable.
# When running as a .py, use the folder of this script.
if getattr(sys, "frozen", False):
    # PyInstaller onefile EXE
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------- Dark theme ----------

DARK_BG = "#1e1e1e"
DARK_FG = "#ffffff"
DARK_ACCENT = "#2d2d2d"
DARK_ENTRY = "#2b2b2b"
DARK_TEXT_BG = "#252525"
DARK_TEXT_FG = "#e6e6e6"
DARK_HIGHLIGHT = "#3a3a3a"
BTN_BG = "#3c3c3c"
BTN_FG = "#ffffff"


def apply_dark_theme(root):
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(
        ".",
        background=DARK_BG,
        foreground=DARK_FG,
        fieldbackground=DARK_ENTRY,
        bordercolor=DARK_HIGHLIGHT,
        lightcolor=DARK_BG,
        darkcolor=DARK_BG,
        troughcolor=DARK_ACCENT,
        padding=2,
    )
    style.configure(
        "TButton",
        background=BTN_BG,
        foreground=BTN_FG,
        borderwidth=1,
        focusthickness=3,
        focuscolor=DARK_HIGHLIGHT,
    )
    style.map(
        "TButton",
        background=[("active", DARK_HIGHLIGHT)],
        foreground=[("active", "white")],
    )
    style.configure(
        "TEntry",
        fieldbackground=DARK_ENTRY,
        foreground=DARK_FG,
        insertcolor=DARK_FG,
        borderwidth=1,
    )
    style.configure(
        "TLabelframe",
        background=DARK_ACCENT,
        foreground=DARK_FG,
        borderwidth=1,
    )
    style.configure(
        "TLabelframe.Label",
        background=DARK_ACCENT,
        foreground=DARK_FG,
    )
    root.option_add("*Listbox*Background", DARK_ENTRY)
    root.option_add("*Listbox*Foreground", DARK_FG)
    root.option_add("*Listbox*SelectBackground", DARK_HIGHLIGHT)
    root.option_add("*Listbox*SelectForeground", DARK_FG)
    root.option_add("*Text*Background", DARK_TEXT_BG)
    root.option_add("*Text*Foreground", DARK_TEXT_FG)
    root.option_add("*Text*InsertBackground", DARK_FG)
    root.configure(background=DARK_BG)


# ---------- XML helpers ----------

def load_xml(path):
    if not os.path.isfile(path):
        return None, None
    tree = ET.parse(path)
    return tree, tree.getroot()


def get_imgdir(root, quest_id: int):
    if root is None:
        return None
    return root.find(f"./imgdir[@name='{quest_id}']")


def clone_node(root, base_id: int, new_id: int):
    """Clone <imgdir name=base_id> to new_id in given root.
       If base_id == new_id, just return existing node.
    """
    if root is None:
        return None, "Root is None"
    base = get_imgdir(root, base_id)
    if base is None:
        return None, f"Base quest {base_id} not found."
    if base_id == new_id:
        node = get_imgdir(root, new_id)
        if node is None:
            node = copy.deepcopy(base)
            node.set("name", str(new_id))
            root.append(node)
            return node, f"Created quest {new_id} from {base_id}."
        return node, f"Editing quest {new_id} (no clone)."
    existing = get_imgdir(root, new_id)
    if existing is not None:
        root.remove(existing)
    node = copy.deepcopy(base)
    node.set("name", str(new_id))
    root.append(node)
    return node, f"Cloned {base_id} -> {new_id}."


# ---------- QuestInfo (text + meta + logs) ----------

def extract_questinfo(root, quest_id: int):
    node = get_imgdir(root, quest_id)
    data = {
        "name": "",
        "type": "",
        "area": None,
        "parent": "",
        "order": None,
        "autoStart": None,
        "autoComplete": None,
        "log0": "",
        "log1": "",
        "log2": "",
        "summary": "",
        "rewardSummary": "",
        "demandSummary": "",
    }
    if node is None:
        return data
    for child in node:
        tag = child.tag
        name = child.get("name")
        val = child.get("value", "")
        if tag == "string":
            if name == "name":
                data["name"] = val
            elif name == "type":
                data["type"] = val
            elif name == "parent":
                data["parent"] = val
            elif name == "demandSummary":
                data["demandSummary"] = val
            elif name == "0":
                data["log0"] = val
            elif name == "1":
                data["log1"] = val
            elif name == "2":
                data["log2"] = val
            elif name == "summary":
                data["summary"] = val
            elif name == "rewardSummary":
                data["rewardSummary"] = val
        elif tag == "int":
            try:
                iv = int(val)
            except ValueError:
                continue
            if name == "area":
                data["area"] = iv
            elif name == "order":
                data["order"] = iv
            elif name == "autoStart":
                data["autoStart"] = bool(iv)
            elif name == "autoComplete":
                data["autoComplete"] = bool(iv)
    if not data["summary"] and data["log0"]:
        data["summary"] = data["log0"]
    return data


def _set_string(node, name, value):
    child = node.find(f"./string[@name='{name}']")
    if child is None:
        child = ET.SubElement(node, "string", name=name, value=value)
    else:
        child.set("value", value)


def _set_int(node, name, value):
    child = node.find(f"./int[@name='{name}']")
    if child is None:
        child = ET.SubElement(node, "int", name=name, value=str(value))
    else:
        child.set("value", str(value))


def apply_questinfo(root, quest_id: int, data: dict):
    node = get_imgdir(root, quest_id)
    if node is None:
        node = ET.SubElement(root, "imgdir", name=str(quest_id))
    _set_string(node, "name", data.get("name", ""))
    _set_string(node, "type", data.get("type", ""))
    _set_string(node, "parent", data.get("parent", ""))
    _set_string(node, "demandSummary", data.get("demandSummary", ""))
    _set_string(node, "0", data.get("log0", ""))
    _set_string(node, "1", data.get("log1", ""))
    _set_string(node, "2", data.get("log2", ""))
    _set_string(node, "summary", data.get("summary", ""))
    _set_string(node, "rewardSummary", data.get("rewardSummary", ""))

    area = data.get("area")
    if isinstance(area, str):
        area = area.strip() or None
    if area not in (None, ""):
        try:
            _set_int(node, "area", int(area))
        except ValueError:
            pass

    order = data.get("order")
    if isinstance(order, str):
        order = order.strip() or None
    if order not in (None, ""):
        try:
            _set_int(node, "order", int(order))
        except ValueError:
            pass

    autoStart = data.get("autoStart")
    if autoStart is not None:
        _set_int(node, "autoStart", 1 if autoStart else 0)
    autoComplete = data.get("autoComplete")
    if autoComplete is not None:
        _set_int(node, "autoComplete", 1 if autoComplete else 0)


# ---------- Requirements (Check.img) ----------

def _parse_id_count_lines(text):
    pairs = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        line = line.replace("x", " ").replace("X", " ")
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            id_ = int(parts[0])
            count = int(parts[1])
        except ValueError:
            continue
        pairs.append((id_, count))
    return pairs


def _parse_id_state_lines(text):
    pairs = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            id_ = int(parts[0])
            st = int(parts[1])
        except ValueError:
            continue
        pairs.append((id_, st))
    return pairs


def validate_id_count_lines(text: str):
    """Return list of (line_no, line_text) that are invalid for id/count."""
    errors = []
    for i, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        line2 = line.replace("x", " ").replace("X", " ")
        parts = line2.split()
        if len(parts) < 2:
            errors.append((i, raw))
            continue
        if not (parts[0].lstrip("-").isdigit() and parts[1].lstrip("-").isdigit()):
            errors.append((i, raw))
            continue
    return errors


def validate_id_state_lines(text: str):
    """Return list of (line_no, line_text) that are invalid for id/state."""
    errors = []
    for i, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            errors.append((i, raw))
            continue
        if not (parts[0].lstrip("-").isdigit() and parts[1].lstrip("-").isdigit()):
            errors.append((i, raw))
            continue
    return errors


def extract_requirements(root, quest_id: int):
    info = dict(start_npc=None, end_npc=None, lvmin=None,
                items_text="", mobs_text="", quests_text="")
    node = get_imgdir(root, quest_id)
    if node is None:
        return info
    items = []
    mobs = []
    quests = []
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
                        iid = None
                        count = 1
                        for i in itemdir.findall("./int"):
                            nm = i.get("name")
                            try:
                                v = int(i.get("value"))
                            except (TypeError, ValueError):
                                continue
                            if nm == "id":
                                iid = v
                            elif nm == "count":
                                count = v
                        if iid is not None:
                            items.append((iid, count))
                elif cname == "mob":
                    for mobdir in child.findall("./imgdir"):
                        mid = None
                        count = 1
                        for i in mobdir.findall("./int"):
                            nm = i.get("name")
                            try:
                                v = int(i.get("value"))
                            except (TypeError, ValueError):
                                continue
                            if nm == "id":
                                mid = v
                            elif nm == "count":
                                count = v
                        if mid is not None:
                            mobs.append((mid, count))
                elif cname == "quest":
                    for qdir in child.findall("./imgdir"):
                        qid = None
                        st = None
                        for i in qdir.findall("./int"):
                            nm = i.get("name")
                            try:
                                v = int(i.get("value"))
                            except (TypeError, ValueError):
                                continue
                            if nm == "id":
                                qid = v
                            elif nm == "state":
                                st = v
                        if qid is not None and st is not None:
                            quests.append((qid, st))
    info["items_text"] = "\n".join(f"{i} {c}" for i, c in items)
    info["mobs_text"] = "\n".join(f"{i} {c}" for i, c in mobs)
    info["quests_text"] = "\n".join(f"{i} {s}" for i, s in quests)
    return info


def apply_requirements(root, quest_id: int, req: dict):
    if root is None or req is None:
        return
    node = get_imgdir(root, quest_id)
    any_detail = any(req.get(k) for k in ("start_npc", "end_npc", "lvmin", "items_text", "mobs_text", "quests_text"))
    if node is None:
        if not any_detail:
            return
        node = ET.SubElement(root, "imgdir", name=str(quest_id))

    def ensure_stage(name):
        st = node.find(f"./imgdir[@name='{name}']")
        if st is None:
            st = ET.SubElement(node, "imgdir", name=str(name))
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
            ET.SubElement(stage, "int", name=name, value=str(v))
        else:
            child.set("value", str(v))

    s0 = ensure_stage("0")
    s1 = ensure_stage("1")
    set_int(s0, "npc", req.get("start_npc"))
    set_int(s0, "lvmin", req.get("lvmin"))
    set_int(s1, "npc", req.get("end_npc"))

    def clear_child(name):
        for st in node.findall("./imgdir"):
            child = st.find(f"./imgdir[@name='{name}']")
            if child is not None:
                st.remove(child)

    def pick_stage_for(name, default_stage):
        for st in node.findall("./imgdir"):
            if st.find(f"./imgdir[@name='{name}']") is not None:
                return st
        return ensure_stage(default_stage)

    items_pairs = _parse_id_count_lines(req.get("items_text") or "")
    clear_child("item")
    if items_pairs:
        st_item = pick_stage_for("item", "1")
        parent = ET.SubElement(st_item, "imgdir", name="item")
        for idx, (iid, count) in enumerate(items_pairs):
            e = ET.SubElement(parent, "imgdir", name=str(idx))
            ET.SubElement(e, "int", name="id", value=str(iid))
            ET.SubElement(e, "int", name="count", value=str(count))

    mobs_pairs = _parse_id_count_lines(req.get("mobs_text") or "")
    clear_child("mob")
    if mobs_pairs:
        st_mob = pick_stage_for("mob", "1")
        parent = ET.SubElement(st_mob, "imgdir", name="mob")
        for idx, (mid, count) in enumerate(mobs_pairs):
            e = ET.SubElement(parent, "imgdir", name=str(idx))
            ET.SubElement(e, "int", name="id", value=str(mid))
            ET.SubElement(e, "int", name="count", value=str(count))

    quests_pairs = _parse_id_state_lines(req.get("quests_text") or "")
    clear_child("quest")
    if quests_pairs:
        st_q = pick_stage_for("quest", "0")
        parent = ET.SubElement(st_q, "imgdir", name="quest")
        for idx, (qid, st) in enumerate(quests_pairs):
            e = ET.SubElement(parent, "imgdir", name=str(idx))
            ET.SubElement(e, "int", name="id", value=str(qid))
            ET.SubElement(e, "int", name="state", value=str(st))


# ---------- Rewards (Act.img) ----------

def extract_rewards(root, quest_id: int):
    info = dict(exp=None, items_gain_text="", items_lose_text="")
    node = get_imgdir(root, quest_id)
    if node is None:
        return info
    gain = []
    lose = []
    for stage in node.findall("./imgdir"):
        for child in stage:
            if child.tag == "int" and child.get("name") == "exp":
                try:
                    info["exp"] = int(child.get("value"))
                except (TypeError, ValueError):
                    pass
            elif child.tag == "imgdir" and child.get("name") == "item":
                for itemdir in child.findall("./imgdir"):
                    iid = None
                    count = None
                    for i in itemdir.findall("./int"):
                        nm = i.get("name")
                        try:
                            v = int(i.get("value"))
                        except (TypeError, ValueError):
                            continue
                        if nm == "id":
                            iid = v
                        elif nm == "count":
                            count = v
                    if iid is not None and count is not None:
                        if count >= 0:
                            gain.append((iid, count))
                        else:
                            lose.append((iid, -count))
    info["items_gain_text"] = "\n".join(f"{i} {c}" for i, c in gain)
    info["items_lose_text"] = "\n".join(f"{i} {c}" for i, c in lose)
    return info


def apply_rewards(root, quest_id: int, rewards: dict):
    """Write EXP + item rewards in Act.img.xml for quest_id.

    Rules:
      - All rewards live under stage '1' (completion).
      - Stage '0' is never allowed to hold exp/item data.
    """
    if root is None or rewards is None:
        return

    any_detail = any(rewards.get(k) for k in ("exp", "items_gain_text", "items_lose_text"))
    node = get_imgdir(root, quest_id)
    if node is None:
        if not any_detail:
            return
        node = ET.SubElement(root, "imgdir", name=str(quest_id))

    # ---- Make sure stage '0' has no rewards ----
    stage0 = node.find("./imgdir[@name='0']")
    if stage0 is not None:
        for child in list(stage0):
            if child.tag == "int" and child.get("name") == "exp":
                stage0.remove(child)
            elif child.tag == "imgdir" and child.get("name") == "item":
                stage0.remove(child)

    # ---- Ensure we have stage '1' (complete) ----
    complete = node.find("./imgdir[@name='1']")
    if complete is None:
        complete = ET.SubElement(node, "imgdir", name="1")

    # Clear old exp + item from stage 1 only
    for child in list(complete):
        if child.tag == "int" and child.get("name") == "exp":
            complete.remove(child)
        elif child.tag == "imgdir" and child.get("name") == "item":
            complete.remove(child)

    # --- EXP reward ---
    exp_val = rewards.get("exp")
    if exp_val not in (None, "", "0"):
        try:
            exp_int = int(exp_val)
        except ValueError:
            exp_int = None
        if exp_int is not None:
            ET.SubElement(complete, "int", name="exp", value=str(exp_int))

    # --- Item rewards ---
    gain_pairs = _parse_id_count_lines(rewards.get("items_gain_text") or "")
    lose_pairs = _parse_id_count_lines(rewards.get("items_lose_text") or "")

    if gain_pairs or lose_pairs:
        item_parent = ET.SubElement(complete, "imgdir", name="item")
        idx = 0
        # positive count = gain
        for iid, count in gain_pairs:
            slot = ET.SubElement(item_parent, "imgdir", name=str(idx))
            idx += 1
            ET.SubElement(slot, "int", name="id", value=str(iid))
            ET.SubElement(slot, "int", name="count", value=str(count))
        # negative count = lose/consume
        for iid, count in lose_pairs:
            slot = ET.SubElement(item_parent, "imgdir", name=str(idx))
            idx += 1
            ET.SubElement(slot, "int", name="id", value=str(iid))
            ET.SubElement(slot, "int", name="count", value=str(-count))


# ---------- GUI ----------

class QuestHelperGUI:
    def __init__(self, root):
        apply_dark_theme(root)
        self.root = root
        root.title("Maple Quest Helper - Flat Editor (Dark)")

        self.qtree, self.qroot = load_xml(os.path.join(SCRIPT_DIR, "QuestInfo.img.xml"))
        if self.qroot is None:
            messagebox.showerror("Error", "QuestInfo.img.xml not found in script folder.")
        self.check_tree, self.check_root = load_xml(os.path.join(SCRIPT_DIR, "Check.img.xml"))
        self.act_tree, self.act_root = load_xml(os.path.join(SCRIPT_DIR, "Act.img.xml"))

        # cache for left-side quest list + search text
        self.all_quests = []
        self.search_var = tk.StringVar()

        # group visibility + widget collections for collapsible sections
        self.group_widgets = {
            "questinfo": [],
            "requirements": [],
            "rewards": [],
        }
        

        self.group_visible = {
            "questinfo": True,
            "requirements": True,
            "rewards": True,
        }

        self.all_text_widgets = []

        self._build_ui()
        if self.qroot is not None:
            self.populate_listbox()

        # mouse wheel scroll for whole editor
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)

    # mouse wheel handler
    def _on_mousewheel(self, event):
        if hasattr(self, "canvas"):
            self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    # ---- UI helpers ----
    def _set_entry(self, entry, text, readonly=False):
        entry.configure(state="normal")
        entry.delete(0, tk.END)
        entry.insert(0, text if text is not None else "")
        if readonly:
            entry.configure(state="readonly")
        else:
            entry.configure(state="normal")

    def _set_text(self, widget, text, readonly=False):
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        if text:
            widget.insert("1.0", text)
        if readonly:
            widget.configure(state="disabled")
        else:
            widget.configure(state="normal")

    def _get_entry(self, entry):
        return entry.get().strip()

    def _get_text(self, widget):
        return widget.get("1.0", tk.END).strip()

    def _register_group_widget(self, group, *widgets):
        if group not in self.group_widgets:
            return
        for w in widgets:
            if w is not None:
                self.group_widgets[group].append(w)

    def _configure_error_tag_on_text(self, widget):
        """Ensure the 'error' tag is configured once for a text widget."""
        widget.tag_configure("error", background="#552222")

    def _clear_all_error_tags(self):
        for w in self.all_text_widgets:
            w.tag_remove("error", "1.0", tk.END)

    def _highlight_lines(self, widget, line_nos):
        """Apply error tag to given 1-based line numbers in a Text widget."""
        for ln in line_nos:
            start = f"{ln}.0"
            end = f"{ln}.end"
            widget.tag_add("error", start, end)

    def toggle_group(self, group):
        """Collapse / expand a logical section (QuestInfo / Requirements / Rewards)."""
        widgets = self.group_widgets.get(group) or []
        if not widgets:
            return
        visible = self.group_visible.get(group, True)
        if visible:
            for w in widgets:
                w.grid_remove()
            self.group_visible[group] = False
        else:
            for w in widgets:
                w.grid()
            self.group_visible[group] = True

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=0)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(1, weight=1)

        # left quest list
        left = ttk.Frame(main)
        left.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 10))
        # row 0 = label, row 1 = search, row 2 = listbox
        left.rowconfigure(2, weight=1)

        ttk.Label(left, text="Quests in QuestInfo.img.xml").grid(row=0, column=0, sticky="w")

        # search bar
        search_frame = ttk.Frame(left)
        search_frame.grid(row=1, column=0, sticky="we", pady=(2, 2))
        ttk.Label(search_frame, text="Search:").pack(side="left")
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side="left", fill="x", expand=True)
        search_entry.bind("<KeyRelease>", self.on_search)

        # listbox
        self.quest_list = tk.Listbox(left, width=28, height=35, highlightbackground=DARK_HIGHLIGHT)
        self.quest_list.grid(row=2, column=0, sticky="nsew")
        self.quest_list.bind("<<ListboxSelect>>", self.on_list_select)

        # top bar
        top = ttk.Frame(main)
        top.grid(row=0, column=1, sticky="we", pady=(0, 5))
        top.columnconfigure(3, weight=1)
        ttk.Label(top, text="Base ID:").grid(row=0, column=0, sticky="e")
        self.base_id_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.base_id_var, width=8).grid(row=0, column=1, sticky="w", padx=(3, 10))
        ttk.Label(top, text="New ID:").grid(row=0, column=2, sticky="e")
        self.new_id_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.new_id_var, width=20).grid(row=0, column=3, sticky="w", padx=(3, 10))
        ttk.Button(top, text="Preview IDs", command=self.preview_ids).grid(row=0, column=4, padx=(5, 0))
        ttk.Button(top, text="Clone / Save", command=self.clone_quest).grid(row=0, column=5, padx=(5, 0))
        ttk.Button(top, text="Delete Quest", command=self.delete_quest).grid(row=0, column=6, padx=(5, 0))

        # scrollable right
        container = ttk.Frame(main)
        container.grid(row=1, column=1, sticky="nsew")
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        canvas = tk.Canvas(container, bg=DARK_BG, highlightthickness=0)
        self.canvas = canvas
        vbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")

        self.inner = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=self.inner, anchor="nw")

        def on_config(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        self.inner.bind("<Configure>", on_config)

        # three columns: base | transfer button | new
        self.inner.columnconfigure(0, weight=1)
        self.inner.columnconfigure(1, weight=0)
        self.inner.columnconfigure(2, weight=1)

        # toggle bar for collapsible sections
        toggle_bar = ttk.Frame(self.inner)
        toggle_bar.grid(row=0, column=0, columnspan=3, sticky="we", pady=(0, 5))
        ttk.Button(toggle_bar, text="QuestInfo ▼",
                   command=lambda: self.toggle_group("questinfo")).pack(side="left", padx=(0, 5))
        ttk.Button(toggle_bar, text="Requirements ▼",
                   command=lambda: self.toggle_group("requirements")).pack(side="left", padx=(0, 5))
        ttk.Button(toggle_bar, text="Rewards ▼",
                   command=lambda: self.toggle_group("rewards")).pack(side="left", padx=(0, 5))

        self.base_col = ttk.LabelFrame(self.inner, text="Base Quest (source, read-only)")
        self.base_col.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        self.base_col.columnconfigure(0, weight=1)

        # transfer column with copy + clear buttons
        self.transfer_col = ttk.Frame(self.inner)
        self.transfer_col.grid(row=1, column=1, sticky="ns", padx=2)
        ttk.Button(self.transfer_col, text=">>> Copy >>>", command=self.copy_base_to_new).pack(pady=(10, 5))
        ttk.Button(self.transfer_col, text="Clear New", command=self.clear_new_form).pack(pady=(0, 10))

        self.new_col = ttk.LabelFrame(self.inner, text="New Quest (editable)")
        self.new_col.grid(row=1, column=2, sticky="nsew", padx=(5, 0))
        self.new_col.columnconfigure(0, weight=1)

        r = 0
        current_group = "questinfo"

        # --- QuestInfo group ---

        lbl = ttk.Label(self.base_col, text="Name:")
        lbl2 = ttk.Label(self.new_col, text="Name:")
        lbl.grid(row=r, column=0, sticky="w")
        lbl2.grid(row=r, column=0, sticky="w")
        self._register_group_widget(current_group, lbl, lbl2)
        r += 1

        self.base_name = ttk.Entry(self.base_col, state="readonly")
        self.new_name = ttk.Entry(self.new_col)
        self.base_name.grid(row=r, column=0, sticky="we", pady=(0, 4))
        self.new_name.grid(row=r, column=0, sticky="we", pady=(0, 4))
        self._register_group_widget(current_group, self.base_name, self.new_name)
        r += 1

        lbl = ttk.Label(self.base_col, text="Type:")
        lbl2 = ttk.Label(self.new_col, text="Type:")
        lbl.grid(row=r, column=0, sticky="w")
        lbl2.grid(row=r, column=0, sticky="w")
        self._register_group_widget(current_group, lbl, lbl2)
        r += 1

        self.base_type = ttk.Entry(self.base_col, state="readonly")
        self.new_type = ttk.Entry(self.new_col)
        self.base_type.grid(row=r, column=0, sticky="we", pady=(0, 4))
        self.new_type.grid(row=r, column=0, sticky="we", pady=(0, 4))
        self._register_group_widget(current_group, self.base_type, self.new_type)
        r += 1

        lbl = ttk.Label(self.base_col, text="Area:")
        lbl2 = ttk.Label(self.new_col, text="Area:")
        lbl.grid(row=r, column=0, sticky="w")
        lbl2.grid(row=r, column=0, sticky="w")
        self._register_group_widget(current_group, lbl, lbl2)
        r += 1

        self.base_area = ttk.Entry(self.base_col, state="readonly")
        self.new_area = ttk.Entry(self.new_col)
        self.base_area.grid(row=r, column=0, sticky="we", pady=(0, 4))
        self.new_area.grid(row=r, column=0, sticky="we", pady=(0, 4))
        self._register_group_widget(current_group, self.base_area, self.new_area)
        r += 1

        lbl = ttk.Label(self.base_col, text="Parent:")
        lbl2 = ttk.Label(self.new_col, text="Parent:")
        lbl.grid(row=r, column=0, sticky="w")
        lbl2.grid(row=r, column=0, sticky="w")
        self._register_group_widget(current_group, lbl, lbl2)
        r += 1

        self.base_parent = ttk.Entry(self.base_col, state="readonly")
        self.new_parent = ttk.Entry(self.new_col)
        self.base_parent.grid(row=r, column=0, sticky="we", pady=(0, 4))
        self.new_parent.grid(row=r, column=0, sticky="we", pady=(0, 4))
        self._register_group_widget(current_group, self.base_parent, self.new_parent)
        r += 1

        lbl = ttk.Label(self.base_col, text="Order:")
        lbl2 = ttk.Label(self.new_col, text="Order:")
        lbl.grid(row=r, column=0, sticky="w")
        lbl2.grid(row=r, column=0, sticky="w")
        self._register_group_widget(current_group, lbl, lbl2)
        r += 1

        self.base_order = ttk.Entry(self.base_col, state="readonly")
        self.new_order = ttk.Entry(self.new_col)
        self.base_order.grid(row=r, column=0, sticky="we", pady=(0, 4))
        self.new_order.grid(row=r, column=0, sticky="we", pady=(0, 4))
        self._register_group_widget(current_group, self.base_order, self.new_order)
        r += 1

        lbl = ttk.Label(self.base_col, text="Auto Start:")
        lbl2 = ttk.Label(self.new_col, text="Auto Start:")
        lbl.grid(row=r, column=0, sticky="w")
        lbl2.grid(row=r, column=0, sticky="w")
        self._register_group_widget(current_group, lbl, lbl2)
        r += 1

        self.base_autostart = ttk.Entry(self.base_col, state="readonly")
        self.base_autostart.grid(row=r, column=0, sticky="we", pady=(0, 4))
        self._register_group_widget(current_group, self.base_autostart)
        self.new_autostart_var = tk.BooleanVar()
        self.new_autostart_cb = ttk.Checkbutton(self.new_col, variable=self.new_autostart_var, text="Enabled")
        self.new_autostart_cb.grid(row=r, column=0, sticky="w", pady=(0, 4))
        self._register_group_widget(current_group, self.new_autostart_cb)
        r += 1

        lbl = ttk.Label(self.base_col, text="Auto Complete:")
        lbl2 = ttk.Label(self.new_col, text="Auto Complete:")
        lbl.grid(row=r, column=0, sticky="w")
        lbl2.grid(row=r, column=0, sticky="w")
        self._register_group_widget(current_group, lbl, lbl2)
        r += 1

        self.base_autocomplete = ttk.Entry(self.base_col, state="readonly")
        self.base_autocomplete.grid(row=r, column=0, sticky="we", pady=(0, 4))
        self._register_group_widget(current_group, self.base_autocomplete)
        self.new_autocomplete_var = tk.BooleanVar()
        self.new_autocomplete_cb = ttk.Checkbutton(self.new_col, variable=self.new_autocomplete_var, text="Enabled")
        self.new_autocomplete_cb.grid(row=r, column=0, sticky="w", pady=(0, 4))
        self._register_group_widget(current_group, self.new_autocomplete_cb)
        r += 1

        def add_text_pair(label, height, group_name):
            nonlocal r
            lbl_a = ttk.Label(self.base_col, text=label)
            lbl_b = ttk.Label(self.new_col, text=label)
            lbl_a.grid(row=r, column=0, sticky="w")
            lbl_b.grid(row=r, column=0, sticky="w")
            self._register_group_widget(group_name, lbl_a, lbl_b)
            r += 1
            base = tk.Text(self.base_col, height=height, wrap="word")
            new = tk.Text(self.new_col, height=height, wrap="word")
            base.grid(row=r, column=0, sticky="we", pady=(0, 4))
            new.grid(row=r, column=0, sticky="we", pady=(0, 4))
            self.all_text_widgets.extend([base, new])
            self._configure_error_tag_on_text(new)
            self._register_group_widget(group_name, base, new)
            r += 1
            return base, new

        self.base_log0, self.new_log0 = add_text_pair("Log 0 (start):", 3, "questinfo")
        self.base_log1, self.new_log1 = add_text_pair("Log 1 (in progress):", 3, "questinfo")
        self.base_log2, self.new_log2 = add_text_pair("Log 2 (complete):", 3, "questinfo")
        self.base_summary, self.new_summary = add_text_pair("Summary:", 3, "questinfo")
        self.base_reward_summary, self.new_reward_summary = add_text_pair("Reward Summary:", 2, "questinfo")
        self.base_demand, self.new_demand = add_text_pair("Demand Summary:", 2, "questinfo")

        # --- Requirements group ---
        current_group = "requirements"

        self.base_start_npc, self.new_start_npc = add_text_pair("Start NPC (stage 0):", 1, current_group)
        self.base_end_npc, self.new_end_npc = add_text_pair("End NPC (stage 1):", 1, current_group)
        self.base_lvmin, self.new_lvmin = add_text_pair("Min Level:", 1, current_group)
        self.base_req_items, self.new_req_items = add_text_pair("Required Items (id count per line):", 4, current_group)
        self.base_req_mobs, self.new_req_mobs = add_text_pair("Required Mobs (id count per line):", 3, current_group)
        self.base_req_quests, self.new_req_quests = add_text_pair("Prereq Quests (id state per line):", 3, current_group)

        # --- Rewards group ---
        current_group = "rewards"

        self.base_exp, self.new_exp = add_text_pair("EXP Reward:", 1, current_group)
        self.base_rew_gain, self.new_rew_gain = add_text_pair("Reward Items Gained (id count per line):", 3, current_group)
        self.base_rew_lose, self.new_rew_lose = add_text_pair("Reward Items Consumed (id count per line):", 3, current_group)

    # ---------- data loading ----------

    def populate_listbox(self):
        # rebuild full quest cache from QuestInfo
        self.all_quests = []
        self.quest_list.delete(0, tk.END)
        if self.qroot is None:
            return
        for imgdir in self.qroot.findall("./imgdir"):
            qid = imgdir.get("name")
            if not (qid and qid.isdigit()):
                continue
            qd = extract_questinfo(self.qroot, int(qid))
            name = qd["name"] or ""
            self.all_quests.append((qid, name))
        # show everything (no filter) by default
        self._refresh_listbox("")

    def _refresh_listbox(self, filter_text: str):
        """Refresh quest_list from self.all_quests using optional filter.

        Supported search patterns:
          • plain text        -> matches ID or name substring
          • npc:<id>          -> quests starting/ending at NPC id
          • mob:<id>          -> quests requiring mob id
          • item:<id>         -> quests requiring/giving item id
          • rx:<pattern>      -> regex on "id: name"
        """
        self.quest_list.delete(0, tk.END)
        ft_raw = (filter_text or "").strip()
        ft = ft_raw.lower()

        if not ft:
            for qid, name in self.all_quests:
                self.quest_list.insert(tk.END, f"{qid}: {name}")
            return

        # regex search
        if ft.startswith("rx:"):
            pattern = ft_raw[3:].strip()
            try:
                rx = re.compile(pattern, re.IGNORECASE)
            except re.error:
                rx = None
            for qid, name in self.all_quests:
                line = f"{qid}: {name}"
                if rx:
                    if rx.search(line):
                        self.quest_list.insert(tk.END, line)
                else:
                    if pattern.lower() in line.lower():
                        self.quest_list.insert(tk.END, line)
            return

        # npc search
        if ft.startswith("npc:"):
            try:
                npc_id = int(ft[4:].strip())
            except ValueError:
                return
            for qid, name in self.all_quests:
                qid_int = int(qid)
                req = extract_requirements(self.check_root, qid_int)
                if req["start_npc"] == npc_id or req["end_npc"] == npc_id:
                    self.quest_list.insert(tk.END, f"{qid}: {name}")
            return

        # mob search
        if ft.startswith("mob:"):
            try:
                mob_id = int(ft[4:].strip())
            except ValueError:
                return
            for qid, name in self.all_quests:
                qid_int = int(qid)
                req = extract_requirements(self.check_root, qid_int)
                mobs_pairs = _parse_id_count_lines(req["mobs_text"] or "")
                if any(mid == mob_id for mid, _ in mobs_pairs):
                    self.quest_list.insert(tk.END, f"{qid}: {name}")
            return

        # item search (requirements + rewards)
        if ft.startswith("item:"):
            try:
                item_id = int(ft[5:].strip())
            except ValueError:
                return
            for qid, name in self.all_quests:
                qid_int = int(qid)
                req = extract_requirements(self.check_root, qid_int)
                rew = extract_rewards(self.act_root, qid_int)
                req_items = _parse_id_count_lines(req["items_text"] or "")
                gain_items = _parse_id_count_lines(rew["items_gain_text"] or "")
                lose_items = _parse_id_count_lines(rew["items_lose_text"] or "")
                if any(iid == item_id for iid, _ in req_items + gain_items + lose_items):
                    self.quest_list.insert(tk.END, f"{qid}: {name}")
            return

        # default: substring on ID or name
        for qid, name in self.all_quests:
            line = f"{qid}: {name}"
            if ft in qid or ft in name.lower():
                self.quest_list.insert(tk.END, line)

    def on_search(self, event=None):
        """Called when user types in the search box."""
        text = self.search_var.get()
        self._refresh_listbox(text)

    def on_list_select(self, event):
        if not self.quest_list.curselection():
            return
        idx = self.quest_list.curselection()[0]
        line = self.quest_list.get(idx)
        qid = line.split(":", 1)[0].strip()
        self.base_id_var.set(qid)
        # NEW ID is NOT auto-filled anymore; user must type it manually
        self.preview_ids()

    def preview_ids(self):
        if self.qroot is None:
            return
        base_id_str = self.base_id_var.get().strip()
        if not base_id_str.isdigit():
            messagebox.showwarning("Invalid IDs", "Base ID must be a number.")
            return
        base_id = int(base_id_str)

        # base quest info
        base_q = extract_questinfo(self.qroot, base_id)
        self._set_entry(self.base_name, base_q["name"], readonly=True)
        self._set_entry(self.base_type, base_q["type"], readonly=True)
        self._set_entry(self.base_area, "" if base_q["area"] is None else str(base_q["area"]), readonly=True)
        self._set_entry(self.base_parent, base_q["parent"], readonly=True)
        self._set_entry(self.base_order, "" if base_q["order"] is None else str(base_q["order"]), readonly=True)
        self._set_entry(self.base_autostart, "Yes" if base_q["autoStart"] else "No", readonly=True)
        self._set_entry(self.base_autocomplete, "Yes" if base_q["autoComplete"] else "No", readonly=True)
        self._set_text(self.base_log0, base_q["log0"], readonly=True)
        self._set_text(self.base_log1, base_q["log1"], readonly=True)
        self._set_text(self.base_log2, base_q["log2"], readonly=True)
        self._set_text(self.base_summary, base_q["summary"], readonly=True)
        self._set_text(self.base_reward_summary, base_q["rewardSummary"], readonly=True)
        self._set_text(self.base_demand, base_q["demandSummary"], readonly=True)

        # base requirements
        base_req = extract_requirements(self.check_root, base_id)
        self._set_text(self.base_start_npc,
                       "" if base_req["start_npc"] is None else str(base_req["start_npc"]),
                       readonly=True)
        self._set_text(self.base_end_npc,
                       "" if base_req["end_npc"] is None else str(base_req["end_npc"]),
                       readonly=True)
        self._set_text(self.base_lvmin,
                       "" if base_req["lvmin"] is None else str(base_req["lvmin"]),
                       readonly=True)
        self._set_text(self.base_req_items, base_req["items_text"], readonly=True)
        self._set_text(self.base_req_mobs, base_req["mobs_text"], readonly=True)
        self._set_text(self.base_req_quests, base_req["quests_text"], readonly=True)

        # base rewards
        base_rew = extract_rewards(self.act_root, base_id)
        self._set_text(self.base_exp,
                       "" if base_rew["exp"] is None else str(base_rew["exp"]),
                       readonly=True)
        self._set_text(self.base_rew_gain, base_rew["items_gain_text"], readonly=True)
        self._set_text(self.base_rew_lose, base_rew["items_lose_text"], readonly=True)
        # right side intentionally NOT touched

    # ---------- copy / clear new ----------

    def copy_base_to_new(self):
        """Copy all base quest fields into the editable new quest side."""
        if self.qroot is None:
            return
        base_id_str = self.base_id_var.get().strip()
        if not base_id_str.isdigit():
            messagebox.showwarning("Invalid base ID", "Base ID must be a number to copy from.")
            return
        base_id = int(base_id_str)

        base_q = extract_questinfo(self.qroot, base_id)
        base_req = extract_requirements(self.check_root, base_id)
        base_rew = extract_rewards(self.act_root, base_id)

        # QuestInfo -> new side
        self._set_entry(self.new_name, base_q["name"])
        self._set_entry(self.new_type, base_q["type"])
        self._set_entry(self.new_area, "" if base_q["area"] is None else str(base_q["area"]))
        self._set_entry(self.new_parent, base_q["parent"])
        self._set_entry(self.new_order, "" if base_q["order"] is None else str(base_q["order"]))
        self.new_autostart_var.set(bool(base_q["autoStart"]))
        self.new_autocomplete_var.set(bool(base_q["autoComplete"]))
        self._set_text(self.new_log0, base_q["log0"])
        self._set_text(self.new_log1, base_q["log1"])
        self._set_text(self.new_log2, base_q["log2"])
        self._set_text(self.new_summary, base_q["summary"])
        self._set_text(self.new_reward_summary, base_q["rewardSummary"])
        self._set_text(self.new_demand, base_q["demandSummary"])

        # Requirements
        self._set_text(self.new_start_npc,
                       "" if base_req["start_npc"] is None else str(base_req["start_npc"]))
        self._set_text(self.new_end_npc,
                       "" if base_req["end_npc"] is None else str(base_req["end_npc"]))
        self._set_text(self.new_lvmin,
                       "" if base_req["lvmin"] is None else str(base_req["lvmin"]))
        self._set_text(self.new_req_items, base_req["items_text"])
        self._set_text(self.new_req_mobs, base_req["mobs_text"])
        self._set_text(self.new_req_quests, base_req["quests_text"])

        # Rewards
        self._set_text(self.new_exp,
                       "" if base_rew["exp"] is None else str(base_rew["exp"]))
        self._set_text(self.new_rew_gain, base_rew["items_gain_text"])
        self._set_text(self.new_rew_lose, base_rew["items_lose_text"])

    def clear_new_form(self):
        """Clear all editable fields on the right side (but keep New ID)."""
        # entries
        for entry in [
            self.new_name,
            self.new_type,
            self.new_area,
            self.new_parent,
            self.new_order,
        ]:
            entry.configure(state="normal")
            entry.delete(0, tk.END)

        # checkboxes
        self.new_autostart_var.set(False)
        self.new_autocomplete_var.set(False)

        # texts
        for text_widget in [
            self.new_log0,
            self.new_log1,
            self.new_log2,
            self.new_summary,
            self.new_reward_summary,
            self.new_demand,
            self.new_start_npc,
            self.new_end_npc,
            self.new_lvmin,
            self.new_req_items,
            self.new_req_mobs,
            self.new_req_quests,
            self.new_exp,
            self.new_rew_gain,
            self.new_rew_lose,
        ]:
            text_widget.configure(state="normal")
            text_widget.delete("1.0", tk.END)

    # ---------- collect data & save ----------

    def _collect_questinfo_from_ui(self):
        return {
            "name": self._get_entry(self.new_name),
            "type": self._get_entry(self.new_type),
            "area": self._get_entry(self.new_area),
            "parent": self._get_entry(self.new_parent),
            "order": self._get_entry(self.new_order),
            "autoStart": self.new_autostart_var.get(),
            "autoComplete": self.new_autocomplete_var.get(),
            "log0": self._get_text(self.new_log0),
            "log1": self._get_text(self.new_log1),
            "log2": self._get_text(self.new_log2),
            "summary": self._get_text(self.new_summary),
            "rewardSummary": self._get_text(self.new_reward_summary),
            "demandSummary": self._get_text(self.new_demand),
        }

    def _collect_requirements_from_ui(self):
        return {
            "start_npc": self._get_text(self.new_start_npc),
            "end_npc": self._get_text(self.new_end_npc),
            "lvmin": self._get_text(self.new_lvmin),
            "items_text": self._get_text(self.new_req_items),
            "mobs_text": self._get_text(self.new_req_mobs),
            "quests_text": self._get_text(self.new_req_quests),
        }

    def _collect_rewards_from_ui(self):
        return {
            "exp": self._get_text(self.new_exp),
            "items_gain_text": self._get_text(self.new_rew_gain),
            "items_lose_text": self._get_text(self.new_rew_lose),
        }

    def clone_quest(self):
        base_id_str = self.base_id_var.get().strip()
        new_id_str = self.new_id_var.get().strip()

        if not base_id_str.isdigit():
            messagebox.showwarning("Invalid IDs", "Base ID must be a number.")
            return

        if not new_id_str:
            messagebox.showwarning(
                "Invalid IDs",
                "New ID must not be empty.\n\nYou can enter a single ID or multiple IDs separated by spaces/commas."
            )
            return

        # Parse one or more new IDs (space/comma separated)
        tokens = re.split(r"[,\s]+", new_id_str.strip())
        new_ids = []
        for t in tokens:
            if not t:
                continue
            if not t.isdigit():
                messagebox.showwarning(
                    "Invalid New ID",
                    f"'{t}' is not a valid numeric quest ID."
                )
                return
            val = int(t)
            if val not in new_ids:
                new_ids.append(val)

        if not new_ids:
            messagebox.showwarning(
                "Invalid New ID",
                "No valid quest IDs were found."
            )
            return

        base_id = int(base_id_str)

        # ---- VALIDATION of item / mob / quest lines ----
        self._clear_all_error_tags()
        validation_errors = []

        # id/count lines
        for widget, label in [
            (self.new_req_items, "Required Items"),
            (self.new_req_mobs, "Required Mobs"),
            (self.new_rew_gain, "Reward Items Gained"),
            (self.new_rew_lose, "Reward Items Consumed"),
        ]:
            text = self._get_text(widget)
            errs = validate_id_count_lines(text)
            if errs:
                line_nos = [ln for ln, _ in errs]
                self._highlight_lines(widget, line_nos)
                validation_errors.append(
                    f"{label}: invalid lines {', '.join(str(ln) for ln in line_nos)}"
                )

        # id/state lines
        q_text = self._get_text(self.new_req_quests)
        q_errs = validate_id_state_lines(q_text)
        if q_errs:
            line_nos = [ln for ln, _ in q_errs]
            self._highlight_lines(self.new_req_quests, line_nos)
            validation_errors.append(
                f"Prereq Quests: invalid lines {', '.join(str(ln) for ln in line_nos)}"
            )

        if validation_errors:
            messagebox.showerror(
                "Invalid Requirement / Reward Format",
                "Please fix the highlighted lines.\n\n"
                "Expected formats:\n"
                "  • Items / Mobs / Rewards:  itemId count\n"
                "      e.g. 2000001 10  or  2000001 x10\n"
                "  • Prereq Quests:  questId state\n"
                "      e.g. 1000 1\n\n"
                + "\n".join(validation_errors)
            )
            return

        # ---- overwrite warning for existing IDs (except edit-in-place) ----
        existing_ids = []
        if self.qroot is not None:
            for nid in new_ids:
                if nid != base_id and get_imgdir(self.qroot, nid) is not None:
                    existing_ids.append(nid)

        if existing_ids:
            if not messagebox.askyesno(
                "Overwrite Existing Quests",
                "The following quest IDs already exist and will be overwritten:\n"
                f"{', '.join(str(i) for i in existing_ids)}\n\nContinue?"
            ):
                return

        # collect data from UI
        qinfo = self._collect_questinfo_from_ui()
        req = self._collect_requirements_from_ui()
        rew = self._collect_rewards_from_ui()
        messages = []

        # perform cloning/saving for each target ID, per XML file
        for fname in FILES:
            path = os.path.join(SCRIPT_DIR, fname)
            if not os.path.isfile(path):
                messages.append(f"[INFO] {fname} not found, skipping.")
                continue
            backup = path + ".bak"
            shutil.copy2(path, backup)
            tree, root = load_xml(path)
            if root is None:
                messages.append(f"[WARN] Could not parse {fname}, skipping.")
                continue

            for nid in new_ids:
                new_node, msg = clone_node(root, base_id, nid)
                messages.append(f"{fname} ({nid}): {msg}")
                if fname == "QuestInfo.img.xml":
                    apply_questinfo(root, nid, qinfo)
                    messages.append(f"    QuestInfo updated for {nid}.")
                elif fname == "Check.img.xml":
                    apply_requirements(root, nid, req)
                    messages.append(f"    Check requirements updated for {nid}.")
                elif fname == "Act.img.xml":
                    apply_rewards(root, nid, rew)
                    messages.append(f"    Act rewards updated for {nid}.")

            tree.write(path, encoding="utf-8", xml_declaration=True)

        # reload so the list + previews are up-to-date
        self.qtree, self.qroot = load_xml(os.path.join(SCRIPT_DIR, "QuestInfo.img.xml"))
        self.check_tree, self.check_root = load_xml(os.path.join(SCRIPT_DIR, "Check.img.xml"))
        self.act_tree, self.act_root = load_xml(os.path.join(SCRIPT_DIR, "Act.img.xml"))
        self.populate_listbox()
        self.preview_ids()
        messagebox.showinfo("Clone / Save complete", "\n".join(messages))

    # ---------- delete quest ----------

    def delete_quest(self):
        """Delete quest from all XMLs.
        Priority:
          1) Currently selected quest in the left list
          2) Quest ID in New ID field
        """
        qid_str = None

        # 1) Try selected quest in the list
        if self.quest_list.curselection():
            idx = self.quest_list.curselection()[0]
            line = self.quest_list.get(idx)
            qid_str = line.split(":", 1)[0].strip()

        # 2) Fallback to New ID field if nothing selected
        if not qid_str:
            qid_str = self.new_id_var.get().strip()

        if not qid_str:
            messagebox.showwarning(
                "Delete Quest",
                "Select a quest on the left OR enter a quest ID in New ID."
            )
            return

        if not qid_str.isdigit():
            messagebox.showwarning("Delete Quest", "Quest ID must be a number.")
            return

        qid = int(qid_str)
        if not messagebox.askyesno(
            "Delete Quest",
            f"Delete quest {qid} from all XMLs?\n"
            "Backups (.bak) will be created first."
        ):
            return

        messages = []
        for fname in FILES:
            path = os.path.join(SCRIPT_DIR, fname)
            if not os.path.isfile(path):
                messages.append(f"[INFO] {fname} not found, skipping.")
                continue
            backup = path + ".bak"
            shutil.copy2(path, backup)
            tree, root = load_xml(path)
            if root is None:
                messages.append(f"[WARN] Could not parse {fname}, skipping.")
                continue
            node = get_imgdir(root, qid)
            if node is not None:
                root.remove(node)
                messages.append(f"{fname}: removed quest {qid}.")
                tree.write(path, encoding="utf-8", xml_declaration=True)
            else:
                messages.append(f"{fname}: quest {qid} not present.")

        # reload so the list + previews are up-to-date
        self.qtree, self.qroot = load_xml(os.path.join(SCRIPT_DIR, "QuestInfo.img.xml"))
        self.check_tree, self.check_root = load_xml(os.path.join(SCRIPT_DIR, "Check.img.xml"))
        self.act_tree, self.act_root = load_xml(os.path.join(SCRIPT_DIR, "Act.img.xml"))
        self.populate_listbox()
        self.preview_ids()
        messagebox.showinfo("Delete Quest", "\n".join(messages))


if __name__ == "__main__":
    root = tk.Tk()
    app = QuestHelperGUI(root)
    root.mainloop()
