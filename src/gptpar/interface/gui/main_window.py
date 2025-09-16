from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
import tkinter as tk
from tkinter import messagebox, ttk

from ...domain.models import Macro
from ...infrastructure.browser.selenium_driver_factory import create_firefox_driver
from ...infrastructure.browser.selenium_player import SeleniumMacroPlayer
from ...infrastructure.browser.selenium_recorder import SeleniumMacroRecorder
from ...infrastructure.storage.json_macro_repository import JsonMacroRepository
from ...usecases.delete_macro import DeleteMacro
from ...usecases.list_macros import ListMacros
from ...usecases.play_macro import PlayMacro
from ...usecases.start_recording import StartMacroRecording
from ...usecases.stop_recording import StopMacroRecording

LOGGER = logging.getLogger(__name__)


@dataclass
class AppConfiguration:
    storage_path: Path
    headless: bool = False
    firefox_binary: Optional[Path] = None


class AppDependencies:
    """Factory responsible for wiring dependencies according to Clean Architecture."""

    def __init__(self, config: Optional[AppConfiguration] = None) -> None:
        if config is None:
            config = AppConfiguration(storage_path=Path.home() / ".gptpar" / "macros.json")
        self._config = config

        repository = JsonMacroRepository(config.storage_path)
        recorder = SeleniumMacroRecorder(
            lambda: create_firefox_driver(headless=config.headless, firefox_binary=config.firefox_binary)
        )
        player = SeleniumMacroPlayer(
            lambda: create_firefox_driver(headless=config.headless, firefox_binary=config.firefox_binary)
        )

        self.start_recording = StartMacroRecording(recorder)
        self.stop_recording = StopMacroRecording(recorder, repository)
        self.list_macros = ListMacros(repository)
        self.play_macro = PlayMacro(repository, player)
        self.delete_macro = DeleteMacro(repository)


