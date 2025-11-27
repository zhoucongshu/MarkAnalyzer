# -*- coding: utf-8 -*-
"""
TVP & AGA Mark Analyzer (PyQt5)
"""
import sys
import re
import math
from typing import List, Dict, Tuple
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QCheckBox,
    QFileDialog, QHBoxLayout, QVBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt

# ---------- Parsing & Analysis Logic ----------
def extract_last_four_floats(tokens: List[str]) -> Tuple[float, float, float, float]:
    floats = []
    for tok in reversed(tokens):
        try:
            floats.append(float(tok))
            if len(floats) == 4:
                break
        except ValueError:
            continue
    if len(floats) < 4:
        raise ValueError("Not enough numeric tokens (need 4 at end).")
    x2, y2, x1, y1 = floats[::-1]
    return x1, y1, x2, y2

def parse_layer_from_tvp(identifier: str) -> str:
    m = re.search(r"\.TVP([A-Z0-9]+)_NS", identifier)
    if not m:
        return ""
    body = m.group(1)
    pos = body.rfind('Y')
    return body[pos + 1:] if pos >= 0 else ""

def parse_layer_from_aga(identifier: str) -> str:
    m = re.search(r"\.AGA([A-Z0-9]+)_NS", identifier)
    if not m:
        return ""
    body = m.group(1)
    posY = body.rfind('Y')
    posX = body.rfind('X')
    pos = max(posY, posX)
    return body[pos + 1:] if pos >= 0 else ""

def parse_marks_from_lines(lines: List[str], prefix: str) -> List[Dict]:
    records = []
    for raw in lines:
        if prefix in raw:
            parts = raw.strip().split()
            ident = parts[1] if len(parts) > 1 else ""
            try:
                x1, y1, x2, y2 = extract_last_four_floats(parts)
            except ValueError:
                continue
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            sx = abs(x2 - x1)
            sy = abs(y2 - y1)
            if prefix == "_MC_TVP":
                layer = parse_layer_from_tvp(ident)
                mark_type = "TVP"
            else:
                layer = parse_layer_from_aga(ident)
                mark_type = "AGA"
            records.append({
                "type": mark_type,
                "mark": ident,
                "layer": layer,
                "center_x": cx,
                "center_y": cy,
                "size_x": sx,
                "size_y": sy
            })
    return records

def add_nearest_same_layer(records: List[Dict]) -> List[Dict]:
    by_layer = {}
    for r in records:
        by_layer.setdefault(r["layer"], []).append(r)
    for r in records:
        layer_list = by_layer.get(r["layer"], [])
        cx, cy = r["center_x"], r["center_y"]
        nearest = None
        nearest_d = float("inf")
        for other in layer_list:
            if other is r:
                continue
            dx = other["center_x"] - cx
            dy = other["center_y"] - cy
            d = math.hypot(dx, dy)
            if d < nearest_d:
                nearest_d = d
                nearest = other
        if nearest is not None and nearest_d < float("inf"):
            dx = nearest["center_x"] - cx
            dy = nearest["center_y"] - cy
            angle = (math.degrees(math.atan2(dy, dx)) + 360.0) % 360.0
            r["nearest_name"] = nearest["mark"]
            r["nearest_dist"] = round(nearest_d, 3)
            r["nearest_angle"] = round(angle, 3)
        else:
            r["nearest_name"] = ""
            r["nearest_dist"] = ""
            r["nearest_angle"] = ""
    records.sort(key=lambda rr: (rr["layer"], rr["center_x"], rr["center_y"]))
    for i, rr in enumerate(records, start=1):
        rr["seq"] = i
    return records

def html_table_section(title: str, records: List[Dict]) -> str:
    rows = []
    for r in records:
        rows.append(
            f"<tr>"
            f"<td>{r['seq']}</td>"
            f"<td>{r['mark']}</td>"
            f"<td>{r['layer']}</td>"
            f"<td>{r['center_x']:.3f}</td>"
            f"<td>{r['center_y']:.3f}</td>"
            f"<td>{r['size_x']:.3f}</td>"
            f"<td>{r['size_y']:.3f}</td>"
            f"<td>{r['nearest_name']}</td>"
            f"<td>{r['nearest_dist']}</td>"
            f"<td>{r['nearest_angle']}</td>"
            f"</tr>"
        )
    table = (
        f"<h2 id='{title.lower()}'> {title} Marks</h2>"
        f"<div class='tablewrap'>"
        f"<table>"
        f"<thead><tr>"
        f"<th>Seq</th><th>Mark</th><th>Layer</th>"
        f"<th>Center X</th><th>Center Y</th>"
        f"<th>Size X</th><th>Size Y</th>"
        f"<th>Nearest (Same Layer)</th><th>Dist</th><th>Angle°</th>"
        f"</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        f"</table>"
        f"</div>"
    )
    return table

