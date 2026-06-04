import os
import sys
import shutil
import subprocess
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox
import winreg
import threading

# Dicionário de Idiomas
LANGUAGES = {
    'pt': {
        'title': 'PyCleaner Pro - Otimizador Dinâmico',
        'tab_disk': 'Limpeza de Disco',
        'tab_bloat': 'Bloatware & UWP',
        'tab_reg': 'Limpar Registro',
        'tab_tweaks': 'Desativar Ferramentas',
        'tab_about': 'Sobre',
        'btn_scan': 'Analisar e Limpar Disco',
        'btn_scan_apps': 'Escanear Apps UWP',
        'btn_remove_bloat': 'Remover Selecionados',
        'btn_scan_reg': 'Escanear Registro',
        'btn_clean_reg': 'Apagar Chaves Selecionadas',
        'btn_apply_tweaks': 'Aplicar Otimizações',
        'disk_chk_temp': 'Arquivos Temporários (%TEMP%)',
        'disk_chk_prefetch': 'Arquivos do Prefetch (Requer Admin)',
        'col_app_name': 'Nome do Aplicativo UWP / Bloatware',
        'col_reg_key': 'Local / Categoria',
        'col_reg_val': 'Valor do Registro',
        'tweak_telemetry': 'Desativar Telemetria e Coleta de Dados',
        'tweak_cortana_bg': 'Desativar Cortana em Segundo Plano',
        'status_ready': 'Pronto',
        'status_scanning': 'Escaneando o sistema... Por favor, aguarde.',
        'status_success': 'Operação concluída com sucesso!',
        'status_error': 'Erro: ',
        'admin_warn': 'Aviso: Execute como Administrador para acesso total.',
        'about_text': "PyCleaner v2.0 (Dynamic Edition)\n\nUtilitário de código aberto para limpeza personalizada do Windows.\n\nDesenvolvido por: Gregório Severiano (Dragoonie)\n\nLinguagem: Python + Tkinter"
    },
    'en': {
        'title': 'PyCleaner Pro - Dynamic Optimizer',
        'tab_disk': 'Disk Cleanup',
        'tab_bloat': 'Bloatware & UWP',
        'tab_reg': 'Clean Registry',
        'tab_tweaks': 'Disable Tools',
        'tab_about': 'About',
        'btn_scan': 'Analyze and Clean Disk',
        'btn_scan_apps': 'Scan UWP Apps',
        'btn_remove_bloat': 'Remove Selected',
        'btn_scan_reg': 'Scan Registry',
        'btn_clean_reg': 'Delete Selected Keys',
        'btn_apply_tweaks': 'Apply Tweaks',
        'disk_chk_temp': 'Temporary Files (%TEMP%)',
        'disk_chk_prefetch': 'Prefetch Files (Requires Admin)',
        'col_app_name': 'UWP Application / Bloatware Name',
        'col_reg_key': 'Location / Category',
        'col_reg_val': 'Registry Value',
        'tweak_telemetry': 'Disable Telemetry & Data Collection',
        'tweak_cortana_bg': 'Disable Cortana Background Processes',
        'status_ready': 'Ready',
        'status_scanning': 'Scanning system... Please wait.',
        'status_success': 'Operation completed successfully!',
        'status_error': 'Error: ',
        'admin_warn': 'Warning: Run as Administrator for full access.',
        'about_text': "PyCleaner v2.0 (Dynamic Edition)\n\nAn open-source utility for custom Windows optimization.\n\nDeveloped by: Gregório Severiano (Dragoonie)\n\nBuilt with Python and Tkinter"
    }
}

# Chaves seguras do registro para limpar histórico/MRU (Most Recently Used)
REG_TARGETS = [
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU", "Run Command History"),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths", "Explorer Typed Paths"),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs", "Recent Documents Log")
]

