import threading
import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
import numpy as np
import json
import os
try:
    from scipy.cluster.hierarchy import linkage, fcluster
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
class TileConverterApp:
    def __init__(self, root):
        self.root = root
        self.languages = {}
        self.current_lang = tk.StringVar(value="en")
        self.load_languages()
        self.image = None
        self.rebuilt_image = None
        self.tiles = []
        self.tile_map = []
        self.tile_w = tk.IntVar(value=8)
        self.tile_h = tk.IntVar(value=8)
        self.global_colors = tk.IntVar(value=32)
        self.max_tiles = tk.IntVar(value=256)
        self.resize_w = tk.IntVar(value=0)
        self.resize_h = tk.IntVar(value=0)
        self.cluster_method = tk.StringVar(value="auto")
        self.preset = tk.StringVar(value="Custom")
        self.progress_var = tk.DoubleVar(value=0)
        self.status_text = tk.StringVar(value="")
        self.percent_text = tk.StringVar(value="0%")
        self.build_gui()
        self.apply_preset()
        self.change_language()
    def load_languages(self):
        path = os.path.join(os.path.dirname(__file__), "lang.json")
        with open(path, "r", encoding="utf-8") as f:
            self.languages = json.load(f)
    def tr(self, key):
        return self.languages[self.current_lang.get()].get(key, key)
    def change_language(self, *args):
        self.root.title(self.tr("title"))
        self.lbl_lang.config(text=self.tr("language"))
        self.lbl_preset.config(text=self.tr("preset"))
        self.lbl_resize_w.config(text=self.tr("resize_w"))
        self.lbl_resize_h.config(text=self.tr("resize_h"))
        self.lbl_tile_w.config(text=self.tr("tile_w"))
        self.lbl_tile_h.config(text=self.tr("tile_h"))
        self.lbl_colors.config(text=self.tr("global_colors"))
        self.lbl_max_tiles.config(text=self.tr("max_tiles"))
        self.lbl_cluster.config(text=self.tr("cluster_method"))
        self.btn_load.config(text=self.tr("load_image"))
        self.btn_resize.config(text=self.tr("resize_image"))
        self.btn_convert.config(text=self.tr("convert"))
        self.btn_export.config(text=self.tr("export"))
    def build_gui(self):
        control = tk.Frame(self.root)
        control.pack(padx=10, pady=10)
        self.lbl_lang = tk.Label(control)
        self.lbl_lang.grid(row=0, column=0)
        lang_menu = ttk.Combobox(control,
                                 textvariable=self.current_lang,
                                 values=list(self.languages.keys()),
                                 state="readonly", width=6)
        lang_menu.grid(row=0, column=1)
        lang_menu.bind("<<ComboboxSelected>>", self.change_language)
        # Preset
        self.lbl_preset = tk.Label(control)
        self.lbl_preset.grid(row=1, column=0)
        preset_menu = ttk.Combobox(control,
                                   textvariable=self.preset,
                                   values=["GB", "GBC", "GBA", "NES", "SNES", "Custom"],
                                   state="readonly", width=8)
        preset_menu.grid(row=1, column=1)
        preset_menu.bind("<<ComboboxSelected>>", lambda e: self.apply_preset())
        self.btn_load = tk.Button(control, command=self.load_image)
        self.btn_load.grid(row=2, column=0, pady=5)
        self.lbl_resize_w = tk.Label(control)
        self.lbl_resize_w.grid(row=3, column=0)
        tk.Entry(control, textvariable=self.resize_w, width=6).grid(row=3, column=1)
        self.lbl_resize_h = tk.Label(control)
        self.lbl_resize_h.grid(row=4, column=0)
        tk.Entry(control, textvariable=self.resize_h, width=6).grid(row=4, column=1)
        self.btn_resize = tk.Button(control, command=self.resize_image)
        self.btn_resize.grid(row=5, column=0, pady=5)
        self.lbl_tile_w = tk.Label(control)
        self.lbl_tile_w.grid(row=6, column=0)
        tk.Entry(control, textvariable=self.tile_w, width=6).grid(row=6, column=1)
        self.lbl_tile_h = tk.Label(control)
        self.lbl_tile_h.grid(row=7, column=0)
        tk.Entry(control, textvariable=self.tile_h, width=6).grid(row=7, column=1)
        self.lbl_colors = tk.Label(control)
        self.lbl_colors.grid(row=8, column=0)
        tk.Entry(control, textvariable=self.global_colors, width=6).grid(row=8, column=1)
        self.lbl_max_tiles = tk.Label(control)
        self.lbl_max_tiles.grid(row=9, column=0)
        tk.Entry(control, textvariable=self.max_tiles, width=6).grid(row=9, column=1)
        self.lbl_cluster = tk.Label(control)
        self.lbl_cluster.grid(row=10, column=0)
        ttk.Combobox(control,
                     textvariable=self.cluster_method,
                     values=["auto", "kmeans", "python", "scipy"],
                     state="readonly",
                     width=8).grid(row=10, column=1)
        self.btn_convert = tk.Button(control, command=self.start_conversion)
        self.btn_convert.grid(row=11, column=0, pady=5)
        self.btn_export = tk.Button(control, command=self.export_png)
        self.btn_export.grid(row=11, column=1, pady=5)
        self.canvas = tk.Canvas(self.root, width=400, height=400, bg="gray")
        self.canvas.pack(pady=10)
        self.progress = ttk.Progressbar(self.root,
                                        variable=self.progress_var,
                                        maximum=100)
        self.progress.pack(fill="x", padx=10)
        tk.Label(self.root, textvariable=self.percent_text).pack()
        tk.Label(self.root, textvariable=self.status_text).pack()
    def apply_preset(self):
        p = self.preset.get()
        if p == "GB":
            self.global_colors.set(4)
            self.max_tiles.set(192)
        elif p == "GBC":
            self.global_colors.set(32)
            self.max_tiles.set(384)
        elif p == "GBA":
            self.global_colors.set(256)
            self.max_tiles.set(1024)
        elif p == "NES":
            self.global_colors.set(54)
            self.max_tiles.set(256)
        elif p == "SNES":
            self.global_colors.set(256)
            self.max_tiles.set(1024)
    def load_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        if not path:
            return
        self.image = Image.open(path).convert("RGB")
        self.display_image(self.image)
    def resize_image(self):
        if not self.image:
            return
        w, h = self.image.size
        new_w = self.resize_w.get()
        new_h = self.resize_h.get()
        if new_w > 0 and new_h == 0:
            new_h = int(h * (new_w / w))
        elif new_h > 0 and new_w == 0:
            new_w = int(w * (new_h / h))
        if new_w > 0 and new_h > 0:
            self.image = self.image.resize((new_w, new_h), Image.NEAREST)
            self.display_image(self.image)
    def display_image(self, img):
        w, h = img.size
        scale = min(400 / w, 400 / h)
        img = img.resize((int(w * scale), int(h * scale)), Image.NEAREST)
        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas.create_image(200, 200, image=self.tk_img)
    def update_progress(self, value, text):
        def _update():
            self.progress_var.set(value)
            self.percent_text.set(f"{int(value)}%")
            self.status_text.set(text)
        self.root.after(0, _update)
    def start_conversion(self):
        if not self.image:
            return
        threading.Thread(target=self.process_conversion, daemon=True).start()
    def process_conversion(self):
        self.update_progress(5, "Quantizing...")
        img = self.image.quantize(colors=self.global_colors.get()).convert("RGB")
        tw, th = self.tile_w.get(), self.tile_h.get()
        img_w, img_h = img.size
        img = img.crop((0, 0, (img_w // tw) * tw, (img_h // th) * th))
        self.update_progress(20, "Extracting tiles...")
        tiles = []
        vectors = []
        for y in range(0, img.size[1], th):
            for x in range(0, img.size[0], tw):
                tile = img.crop((x, y, x + tw, y + th))
                arr = np.array(tile).reshape(-1)
                tiles.append(tile)
                vectors.append(arr)
        vectors = np.array(vectors)
        if len(tiles) <= self.max_tiles.get():
            labels = np.arange(len(tiles))
        else:
            method = self.cluster_method.get()
            if method == "auto":
                method = "scipy" if SCIPY_AVAILABLE else "kmeans"
            self.update_progress(40, "Clustering...")
            if method == "scipy" and SCIPY_AVAILABLE:
                Z = linkage(vectors, method="complete")
                labels = fcluster(Z, t=self.max_tiles.get(), criterion='maxclust')
            elif method == "python":
                labels = self.agglomerative_python(vectors)
            else:
                labels = self.kmeans(vectors)
        self.update_progress(80, "Rebuilding...")
        unique = np.unique(labels)
        mapping = {}
        self.tiles = []
        for i, lab in enumerate(unique):
            idx = np.where(labels == lab)[0][0]
            mapping[lab] = i
            self.tiles.append(tiles[idx])
        self.tile_map = []
        idx = 0
        cols = img.size[0] // tw
        rows = img.size[1] // th
        for r in range(rows):
            row = []
            for c in range(cols):
                row.append(mapping[labels[idx]])
                idx += 1
            self.tile_map.append(row)
        self.rebuilt_image = self.rebuild_image(img.size[0], img.size[1])
        self.root.after(0, lambda: self.display_image(self.rebuilt_image))
        self.update_progress(100, "Done")
    def kmeans(self, vectors, iterations=10):
        n = len(vectors)
        k = self.max_tiles.get()
        centroids = vectors[np.random.choice(n, k, replace=False)]
        for _ in range(iterations):
            dists = np.linalg.norm(vectors[:, None] - centroids[None, :], axis=2)
            labels = np.argmin(dists, axis=1)
            for i in range(k):
                pts = vectors[labels == i]
                if len(pts) > 0:
                    centroids[i] = pts.mean(axis=0)
        return labels
    def agglomerative_python(self, vectors):
        clusters = [[i] for i in range(len(vectors))]
        while len(clusters) > self.max_tiles.get():
            best_i, best_j, best_d = 0, 1, None
            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    d = np.linalg.norm(
                        vectors[clusters[i][0]] - vectors[clusters[j][0]]
                    )
                    if best_d is None or d < best_d:
                        best_i, best_j, best_d = i, j, d
            clusters[best_i] += clusters[best_j]
            del clusters[best_j]
        labels = np.zeros(len(vectors))
        for idx, cluster in enumerate(clusters):
            for i in cluster:
                labels[i] = idx
        return labels
    def rebuild_image(self, w, h):
        tw, th = self.tile_w.get(), self.tile_h.get()
        img = Image.new("RGB", (w, h))
        for y, row in enumerate(self.tile_map):
            for x, idx in enumerate(row):
                img.paste(self.tiles[idx], (x * tw, y * th))
        return img
    def export_png(self):
        if self.rebuilt_image:
            self.rebuilt_image.save("preview.png")
if __name__ == "__main__":
    root = tk.Tk()
    app = TileConverterApp(root)
    root.mainloop()