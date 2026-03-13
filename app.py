import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import fitz
import yaml
from PIL import Image, ImageTk


def load_config(config_path: Path) -> dict:
	if not config_path.exists():
		return {}

	with config_path.open("r", encoding="utf-8") as file:
		loaded = yaml.safe_load(file) or {}
	if not isinstance(loaded, dict):
		return {}

	return loaded


class SpeedPDFApp:
	def __init__(self, root: tk.Tk) -> None:
		self.root = root
		self.config = load_config(Path(__file__).with_name("config.yaml"))
		app_cfg = self.config.get("app", {})
		reader_cfg = self.config.get("reader", {})

		self.app_title = str(app_cfg.get("title", "Speed-PDF"))
		self.window_width = int(app_cfg.get("window_width", 1100))
		self.window_height = int(app_cfg.get("window_height", 700))
		self.min_width = int(app_cfg.get("min_width", 900))
		self.min_height = int(app_cfg.get("min_height", 550))

		self.wpm_default = int(reader_cfg.get("wpm_default", 300))
		self.wpm_min = int(reader_cfg.get("wpm_min", 100))
		self.wpm_max = int(reader_cfg.get("wpm_max", 1000))

		self.root.title(self.app_title)
		self.root.geometry(f"{self.window_width}x{self.window_height}")
		self.root.minsize(self.min_width, self.min_height)
		self.root.configure(bg="#0f172a")

		self.words: list[str] = []
		self.pdf_word_entries: list[dict] = []
		self.current_file_name = ""
		self.word_index = 0
		self.is_playing = False
		self.current_job: str | None = None
		self.is_updating_progress = False
		self.pdf_doc: fitz.Document | None = None
		self.pdf_current_page = 0
		self.text_canvas: tk.Canvas | None = None
		self.text_line_label: tk.Label | None = None
		self.text_page_label: tk.Label | None = None
		self.text_canvas_image_ref: ImageTk.PhotoImage | None = None

		self._build_ui()

	def _build_ui(self) -> None:
		self.root.bind("<Configure>", self._on_resize)

		self.title_label = tk.Label(
			self.root,
			text="Speed-PDF",
			font=("Segoe UI", 34, "bold"),
			fg="#e2e8f0",
			bg="#0f172a",
		)
		self.title_label.place(relx=0.5, y=24, anchor="n")

		self.subtitle_label = tk.Label(
			self.root,
			text="Load a PDF and read one word at a time without moving your eyes",
			font=("Segoe UI", 11),
			fg="#94a3b8",
			bg="#0f172a",
		)
		self.subtitle_label.place(relx=0.5, y=86, anchor="n")

		controls = tk.Frame(self.root, bg="#0f172a")
		controls.place(relx=0.5, y=120, anchor="n")

		self.open_button = tk.Button(
			controls,
			text="Open PDF",
			command=self.open_pdf,
			font=("Segoe UI", 11, "bold"),
			padx=16,
			pady=8,
			bg="#2563eb",
			fg="#ffffff",
			activebackground="#1d4ed8",
			activeforeground="#ffffff",
			relief="flat",
			cursor="hand2",
		)
		self.open_button.grid(row=0, column=0, padx=(0, 16))

		self.start_button = tk.Button(
			controls,
			text="Start",
			command=self.start_playback,
			font=("Segoe UI", 11, "bold"),
			padx=16,
			pady=8,
			bg="#16a34a",
			fg="#ffffff",
			activebackground="#15803d",
			activeforeground="#ffffff",
			relief="flat",
			cursor="hand2",
		)
		self.start_button.grid(row=0, column=1, padx=(0, 8))

		self.stop_button = tk.Button(
			controls,
			text="Stop",
			command=self.stop_playback,
			font=("Segoe UI", 11, "bold"),
			padx=16,
			pady=8,
			bg="#ef4444",
			fg="#ffffff",
			activebackground="#dc2626",
			activeforeground="#ffffff",
			relief="flat",
			cursor="hand2",
		)
		self.stop_button.grid(row=0, column=2, padx=(0, 16))

		tk.Label(
			controls,
			text="Speed (WPM)",
			font=("Segoe UI", 10),
			fg="#cbd5e1",
			bg="#0f172a",
		).grid(row=0, column=3, sticky="e")

		self.speed_var = tk.IntVar(value=300)
		self.speed_scale = tk.Scale(
			controls,
			from_=self.wpm_min,
			to=self.wpm_max,
			orient="horizontal",
			resolution=10,
			variable=self.speed_var,
			length=260,
			showvalue=False,
			troughcolor="#334155",
			bg="#0f172a",
			fg="#e2e8f0",
			activebackground="#60a5fa",
			highlightthickness=0,
		)
		self.speed_scale.grid(row=0, column=4, padx=(8, 8))
		self.speed_var.set(self.wpm_default)

		self.speed_value = tk.Label(
			controls,
			text="300",
			font=("Segoe UI", 10, "bold"),
			fg="#93c5fd",
			bg="#0f172a",
			width=5,
		)
		self.speed_value.grid(row=0, column=5, sticky="w")
		self.speed_var.trace_add("write", self._on_speed_change)

		self.content_split = tk.Frame(self.root, bg="#0f172a")
		self.content_split.place(relx=0.5, rely=0.24, anchor="n", relwidth=0.96, relheight=0.74)
		self.content_split.grid_columnconfigure(0, weight=2)
		self.content_split.grid_columnconfigure(1, weight=3)
		self.content_split.grid_rowconfigure(0, weight=1)

		self.reader_panel = tk.Frame(
			self.content_split,
			bg="#0f172a",
			highlightthickness=1,
			highlightbackground="#334155",
		)
		self.reader_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

		self.pdf_panel = tk.Frame(
			self.content_split,
			bg="#111827",
			highlightthickness=1,
			highlightbackground="#334155",
		)
		self.pdf_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

		self.word_label = tk.Label(
			self.reader_panel,
			text="Open a PDF to begin",
			font=("Segoe UI", 46, "bold"),
			fg="#f8fafc",
			bg="#0f172a",
			wraplength=560,
			justify="center",
		)
		self.word_label.pack(expand=True, fill="both", padx=12, pady=(12, 8))

		progress_frame = tk.Frame(self.reader_panel, bg="#0f172a")
		progress_frame.pack(fill="x", padx=12, pady=(0, 8))

		tk.Label(
			progress_frame,
			text="Progress",
			font=("Segoe UI", 10),
			fg="#cbd5e1",
			bg="#0f172a",
		).grid(row=0, column=0, padx=(0, 10))

		self.progress_var = tk.IntVar(value=0)
		self.progress_scale = tk.Scale(
			progress_frame,
			from_=0,
			to=0,
			orient="horizontal",
			resolution=1,
			variable=self.progress_var,
			length=420,
			showvalue=False,
			troughcolor="#334155",
			bg="#0f172a",
			fg="#e2e8f0",
			activebackground="#60a5fa",
			highlightthickness=0,
			command=self._on_seek,
		)
		self.progress_scale.grid(row=0, column=1, padx=(0, 10))

		self.progress_text = tk.Label(
			progress_frame,
			text="0 / 0",
			font=("Segoe UI", 10, "bold"),
			fg="#93c5fd",
			bg="#0f172a",
			width=12,
		)
		self.progress_text.grid(row=0, column=2, sticky="w")

		self.status_label = tk.Label(
			self.reader_panel,
			text="No file loaded",
			font=("Segoe UI", 10),
			fg="#94a3b8",
			bg="#0f172a",
		)
		self.status_label.pack(fill="x", padx=12, pady=(0, 10))

		header = tk.Frame(self.pdf_panel, bg="#0f172a")
		header.pack(fill="x", padx=8, pady=(8, 6))

		self.text_line_label = tk.Label(
			header,
			text="Line: -",
			font=("Segoe UI", 10, "bold"),
			fg="#93c5fd",
			bg="#0f172a",
		)
		self.text_line_label.pack(side="left", anchor="w")

		self.text_page_label = tk.Label(
			header,
			text="Page: - / -",
			font=("Segoe UI", 10, "bold"),
			fg="#93c5fd",
			bg="#0f172a",
		)
		self.text_page_label.pack(side="left", padx=(12, 0))

		nav = tk.Frame(self.pdf_panel, bg="#0f172a")
		nav.pack(fill="x", padx=8, pady=(0, 6))

		tk.Button(
			nav,
			text="Previous Page",
			command=self._go_to_prev_pdf_page,
			font=("Segoe UI", 9, "bold"),
			bg="#334155",
			fg="#ffffff",
			activebackground="#1e293b",
			activeforeground="#ffffff",
			relief="flat",
		).pack(side="left")

		tk.Button(
			nav,
			text="Next Page",
			command=self._go_to_next_pdf_page,
			font=("Segoe UI", 9, "bold"),
			bg="#334155",
			fg="#ffffff",
			activebackground="#1e293b",
			activeforeground="#ffffff",
			relief="flat",
		).pack(side="left", padx=(8, 0))

		self.text_canvas = tk.Canvas(
			self.pdf_panel,
			bg="#111827",
			highlightthickness=0,
		)
		self.text_canvas.pack(expand=True, fill="both", padx=8, pady=(0, 8))
		self.text_canvas.bind("<Configure>", self._on_pdf_canvas_resize)
		self._refresh_text_window_content()

	def _on_resize(self, _event: tk.Event) -> None:
		panel_width = self.reader_panel.winfo_width() if hasattr(self, "reader_panel") else self.root.winfo_width()
		wrap = max(260, panel_width - 40)
		self.word_label.config(wraplength=wrap)

	def _on_speed_change(self, *_args) -> None:
		self.speed_value.config(text=str(self.speed_var.get()))

	def _on_seek(self, value: str) -> None:
		if self.is_updating_progress or not self.words:
			return

		position = max(0, min(int(float(value)), len(self.words)))
		self.word_index = position

		if position == 0:
			self.word_label.config(text="Ready to start")
		else:
			self.word_label.config(text=self.words[position - 1])

		self._update_progress_text()
		self._update_text_view_tracking()
		if self.current_job is not None and self.is_playing:
			self.root.after_cancel(self.current_job)
			self.current_job = None
			self.current_job = self.root.after(self._get_delay_ms(), self._show_next_word)

	def open_pdf(self) -> None:
		file_path = filedialog.askopenfilename(
			title="Choose PDF",
			filetypes=[("PDF Files", "*.pdf")],
		)
		if not file_path:
			return

		try:
			words, text, word_entries = self._extract_pdf_words_with_layout(Path(file_path))
		except Exception as error:
			messagebox.showerror("Failed to read PDF", str(error))
			return

		if not words:
			messagebox.showwarning("No text found", "This PDF does not contain readable text.")
			return

		self.current_file_name = Path(file_path).name
		self.words = words
		self.pdf_word_entries = word_entries
		self.pdf_current_page = 0
		self.word_index = 0
		self.stop_playback()
		self.word_label.config(text="Ready to start")
		self.progress_scale.config(to=len(self.words))
		self._set_progress_value(0)
		self._update_progress_text()
		self.status_label.config(text=f"Loaded: {self.current_file_name} · {len(self.words)} words")
		self._refresh_text_window_content()
		self._update_text_view_tracking()

	def _extract_pdf_words_with_layout(self, file_path: Path) -> tuple[list[str], str, list[dict]]:
		doc = fitz.open(str(file_path))
		self.pdf_doc = doc

		page_text_parts: list[str] = []
		word_entries: list[dict] = []
		line_index_map: dict[tuple[int, int, int], int] = {}
		line_counter = 0
		line_bbox_map: dict[tuple[int, int, int], list[float]] = {}

		for page_index, page in enumerate(doc):
			page_text_parts.append(page.get_text("text") or "")
			page_words = page.get_text("words")
			page_words.sort(key=lambda item: (item[5], item[6], item[7]))

			for item in page_words:
				x0, y0, x1, y1, text, block_no, line_no, _word_no = item[:8]
				token_text = str(text).strip()
				if not token_text:
					continue

				line_key = (page_index, int(block_no), int(line_no))
				if line_key not in line_index_map:
					line_index_map[line_key] = line_counter
					line_counter += 1
					line_bbox_map[line_key] = [float(x0), float(y0), float(x1), float(y1)]
				else:
					bbox = line_bbox_map[line_key]
					bbox[0] = min(bbox[0], float(x0))
					bbox[1] = min(bbox[1], float(y0))
					bbox[2] = max(bbox[2], float(x1))
					bbox[3] = max(bbox[3], float(y1))

				tokens = re.findall(r"\S+", token_text)
				for token in tokens:
					word_entries.append(
						{
							"word": token,
							"page": page_index,
							"line_key": line_key,
							"line_flat_index": line_index_map[line_key],
						}
					)

		for entry in word_entries:
			line_box = line_bbox_map[entry["line_key"]]
			entry["line_bbox"] = (line_box[0], line_box[1], line_box[2], line_box[3])

		all_words = [entry["word"] for entry in word_entries]
		full_text = "\n".join(page_text_parts)
		return all_words, full_text, word_entries

	def _refresh_text_window_content(self) -> None:
		if self.text_canvas is None or not self.text_canvas.winfo_exists():
			return
		self._render_pdf_page()

	def _on_pdf_canvas_resize(self, _event: tk.Event) -> None:
		self._render_pdf_page()

	def _render_pdf_page(self, highlight_bbox: tuple[float, float, float, float] | None = None) -> None:
		if self.text_canvas is None or self.pdf_doc is None or len(self.pdf_doc) == 0:
			if self.text_canvas is not None:
				self.text_canvas.delete("all")
				self.text_canvas.create_text(
					20,
					20,
					anchor="nw",
					text="Open a PDF to display pages.",
					fill="#e5e7eb",
					font=("Segoe UI", 12),
				)
				self.text_canvas.config(scrollregion=(0, 0, 500, 300))
			if self.text_page_label is not None:
				self.text_page_label.config(text="Page: - / -")
			return

		self.pdf_current_page = max(0, min(self.pdf_current_page, len(self.pdf_doc) - 1))
		page = self.pdf_doc[self.pdf_current_page]
		canvas_w = max(120, self.text_canvas.winfo_width())
		canvas_h = max(120, self.text_canvas.winfo_height())
		page_rect = page.rect
		fit_scale = min((canvas_w - 12) / page_rect.width, (canvas_h - 12) / page_rect.height)
		render_scale = max(0.1, min(fit_scale, 3.0))

		pix = page.get_pixmap(matrix=fitz.Matrix(render_scale, render_scale), alpha=False)
		image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
		self.text_canvas_image_ref = ImageTk.PhotoImage(image)

		self.text_canvas.delete("all")
		offset_x = max((canvas_w - pix.width) / 2, 0)
		offset_y = max((canvas_h - pix.height) / 2, 0)
		self.text_canvas.create_image(offset_x, offset_y, anchor="nw", image=self.text_canvas_image_ref)

		if highlight_bbox is not None:
			x0, y0, x1, y1 = highlight_bbox
			scale = render_scale
			self.text_canvas.create_rectangle(
				offset_x + x0 * scale,
				offset_y + y0 * scale,
				offset_x + x1 * scale,
				offset_y + y1 * scale,
				outline="#ef4444",
				width=3,
			)

		self.text_canvas.config(scrollregion=(0, 0, canvas_w, canvas_h))
		if self.text_page_label is not None:
			self.text_page_label.config(text=f"Page: {self.pdf_current_page + 1} / {len(self.pdf_doc)}")

	def _update_text_view_tracking(self) -> None:
		if self.text_canvas is None or not self.text_canvas.winfo_exists():
			return

		highlight_bbox: tuple[float, float, float, float] | None = None
		display_word_index = self.word_index - 1 if self.word_index > 0 else None

		if display_word_index is not None and 0 <= display_word_index < len(self.pdf_word_entries):
			entry = self.pdf_word_entries[display_word_index]
			self.pdf_current_page = entry["page"]
			highlight_bbox = entry.get("line_bbox")
			if self.text_line_label is not None:
				self.text_line_label.config(
					text=f"Line: {entry['line_flat_index'] + 1} (word {display_word_index + 1})"
				)
		else:
			if self.text_line_label is not None:
				self.text_line_label.config(text="Line: -")

		self._render_pdf_page(highlight_bbox=highlight_bbox)

	def _go_to_prev_pdf_page(self) -> None:
		if self.pdf_doc is None or len(self.pdf_doc) == 0:
			return
		self.pdf_current_page = max(0, self.pdf_current_page - 1)
		self._render_pdf_page()

	def _go_to_next_pdf_page(self) -> None:
		if self.pdf_doc is None or len(self.pdf_doc) == 0:
			return
		self.pdf_current_page = min(len(self.pdf_doc) - 1, self.pdf_current_page + 1)
		self._render_pdf_page()

	def _set_controls_state(self, enabled: bool) -> None:
		state = "normal" if enabled else "disabled"
		self.open_button.config(state=state)
		self.start_button.config(state=state)
		self.stop_button.config(state=state)
		self.speed_scale.config(state=state)
		self.progress_scale.config(state=state)

	def start_playback(self) -> None:
		if not self.words:
			messagebox.showinfo("No PDF loaded", "Please open a PDF first.")
			return

		if self.word_index >= len(self.words):
			self.word_index = 0
			self._set_progress_value(0)

		self.is_playing = True
		if self.current_job is not None:
			self.root.after_cancel(self.current_job)
			self.current_job = None
		self._show_next_word()

	def stop_playback(self) -> None:
		self.is_playing = False
		if self.current_job is not None:
			self.root.after_cancel(self.current_job)
			self.current_job = None
		if self.words:
			self.status_label.config(text=f"Paused · {self.word_index} / {len(self.words)} words")

	def _get_delay_ms(self) -> int:
		wpm = max(1, self.speed_var.get())
		return int(60000 / wpm)

	def _set_progress_value(self, value: int) -> None:
		self.is_updating_progress = True
		self.progress_var.set(value)
		self.is_updating_progress = False

	def _update_progress_text(self) -> None:
		self.progress_text.config(text=f"{self.word_index} / {len(self.words)}")

	def _show_next_word(self) -> None:
		if not self.is_playing or self.word_index >= len(self.words):
			self.current_job = None
			if self.word_index >= len(self.words) and self.words:
				self.status_label.config(text="Finished reading PDF")
				self.is_playing = False
			return

		self.word_label.config(text=self.words[self.word_index])
		self.word_index += 1
		self._set_progress_value(self.word_index)
		self._update_progress_text()
		self._update_text_view_tracking()
		self.status_label.config(text=f"Reading · {self.word_index} / {len(self.words)} words")
		self.current_job = self.root.after(self._get_delay_ms(), self._show_next_word)


def main() -> None:
	root = tk.Tk()
	app = SpeedPDFApp(root)
	root.mainloop()


if __name__ == "__main__":
	main()