class PyCleanerApp:
    def __init__(self, root):
        self.root = root
        self.current_lang = 'pt'
        self.is_admin = self.check_admin()
        
        self.root.geometry("700x500")
        self.root.resizable(False, False)
        
        self.setup_ui()
        self.update_ui_text()

    def check_admin(self):
        try: return ctypes.windll.shell32.IsUserAnAdmin()
        except: return False

    def setup_ui(self):
        # Top Menu / Idioma
        lang_frame = ttk.Frame(self.root, padding=5)
        lang_frame.pack(fill='x')
        ttk.Label(lang_frame, text="Language:").pack(side='left', padx=5)
        self.lang_combo = ttk.Combobox(lang_frame, values=['Português', 'English'], state="readonly", width=12)
        self.lang_combo.current(0)
        self.lang_combo.bind("<<ComboboxSelected>>", self.change_language)
        self.lang_combo.pack(side='left', padx=5)
        
        if not self.is_admin:
            ttk.Label(lang_frame, text="⚠️ No Admin Mode", foreground="orange", font=("Arial", 9, "bold")).pack(side='right', padx=10)

        # Abas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.tab_disk = ttk.Frame(self.notebook, padding=10)
        self.tab_bloat = ttk.Frame(self.notebook, padding=10)
        self.tab_reg = ttk.Frame(self.notebook, padding=10)
        self.tab_tweaks = ttk.Frame(self.notebook, padding=10)
        self.tab_about = ttk.Frame(self.notebook, padding=10)
        
        self.notebook.add(self.tab_disk, text="")
        self.notebook.add(self.tab_bloat, text="")
        self.notebook.add(self.tab_reg, text="")
        self.notebook.add(self.tab_tweaks, text="")
        self.notebook.add(self.tab_about, text="")
        
        # --- TAB 1: DISK CLEANUP ---
        self.var_temp = tk.BooleanVar(value=True)
        self.var_prefetch = tk.BooleanVar(value=True)
        self.chk_temp = ttk.Checkbutton(self.tab_disk, variable=self.var_temp)
        self.chk_temp.pack(anchor='w', pady=5)
        self.chk_prefetch = ttk.Checkbutton(self.tab_disk, variable=self.var_prefetch)
        self.chk_prefetch.pack(anchor='w', pady=5)
        self.btn_disk = ttk.Button(self.tab_disk, command=self.run_disk_cleanup)
        self.btn_disk.pack(pady=20)
        
        # --- TAB 2: DYNAMIC BLOATWARE / UWP ---
        btn_frame_bloat = ttk.Frame(self.tab_bloat)
        btn_frame_bloat.pack(fill='x', pady=5)
        self.btn_scan_apps = ttk.Button(btn_frame_bloat, command=self.start_uwp_scan)
        self.btn_scan_apps.pack(side='left', padx=5)
        self.btn_remove_bloat = ttk.Button(btn_frame_bloat, command=self.remove_selected_apps, state='disabled')
        self.btn_remove_bloat.pack(side='left', padx=5)
        
        # Lista de exibição dos Apps (Multi-seleção via Ctrl ou Shift clicar)
        self.app_tree = ttk.Treeview(self.tab_bloat, columns=('Name'), show='headings', selectmode='extended')
        self.app_tree.pack(fill='both', expand=True, pady=5)
        scrollbar_app = ttk.Scrollbar(self.app_tree, orient="vertical", command=self.app_tree.yview)
        self.app_tree.configure(yscrollcommand=scrollbar_app.set)
        scrollbar_app.pack(side='right', fill='y')

        # --- TAB 3: DYNAMIC REGISTRY ---
        btn_frame_reg = ttk.Frame(self.tab_reg)
        btn_frame_reg.pack(fill='x', pady=5)
        self.btn_scan_reg = ttk.Button(btn_frame_reg, command=self.scan_registry)
        self.btn_scan_reg.pack(side='left', padx=5)
        self.btn_clean_reg = ttk.Button(btn_frame_reg, command=self.clean_selected_registry, state='disabled')
        self.btn_clean_reg.pack(side='left', padx=5)
        
        # Tabela do Registro
        self.reg_tree = ttk.Treeview(self.tab_reg, columns=('Category', 'ValueName'), show='headings', selectmode='extended')
        self.reg_tree.pack(fill='both', expand=True, pady=5)
        scrollbar_reg = ttk.Scrollbar(self.reg_tree, orient="vertical", command=self.reg_tree.yview)
        self.reg_tree.configure(yscrollcommand=scrollbar_reg.set)
        scrollbar_reg.pack(side='right', fill='y')

        # --- TAB 4: TWEAKS ---
        self.var_telemetry = tk.BooleanVar(value=True)
        self.var_cortana_bg = tk.BooleanVar(value=True)
        self.chk_telemetry = ttk.Checkbutton(self.tab_tweaks, variable=self.var_telemetry)
        self.chk_telemetry.pack(anchor='w', pady=5)
        self.chk_cortana_bg = ttk.Checkbutton(self.tab_tweaks, variable=self.var_cortana_bg)
        self.chk_cortana_bg.pack(anchor='w', pady=5)
        self.btn_tweaks = ttk.Button(self.tab_tweaks, command=self.run_tweaks)
        self.btn_tweaks.pack(pady=20)
        
        # --- TAB 5: ABOUT ---
        self.lbl_about = ttk.Label(self.tab_about, justify="center", font=("Arial", 11))
        self.lbl_about.pack(pady=50)
        
        # Status Bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief='sunken', anchor='w', padding=5)
        self.status_bar.pack(fill='x', side='bottom')

    def change_language(self, event):
        selection = self.lang_combo.get()
        self.current_lang = 'pt' if selection == 'Português' else 'en'
        self.update_ui_text()

    def update_ui_text(self):
        lang = LANGUAGES[self.current_lang]
        self.root.title(lang['title'])
        
        self.notebook.tab(0, text=lang['tab_disk'])
        self.notebook.tab(1, text=lang['tab_bloat'])
        self.notebook.tab(2, text=lang['tab_reg'])
        self.notebook.tab(3, text=lang['tab_tweaks'])
        self.notebook.tab(4, text=lang['tab_about'])
        
        self.chk_temp.config(text=lang['disk_chk_temp'])
        self.chk_prefetch.config(text=lang['disk_chk_prefetch'])
        self.btn_disk.config(text=lang['btn_scan'])
        
        self.btn_scan_apps.config(text=lang['btn_scan_apps'])
        self.btn_remove_bloat.config(text=lang['btn_remove_bloat'])
        self.app_tree.heading('Name', text=lang['col_app_name'])
        
        self.btn_scan_reg.config(text=lang['btn_scan_reg'])
        self.btn_clean_reg.config(text=lang['btn_clean_reg'])
        self.reg_tree.heading('Category', text=lang['col_reg_key'])
        self.reg_tree.heading('ValueName', text=lang['col_reg_val'])
        
        self.chk_telemetry.config(text=lang['tweak_telemetry'])
        self.chk_cortana_bg.config(text=lang['tweak_cortana_bg'])
        self.btn_tweaks.config(text=lang['btn_apply_tweaks'])
        
        self.lbl_about.config(text=lang['about_text'])
        self.status_var.set(lang['status_ready'] if self.is_admin else lang['admin_warn'])

    # --- LÓGICA DINÂMICA: ESCANEAR UWP (THREAD SEPARADA PARA NÃO TRAVAR A UI) ---
    def start_uwp_scan(self):
        lang = LANGUAGES[self.current_lang]
        self.status_var.set(lang['status_scanning'])
        self.btn_scan_apps.config(state='disabled')
        threading.Thread(target=self.scan_uwp_apps, daemon=True).start()

    def scan_uwp_apps(self):
        # Limpar registros antigos da tabela
        for item in self.app_tree.get_children():
            self.app_tree.delete(item)
            
        try:
            # Puxa dinamicamente via PowerShell todos os Apps instalados no escopo do usuário atual
            cmd = "Get-AppxPackage | Sort-Object Name | Select-Object -ExpandProperty Name"
            result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, shell=True)
            
            if result.stdout:
                apps = filter(None, result.stdout.split('\n'))
                for app in apps:
                    # Filtra frameworks vitais para evitar acidentes graves
                    if not any(x in app.lower() for x in ["vclibs", ".net", "framework", "nativeimages"]):
                        self.app_tree.insert('', 'end', values=(app.strip(),))
                        
            self.root.after(0, self.uwp_scan_complete)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"{str(e)}"))

    def uwp_scan_complete(self):
        lang = LANGUAGES[self.current_lang]
        self.btn_scan_apps.config(state='normal')
        self.btn_remove_bloat.config(state='normal')
        self.status_var.set(lang['status_ready'])

    def remove_selected_apps(self):
        lang = LANGUAGES[self.current_lang]
        selected_items = self.app_tree.selection()
        if not selected_items:
            return
            
        for item in selected_items:
            app_name = self.app_tree.item(item)['values'][0]
            # Desinstala dinamicamente o pacote selecionado
            cmd = f"Get-AppxPackage *{app_name}* | Remove-AppxPackage"
            subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, shell=True)
            self.app_tree.delete(item)
            
        self.status_var.set(lang['status_success'])
        messagebox.showinfo("PyCleaner", lang['status_success'])

    # --- LÓGICA DINÂMICA: VARRER REGISTRO ---
    def scan_registry(self):
        lang = LANGUAGES[self.current_lang]
        for item in self.reg_tree.get_children():
            self.reg_tree.delete(item)
            
        for root_key, subkey, category in REG_TARGETS:
            try:
                key = winreg.OpenKey(root_key, subkey, 0, winreg.KEY_READ)
                info = winreg.QueryInfoKey(key)
                for i in range(info[1]):
                    val_name, val_data, _ = winreg.EnumValue(key, i)
                    # Não exibir o marcador padrão/indexador do Windows
                    if val_name != "MRUList":
                        # Armazena metadados ocultos para deleção posterior
                        self.reg_tree.insert('', 'end', values=(category, f"{val_name} -> {str(val_data)[:40]}"), tags=(subkey, val_name))
                winreg.CloseKey(key)
            except WindowsError:
                pass # Chave inexistente ou sem permissão temporária
                
        self.btn_clean_reg.config(state='normal')
        self.status_var.set(lang['status_ready'])

    def clean_selected_registry(self):
        lang = LANGUAGES[self.current_lang]
        selected_items = self.reg_tree.selection()
        if not selected_items:
            return
            
        for item in selected_items:
            tags = self.reg_tree.item(item)['tags']
            subkey, val_name = tags[0], tags[1]
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey, 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(key, val_name)
                winreg.CloseKey(key)
                self.reg_tree.delete(item)
            except Exception as e:
                pass
                
        self.status_var.set(lang['status_success'])
        messagebox.showinfo("PyCleaner", lang['status_success'])

    # --- LIMPEZA DE DISCO & TWEAKS (ESTÁVEIS) ---
    def run_disk_cleanup(self):
        lang = LANGUAGES[self.current_lang]
        if self.var_temp.get():
            paths = [os.environ.get('TEMP'), os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp')]
            for p in paths:
                if p and os.path.exists(p):
                    for item in os.listdir(p):
                        try:
                            shutil.rmtree(os.path.join(p, item)) if os.path.isdir(os.path.join(p, item)) else os.remove(os.path.join(p, item))
                        except: pass
        if self.var_prefetch.get():
            p = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Prefetch')
            if os.path.exists(p):
                for item in os.listdir(p):
                    try: os.remove(os.path.join(p, item))
                    except: pass
        self.status_var.set(lang['status_success'])
        messagebox.showinfo("PyCleaner", lang['status_success'])

    def run_tweaks(self):
        lang = LANGUAGES[self.current_lang]
        try:
            if self.var_telemetry.get():
                subprocess.run(["sc", "stop", "DiagTrack"], capture_output=True)
                subprocess.run(["sc", "config", "DiagTrack", "start=", "disabled"], capture_output=True)
                k = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(k, "AllowTelemetry", 0, winreg.REG_DWORD, 0)
                winreg.CloseKey(k)
            if self.var_cortana_bg.get():
                k = winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\Windows Search", 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(k, "AllowCortana", 0, winreg.REG_DWORD, 0)
                winreg.CloseKey(k)
            self.status_var.set(lang['status_success'])
            messagebox.showinfo("PyCleaner", lang['status_success'])
        except Exception as e:
            messagebox.showerror("PyCleaner", f"{lang['status_error']} {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PyCleanerApp(root)
    root.mainloop()