class MacroApp(tk.Tk):
    """Tkinter based graphical interface for GPTPar."""

    def __init__(self, dependencies: AppDependencies) -> None:
        super().__init__()
        self.title("GPTPar - Gravador de Macros Web")
        self.geometry("900x520")
        self.resizable(False, False)

        self._dependencies = dependencies
        self._is_recording = False
        self._selected_macro: Optional[str] = None

        self.url_var = tk.StringVar()
        self.macro_name_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Pronto para gravar")

        self._build_widgets()
        self._refresh_macro_list()

    # UI building -----------------------------------------------------

    def _build_widgets(self) -> None:
        header = ttk.Label(self, text="GPTPar", font=("Helvetica", 20, "bold"))
        header.pack(pady=(15, 5))

        description = ttk.Label(
            self,
            text=(
                "Grave suas interações no Firefox com o Selenium e reproduza-as sempre que precisar.\n"
                "1. Informe o endereço e o nome da macro. 2. Clique em Iniciar Gravação. 3. Execute suas ações.\n"
                "4. Clique em Finalizar para salvar o fluxo."
            ),
            justify=tk.CENTER,
        )
        description.pack(pady=(0, 15))

        form_frame = ttk.Frame(self)
        form_frame.pack(fill=tk.X, padx=20)

        ttk.Label(form_frame, text="Endereço (URL):").grid(row=0, column=0, sticky=tk.W, pady=5)
        url_entry = ttk.Entry(form_frame, textvariable=self.url_var, width=60)
        url_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        ttk.Label(form_frame, text="Nome da macro:").grid(row=1, column=0, sticky=tk.W, pady=5)
        macro_entry = ttk.Entry(form_frame, textvariable=self.macro_name_var, width=40)
        macro_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(fill=tk.X, padx=20, pady=(10, 5))

        self.start_button = ttk.Button(buttons_frame, text="Iniciar Gravação", command=self._start_recording)
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = ttk.Button(buttons_frame, text="Finalizar e Salvar", command=self._stop_recording, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5)

        self.play_button = ttk.Button(buttons_frame, text="Reproduzir Macro", command=self._play_macro)
        self.play_button.grid(row=0, column=2, padx=5)

        self.delete_button = ttk.Button(buttons_frame, text="Excluir Macro", command=self._delete_macro)
        self.delete_button.grid(row=0, column=3, padx=5)

        self.refresh_button = ttk.Button(buttons_frame, text="Atualizar Lista", command=self._refresh_macro_list)
        self.refresh_button.grid(row=0, column=4, padx=5)

        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        columns = ("macro", "url", "data")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        self.tree.heading("macro", text="Macro")
        self.tree.heading("url", text="URL")
        self.tree.heading("data", text="Data/Hora")
        self.tree.column("macro", width=200)
        self.tree.column("url", width=420)
        self.tree.column("data", width=180)
        self.tree.bind("<<TreeviewSelect>>", self._on_macro_select)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, padx=20, pady=(0, 10))

    # Actions ---------------------------------------------------------

    def _start_recording(self) -> None:
        if self._is_recording:
            return

        url = self.url_var.get().strip()
        macro_name = self.macro_name_var.get().strip()

        if not url:
            messagebox.showwarning("URL obrigatória", "Informe um endereço para iniciar a gravação.")
            return

        if not macro_name:
            messagebox.showwarning("Nome obrigatório", "Informe um nome para identificar a macro.")
            return

        self._update_status(f"Iniciando gravação em {url}...")
        self._toggle_recording_state(True)

        def task() -> None:
            try:
                self._dependencies.start_recording.execute(url)
                self._update_status_threadsafe("Gravação em andamento. Execute as ações no Firefox.")
            except Exception as exc:  # noqa: BLE001 - interface shows error to the user
                LOGGER.exception("Erro ao iniciar gravação")
                self._toggle_recording_state_threadsafe(False)
                self._show_error("Falha ao iniciar a gravação", str(exc))

        threading.Thread(target=task, daemon=True).start()

    def _stop_recording(self) -> None:
        if not self._is_recording:
            return

        macro_name = self.macro_name_var.get().strip()

        def task() -> None:
            try:
                macro = self._dependencies.stop_recording.execute(macro_name)
                self._toggle_recording_state_threadsafe(False)
                self._update_status_threadsafe(f"Macro '{macro.name}' salva com sucesso.")
                self._refresh_macro_list_threadsafe()
            except Exception as exc:  # noqa: BLE001
                LOGGER.exception("Erro ao finalizar gravação")
                self._toggle_recording_state_threadsafe(False)
                self._show_error("Falha ao finalizar a gravação", str(exc))

        threading.Thread(target=task, daemon=True).start()

    def _play_macro(self) -> None:
        macro_name = self._selected_macro
        if not macro_name:
            messagebox.showinfo("Selecione uma macro", "Escolha a macro desejada na lista antes de reproduzir.")
            return

        self._update_status(f"Reproduzindo macro '{macro_name}'...")

        def task() -> None:
            try:
                self._dependencies.play_macro.execute(macro_name)
                self._update_status_threadsafe(f"Macro '{macro_name}' executada com sucesso.")
            except Exception as exc:  # noqa: BLE001
                LOGGER.exception("Erro ao reproduzir macro")
                self._show_error("Falha na reprodução", str(exc))

        threading.Thread(target=task, daemon=True).start()

    def _delete_macro(self) -> None:
        macro_name = self._selected_macro
        if not macro_name:
            messagebox.showinfo("Selecione uma macro", "Escolha a macro que deseja excluir.")
            return

        if not messagebox.askyesno("Confirmação", f"Deseja realmente excluir a macro '{macro_name}'?"):
            return

        try:
            self._dependencies.delete_macro.execute(macro_name)
            self._update_status(f"Macro '{macro_name}' excluída.")
            self._refresh_macro_list()
        except Exception as exc:  # noqa: BLE001
            LOGGER.exception("Erro ao excluir macro")
            self._show_error("Falha ao excluir macro", str(exc))

    def _refresh_macro_list(self) -> None:
        macros = self._dependencies.list_macros.execute()
        self._populate_tree(macros)

    # Thread safe UI helpers -----------------------------------------

    def _toggle_recording_state(self, recording: bool) -> None:
        self._is_recording = recording
        self.start_button.config(state=tk.DISABLED if recording else tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL if recording else tk.DISABLED)
        self.play_button.config(state=tk.DISABLED if recording else tk.NORMAL)
        self.delete_button.config(state=tk.DISABLED if recording else tk.NORMAL)
        self.refresh_button.config(state=tk.DISABLED if recording else tk.NORMAL)

    def _toggle_recording_state_threadsafe(self, recording: bool) -> None:
        self.after(0, lambda: self._toggle_recording_state(recording))

    def _update_status(self, text: str) -> None:
        self.status_var.set(text)

    def _update_status_threadsafe(self, text: str) -> None:
        self.after(0, lambda: self._update_status(text))

    def _refresh_macro_list_threadsafe(self) -> None:
        self.after(0, self._refresh_macro_list)

    def _show_error(self, title: str, message: str) -> None:
        def _inner() -> None:
            messagebox.showerror(title, message)
            self._update_status("Ocorreu um erro. Verifique os detalhes e tente novamente.")

        self.after(0, _inner)

    def _populate_tree(self, macros: list[Macro]) -> None:
        self.tree.delete(*self.tree.get_children())
        for macro in macros:
            recorded_at = self._format_datetime(macro.recorded_at)
            self.tree.insert("", tk.END, iid=macro.name, values=(macro.name, macro.start_url, recorded_at))

    def _format_datetime(self, value: datetime) -> str:
        return value.astimezone().strftime("%d/%m/%Y %H:%M:%S")

    def _on_macro_select(self, event) -> None:  # noqa: ANN001 - Tkinter callback signature
        selection = self.tree.selection()
        if not selection:
            self._selected_macro = None
            return
        self._selected_macro = selection[0]
        self.macro_name_var.set(self._selected_macro)


def launch_app() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    dependencies = AppDependencies()
    app = MacroApp(dependencies)
    app.mainloop()