def build_html(tvp_records: List[Dict], aga_records: List[Dict]) -> str:
    style = """
    <style>
    body { font-family: Arial, Helvetica, sans-serif; margin: 20px; }
    h1 { font-size: 20px; margin-bottom: 6px; }
    h2 { font-size: 16px; margin-top: 24px; }
    .tablewrap { overflow-x: auto; }
    table { border-collapse: collapse; width: 100%; font-size: 12px; }
    th, td { border: 1px solid #ccc; padding: 6px 8px; text-align: left; }
    th { position: sticky; top: 0; background: #f5f5f5; }
    tr:nth-child(even) { background: #fafafa; }
    .note { color: #666; font-size: 11px; }
    nav a { margin-right: 12px; }
    </style>
    """
    sections = []
    if tvp_records:
        sections.append(html_table_section("TVP", tvp_records))
    if aga_records:
        sections.append(html_table_section("AGA", aga_records))
    nav_links = []
    if tvp_records:
        nav_links.append("<a href=\"#tvp\">TVP Section</a>")
    if aga_records:
        nav_links.append("<a href=\"#aga\">AGA Section</a>")
    html = (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<title>TVP & AGA Marks Analysis</title>"
        f"{style}</head><body>"
        "<h1>TVP & AGA Marks Analysis Report</h1>"
        f"<nav>{''.join(nav_links)}</nav>"
        "<p class='note'>Columns: Seq, Mark, Layer, Center X/Y, Size X/Y, "
        "Nearest (Same Layer), Dist, Angle°. Sorted by Layer → Center X → Center Y.</p>"
        f"{''.join(sections) if sections else '<p>No marks selected or found.</p>'}"
        "</body></html>"
    )
    return html

class MarkAnalyzerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TVP & AGA Mark Analyzer (PyQt5)")
        self.setMinimumWidth(640)
        self.lbl_file = QLabel("Input TXT file:")
        self.edit_file = QLineEdit()
        self.edit_file.setPlaceholderText("Choose your content .txt file...")
        self.btn_browse = QPushButton("Browse…")
        self.btn_browse.clicked.connect(self.on_browse)
        self.chk_tvp = QCheckBox("Analyze TVP marks")
        self.chk_tvp.setChecked(True)
        self.chk_aga = QCheckBox("Analyze AGA marks")
        self.chk_aga.setChecked(True)
        self.btn_generate = QPushButton("Generate HTML")
        self.btn_generate.setDefault(True)
        self.btn_generate.clicked.connect(self.on_generate)
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color:#555;")
        top = QHBoxLayout()
        top.addWidget(self.lbl_file)
        top.addWidget(self.edit_file)
        top.addWidget(self.btn_browse)
        opts = QHBoxLayout()
        opts.addWidget(self.chk_tvp)
        opts.addWidget(self.chk_aga)
        opts.addStretch(1)
        main = QVBoxLayout()
        main.addLayout(top)
        main.addLayout(opts)
        main.addWidget(self.btn_generate)
        main.addWidget(self.lbl_status)
        self.setLayout(main)

    def on_browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select content TXT file",
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        if path:
            self.edit_file.setText(path)

    def on_generate(self):
        path = self.edit_file.text().strip()
        analyze_tvp = self.chk_tvp.isChecked()
        analyze_aga = self.chk_aga.isChecked()
        if not path:
            QMessageBox.warning(self, "Missing file", "Please select a TXT content file.")
            return
        if not (analyze_tvp or analyze_aga):
            QMessageBox.warning(self, "No selection", "Please select at least one mark type (TVP/AGA).")
            return
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception as e:
            QMessageBox.critical(self, "Read error", f"Failed to read file:\n{e}")
            return
        tvp_records = []
        aga_records = []
        try:
            if analyze_tvp:
                tvp_records = parse_marks_from_lines(lines, "_MC_TVP")
                tvp_records = add_nearest_same_layer(tvp_records)
            if analyze_aga:
                aga_records = parse_marks_from_lines(lines, "_MC_AGA")
                aga_records = add_nearest_same_layer(aga_records)
        except Exception as e:
            QMessageBox.critical(self, "Parse error", f"Parsing failed:\n{e}")
            return
        html = build_html(tvp_records, aga_records)
        out_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save HTML report",
            "mark_analysis_report.html",
            "HTML Files (*.html);;All Files (*)"
        )
        if not out_path:
            return
        try:
            with open(out_path, "w", encoding="utf-8") as fo:
                fo.write(html)
        except Exception as e:
            QMessageBox.critical(self, "Write error", f"Failed to write HTML:\n{e}")
            return
        tvp_count = len(tvp_records) if analyze_tvp else 0
        aga_count = len(aga_records) if analyze_aga else 0
        self.lbl_status.setText(
            f"Done. TVP: {tvp_count}, AGA: {aga_count}. Saved to: {out_path}"
        )
        QMessageBox.information(
            self,
            "Success",
            f"HTML report generated.\n\nTVP: {tvp_count}\nAGA: {aga_count}\n\nSaved to:\n{out_path}"
        )


def main():
    app = QApplication(sys.argv)
    gui = MarkAnalyzerGUI()
    gui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
