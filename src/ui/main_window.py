
"""
Project : Document Converter
Project ID : 034

Desktop Main Window
"""

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from src.config import APP_VERSION, OUTPUT_DIR
from src.services.batch_conversion_service import (
    BatchConversionService,
)
from src.services.conversion_history_service import (
    ConversionHistoryService,
)
from src.services.pdf_operation_service import (
    PDFOperationService,
)


class MainWindow:
    """Desktop interface for document conversion and batch processing."""

    OPERATIONS = {
        "DOCX to PDF": "docx_to_pdf",
        "PDF to DOCX": "pdf_to_docx",
        "DOCX to TXT": "docx_to_txt",
        "TXT to DOCX": "txt_to_docx",
        "Merge PDFs": "merge_pdfs",
        "Extract PDF Pages": "extract_pages",
    }

    FILE_TYPES = [
        ("Supported documents", "*.docx *.pdf *.txt"),
        ("Word documents", "*.docx"),
        ("PDF documents", "*.pdf"),
        ("Text files", "*.txt"),
        ("All files", "*.*"),
    ]

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(f"Document Converter v{APP_VERSION}")
        self.root.geometry("900x650")
        self.root.minsize(720, 520)

        self.batch_service = BatchConversionService()
        self.history_service = ConversionHistoryService()
        self.pdf_service = PDFOperationService()

        self.input_paths: list[Path] = []
        self.output_directory = tk.StringVar(
            value=str(OUTPUT_DIR)
        )
        self.operation = tk.StringVar(
            value="DOCX to PDF"
        )
        self.page_selection = tk.StringVar()
        self.status_text = tk.StringVar(
            value="Ready."
        )

        self._messages: queue.Queue = queue.Queue()
        self._running = False

        self._build_interface()
        self._refresh_history()
        self.root.after(100, self._process_messages)

    def _build_interface(self) -> None:
        """Build the main window and its controls."""

        container = ttk.Frame(self.root, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            container,
            text="Document Converter",
            font=("Segoe UI", 15, "bold"),
        ).pack(anchor=tk.W)

        operation_frame = ttk.LabelFrame(
            container, text="Conversion Operation", padding=8
        )
        operation_frame.pack(fill=tk.X, pady=(10, 6))

        ttk.Label(
            operation_frame, text="Operation:"
        ).pack(side=tk.LEFT)

        self.operation_combo = ttk.Combobox(
            operation_frame,
            textvariable=self.operation,
            values=list(self.OPERATIONS.keys()),
            state="readonly",
            width=25,
        )
        self.operation_combo.pack(
            side=tk.LEFT, padx=8
        )
        self.operation_combo.bind(
            "<<ComboboxSelected>>",
            self._operation_changed,
        )

        ttk.Label(
            operation_frame, text="Pages:"
        ).pack(side=tk.LEFT, padx=(12, 4))

        self.pages_entry = ttk.Entry(
            operation_frame,
            textvariable=self.page_selection,
            width=16,
        )
        self.pages_entry.pack(side=tk.LEFT)
        self.pages_entry.configure(state=tk.DISABLED)

        file_frame = ttk.LabelFrame(
            container, text="Input Files", padding=8
        )
        file_frame.pack(fill=tk.BOTH, expand=True, pady=6)

        button_row = ttk.Frame(file_frame)
        button_row.pack(fill=tk.X, pady=(0, 6))

        self.add_button = ttk.Button(
            button_row,
            text="Add Files",
            command=self._add_files,
        )
        self.add_button.pack(side=tk.LEFT)

        self.remove_button = ttk.Button(
            button_row,
            text="Remove Selected",
            command=self._remove_selected,
        )
        self.remove_button.pack(
            side=tk.LEFT, padx=6
        )

        self.clear_button = ttk.Button(
            button_row,
            text="Clear List",
            command=self._clear_files,
        )
        self.clear_button.pack(side=tk.LEFT)

        self.file_list = tk.Listbox(
            file_frame,
            selectmode=tk.EXTENDED,
            height=7,
        )
        self.file_list.pack(
            fill=tk.BOTH, expand=True
        )

        output_frame = ttk.LabelFrame(
            container, text="Output Folder", padding=8
        )
        output_frame.pack(fill=tk.X, pady=6)

        ttk.Entry(
            output_frame,
            textvariable=self.output_directory,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.folder_button = ttk.Button(
            output_frame,
            text="Browse",
            command=self._choose_output_folder,
        )
        self.folder_button.pack(
            side=tk.LEFT, padx=(6, 0)
        )

        action_frame = ttk.Frame(container)
        action_frame.pack(fill=tk.X, pady=6)

        self.start_button = ttk.Button(
            action_frame,
            text="Start Processing",
            command=self._start_processing,
        )
        self.start_button.pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(
            action_frame,
            mode="determinate",
            maximum=100,
        )
        self.progress.pack(
            side=tk.LEFT, fill=tk.X, expand=True,
            padx=10,
        )

        ttk.Label(
            container,
            textvariable=self.status_text,
        ).pack(anchor=tk.W, pady=(0, 6))

        result_frame = ttk.LabelFrame(
            container, text="Results", padding=6
        )
        result_frame.pack(fill=tk.BOTH, expand=True)

        self.result_list = tk.Listbox(
            result_frame, height=5
        )
        self.result_list.pack(
            fill=tk.BOTH, expand=True
        )

        history_button = ttk.Button(
            container,
            text="Refresh History",
            command=self._refresh_history,
        )
        history_button.pack(anchor=tk.E, pady=(6, 0))

    def _operation_changed(self, _event=None) -> None:
        """Enable page selection only for page extraction."""

        if self.operation.get() == "Extract PDF Pages":
            self.pages_entry.configure(state=tk.NORMAL)
        else:
            self.pages_entry.configure(state=tk.DISABLED)

    def _add_files(self) -> None:
        """Add selected input files without duplicates."""

        paths = filedialog.askopenfilenames(
            title="Select input files",
            filetypes=self.FILE_TYPES,
        )

        for value in paths:
            path = Path(value)

            if path not in self.input_paths:
                self.input_paths.append(path)
                self.file_list.insert(
                    tk.END, str(path)
                )

    def _remove_selected(self) -> None:
        """Remove selected input files."""

        indexes = list(self.file_list.curselection())

        for index in reversed(indexes):
            self.file_list.delete(index)
            del self.input_paths[index]

    def _clear_files(self) -> None:
        """Clear the input file list."""

        if self._running:
            return

        self.input_paths.clear()
        self.file_list.delete(0, tk.END)

    def _choose_output_folder(self) -> None:
        """Select the output directory."""

        folder = filedialog.askdirectory(
            title="Select output folder",
            initialdir=self.output_directory.get(),
        )

        if folder:
            self.output_directory.set(folder)

    def _start_processing(self) -> None:
        """Validate the request and start a worker thread."""

        if self._running:
            return

        if not self.input_paths:
            messagebox.showwarning(
                "No input files",
                "Please add at least one input file.",
            )
            return

        operation = self.OPERATIONS.get(
            self.operation.get()
        )
        if not operation:
            messagebox.showerror(
                "Invalid operation",
                "Select a supported operation.",
            )
            return

        output_directory = Path(
            self.output_directory.get()
        ).expanduser()

        if not output_directory.is_dir():
            messagebox.showerror(
                "Invalid output folder",
                "Select an existing output folder.",
            )
            return

        if operation == "extract_pages":
            if len(self.input_paths) != 1:
                messagebox.showerror(
                    "Select one PDF",
                    "Page extraction requires exactly one PDF.",
                )
                return

            if not self.page_selection.get().strip():
                messagebox.showerror(
                    "Missing page selection",
                    "Enter pages such as 1,3,5-7.",
                )
                return

        if operation == "merge_pdfs":
            if len(self.input_paths) < 2:
                messagebox.showerror(
                    "Insufficient files",
                    "Select at least two PDFs to merge.",
                )
                return

        self._running = True
        self._set_controls_enabled(False)
        self.progress["value"] = 0
        self.result_list.delete(0, tk.END)
        self.status_text.set("Processing files...")

        worker = threading.Thread(
            target=self._run_operation,
            args=(
                operation,
                list(self.input_paths),
                output_directory,
                self.page_selection.get().strip(),
            ),
            daemon=True,
        )
        worker.start()

    def _run_operation(
        self,
        operation: str,
        sources: list[Path],
        output_directory: Path,
        page_selection: str,
    ) -> None:
        """Run conversions off the UI thread."""

        try:
            if operation in {
                "docx_to_pdf",
                "pdf_to_docx",
                "docx_to_txt",
                "txt_to_docx",
            }:
                result = self.batch_service.process_batch(
                    sources,
                    operation,
                    output_directory,
                    progress_callback=lambda done, total, name:
                        self._messages.put(
                            ("progress", done, total, name)
                        ),
                )

                for item in result.results:
                    self.history_service.record_conversion(
                        item.operation,
                        item.input_path,
                        item.output_path,
                        item.success,
                        item.message,
                        item.error_details,
                    )
                    self._messages.put(
                        ("result", item.success,
                         item.input_path, item.output_path,
                         item.message, item.error_details)
                    )

                self._messages.put(
                    ("batch_complete",
                     result.successful_files,
                     result.failed_files,
                     result.total_files)
                )

            elif operation == "merge_pdfs":
                destination = output_directory / "merged.pdf"
                result = self.pdf_service.merge_pdfs(
                    sources, destination
                )
                self._record_pdf_result(
                    operation, sources, result
                )

            elif operation == "extract_pages":
                source = sources[0]
                destination = (
                    output_directory
                    / f"{source.stem}_extracted.pdf"
                )
                result = self.pdf_service.extract_pages(
                    source,
                    page_selection,
                    destination,
                )
                self._record_pdf_result(
                    operation, sources, result
                )

        except Exception as exc:
            self._messages.put(
                ("fatal_error", f"{type(exc).__name__}: {exc}")
            )

        finally:
            self._messages.put(("finished",))

    def _record_pdf_result(
        self,
        operation: str,
        sources: list[Path],
        result,
    ) -> None:
        """Record a merge or page extraction result."""

        source_text = "; ".join(str(path) for path in sources)

        self.history_service.record_conversion(
            operation,
            source_text,
            result.output_path,
            result.success,
            result.message,
            result.error_details,
        )

        self._messages.put(
            ("result", result.success,
             source_text, result.output_path,
             result.message, result.error_details)
        )

        self._messages.put(
            ("batch_complete",
             1 if result.success else 0,
             0 if result.success else 1,
             1)
        )

    def _process_messages(self) -> None:
        """Apply worker messages on the Tkinter main thread."""

        try:
            while True:
                message = self._messages.get_nowait()
                kind = message[0]

                if kind == "progress":
                    _, done, total, name = message
                    percentage = (
                        done / total * 100 if total else 0
                    )
                    self.progress["value"] = percentage
                    self.status_text.set(
                        f"Processing {name} ({done}/{total})"
                    )

                elif kind == "result":
                    (
                        _, success, source, destination,
                        text, details,
                    ) = message
                    status = "PASS" if success else "FAIL"
                    self.result_list.insert(
                        tk.END,
                        f"[{status}] {Path(source).name}: {text}",
                    )
                    if not success and details:
                        self.result_list.insert(
                            tk.END, f"    Details: {details}"
                        )

                elif kind == "batch_complete":
                    _, succeeded, failed, total = message
                    self.status_text.set(
                        f"Completed: {succeeded}/{total} successful; "
                        f"{failed} failed."
                    )
                    self.progress["value"] = 100

                elif kind == "fatal_error":
                    messagebox.showerror(
                        "Processing error", message[1]
                    )
                    self.status_text.set(
                        "Processing stopped due to an error."
                    )

                elif kind == "finished":
                    self._running = False
                    self._set_controls_enabled(True)
                    # Keep the just-completed results visible. History can
                    # be opened explicitly with the Refresh History button.

        except queue.Empty:
            pass

        self.root.after(100, self._process_messages)

    def _refresh_history(self) -> None:
        """Show the latest stored history in the results list."""

        if self._running:
            return

        try:
            records = self.history_service.get_recent_records(
                limit=10
            )
            self.result_list.delete(0, tk.END)
            self.result_list.insert(
                tk.END, "Recent conversion history:"
            )

            for record in records:
                self.result_list.insert(
                    tk.END,
                    f"[{record.status}] {record.timestamp} | "
                    f"{record.operation} | "
                    f"{Path(record.input_path).name} | "
                    f"{record.message}",
                )
                if record.error_details:
                    self.result_list.insert(
                        tk.END,
                        f"    Details: {record.error_details}",
                    )

        except Exception as exc:
            self.status_text.set(
                f"Could not load history: {exc}"
            )

    def _set_controls_enabled(self, enabled: bool) -> None:
        """Prevent conflicting UI actions during processing."""

        state = tk.NORMAL if enabled else tk.DISABLED

        self.start_button.configure(state=state)
        self.add_button.configure(state=state)
        self.remove_button.configure(state=state)
        self.clear_button.configure(state=state)
        self.folder_button.configure(state=state)
        self.operation_combo.configure(
            state="readonly" if enabled else tk.DISABLED
        )

        self.pages_entry.configure(
            state=(
                tk.NORMAL
                if enabled
                and self.operation.get() == "Extract PDF Pages"
                else tk.DISABLED
            )
        )

    def run(self) -> None:
        """Start the Tkinter event loop."""

        self.root.mainloop()


# Public interface
# Class: MainWindow
# Method: run()
# Responsibilities: UI, file selection, progress, results,
#   batch orchestration and history display.
# Dependencies: Tkinter, queue, threading, existing project services.
