import os
import sys
import shutil
import subprocess
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox
import winreg
import threading
import json

# Dicionário de Idiomas (Atualizado para refletir a detecção dinâmica)
LANGUAGES = {
    'pt': {
        'title': 'PyCleaner Pro - Otimizador Dinâmico',
        'tab_disk': 'Limpeza de Disco',
        'tab_bloat': 'Desinstalador & UWP',
        'tab_reg': 'Limpar Registro',
        'tab_tweaks': 'Ajustes do Sistema',
        'tab_about': 'Sobre',
        'btn_scan': 'Analisar e Limpar Disco',
        'btn_scan_apps': 'Escanear Apps UWP',
        'btn_scan_win32': 'Escanear Programas (Win32)',
        'btn_remove_bloat': 'Desinstalar Selecionados',
        'btn_scan_reg': 'Escanear Registro',
        'btn_clean_reg': 'Apagar Chaves Selecionadas',
        'btn_apply_tweaks': 'Aplicar Otimizações',
        'disk_frame_sys': 'Arquivos do Sistema',
        'disk_frame_browser': 'Navegadores Instalados',
        'disk_chk_temp': 'Arquivos Temporários (%TEMP%)',
        'disk_chk_prefetch': 'Arquivos do Prefetch (Requer Admin)',
        'disk_chk_browser_cache': 'Limpar Cache de Arquivos e Imagens',
        'disk_chk_browser_data': 'Limpar Histórico, Cookies e Logins (Atenção!)',
        'col_app_name': 'Nome do Aplicativo / Programa',
        'col_app_type': 'Tipo',
        'col_reg_key': 'Local / Categoria',
        'col_reg_val': 'Valor do Registro',
        'tweak_telemetry': 'Desativar Telemetria e Coleta de Dados',
        'tweak_cortana_bg': 'Desativar Cortana em Segundo Plano',
        'tweak_copilot': 'Desativar Windows Copilot (Win 11)',
        'tweak_websearch': 'Desativar Pesquisa Bing no Menu Iniciar',
        'tweak_edge_bg': 'Impedir Microsoft Edge em Segundo Plano',
        'status_ready': 'Pronto',
        'status_scanning': 'Escaneando o sistema... Por favor, aguarde.',
        'status_success': 'Operação concluída com sucesso!',
        'status_error': 'Erro: ',
        'admin_warn': 'Aviso: Execute como Administrador para acesso total.',
        'about_text': "PyCleaner v2.1 (Advanced Edition)\n\nUtilitário de código aberto para limpeza e otimização do Windows.\n\nDesenvolvido por: Gregório Severiano (Dragoonie)\n\nLinguagem: Python + Tkinter"
    },
    'en': {
        'title': 'PyCleaner Pro - Dynamic Optimizer',
        'tab_disk': 'Disk Cleanup',
        'tab_bloat': 'Uninstaller & UWP',
        'tab_reg': 'Clean Registry',
        'tab_tweaks': 'System Tweaks',
        'tab_about': 'About',
        'btn_scan': 'Analyze and Clean Disk',
        'btn_scan_apps': 'Scan UWP Apps',
        'btn_scan_win32': 'Scan Programs (Win32)',
        'btn_remove_bloat': 'Uninstall Selected',
        'btn_scan_reg': 'Scan Registry',
        'btn_clean_reg': 'Delete Selected Keys',
        'btn_apply_tweaks': 'Apply Tweaks',
        'disk_frame_sys': 'System Files',
        'disk_frame_browser': 'Installed Browsers',
        'disk_chk_temp': 'Temporary Files (%TEMP%)',
        'disk_chk_prefetch': 'Prefetch Files (Requires Admin)',
        'disk_chk_browser_cache': 'Clear Image and File Cache',
        'disk_chk_browser_data': 'Clear History, Cookies & Logins (Warning!)',
        'col_app_name': 'Application / Program Name',
        'col_app_type': 'Type',
        'col_reg_key': 'Location / Category',
        'col_reg_val': 'Registry Value',
        'tweak_telemetry': 'Disable Telemetry & Data Collection',
        'tweak_cortana_bg': 'Disable Cortana Background Processes',
        'tweak_copilot': 'Disable Windows Copilot (Win 11)',
        'tweak_websearch': 'Disable Bing Web Search in Start Menu',
        'tweak_edge_bg': 'Prevent Microsoft Edge Background Running',
        'status_ready': 'Ready',
        'status_scanning': 'Scanning system... Please wait.',
        'status_success': 'Operation completed successfully!',
        'status_error': 'Error: ',
        'admin_warn': 'Warning: Run as Administrator for full access.',
        'about_text': "PyCleaner v3.0 (Advanced Edition)\n\nAn open-source utility for custom Windows optimization.\n\nDeveloped by: Gregório Severiano (Dragoonie)\n\nBuilt with Python and Tkinter"
    }
}

# Expandido com mais alvos de MRU (Most Recently Used) e Históricos
REG_TARGETS = [
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU", "Run Command History"),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths", "Explorer Typed Paths"),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs", "Recent Documents Log"),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\OpenSavePidlMRU", "Open/Save Dialog History"),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\LastVisitedPidlMRU", "Last Visited Dialog History"),
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\WordWheelQuery", "Explorer Search History")
]

class PyCleanerApp:
    def __init__(self, root):
        self.root = root
        self.current_lang = 'pt'
        self.is_admin = self.check_admin()
        self.browser_vars = {} # Armazena os checkboxes dinâmicos dos navegadores
        
        self.root.geometry("800x600") # Altura levemente aumentada para acomodar a lista dinâmica
        self.root.resizable(False, False)
        
        self.setup_ui()
        self.update_ui_text()

    def check_admin(self):
        try: return ctypes.windll.shell32.IsUserAnAdmin()
        except: return False

    def get_installed_browsers(self):
        """Detecta quais navegadores estão realmente instalados no PC"""
        local = os.environ.get('LOCALAPPDATA', '')
        appdata = os.environ.get('APPDATA', '')
        browsers = {
            "Google Chrome": os.path.join(local, r"Google\Chrome\User Data"),
            "Microsoft Edge": os.path.join(local, r"Microsoft\Edge\User Data"),
            "Brave": os.path.join(local, r"BraveSoftware\Brave-Browser\User Data"),
            "Opera Stable": os.path.join(appdata, r"Opera Software\Opera Stable"),
            "Opera GX": os.path.join(local, r"Opera Software\Opera GX Stable"),
            "Firefox": os.path.join(appdata, r"Mozilla\Firefox\Profiles")
        }
        return {name: path for name, path in browsers.items() if os.path.exists(path)}

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
        
        # --- TAB 1: DISK CLEANUP (DINÂMICO) ---
        self.frame_sys = ttk.LabelFrame(self.tab_disk, padding=10)
        self.frame_sys.pack(fill='x', pady=5)
        
        self.var_temp = tk.BooleanVar(value=True)
        self.var_prefetch = tk.BooleanVar(value=True)
        self.chk_temp = ttk.Checkbutton(self.frame_sys, variable=self.var_temp)
        self.chk_temp.pack(anchor='w', pady=2)
        self.chk_prefetch = ttk.Checkbutton(self.frame_sys, variable=self.var_prefetch)
        self.chk_prefetch.pack(anchor='w', pady=2)
        
        self.frame_browsers = ttk.LabelFrame(self.tab_disk, padding=10)
        self.frame_browsers.pack(fill='x', pady=10)
        
        # Inserção dinâmica dos navegadores encontrados
        self.installed_browsers = self.get_installed_browsers()
        if self.installed_browsers:
            for name in self.installed_browsers:
                var = tk.BooleanVar(value=True) # Ativado por padrão
                self.browser_vars[name] = var
                ttk.Checkbutton(self.frame_browsers, text=name, variable=var).pack(anchor='w', pady=1)
        else:
            ttk.Label(self.frame_browsers, text="Nenhum navegador suportado encontrado.", font=("Arial", 8, "italic")).pack(anchor='w')

        ttk.Separator(self.frame_browsers, orient='horizontal').pack(fill='x', pady=(10, 5))
        
        self.var_browser_cache = tk.BooleanVar(value=True)
        self.var_browser_data = tk.BooleanVar(value=False)
        self.chk_browser_cache = ttk.Checkbutton(self.frame_browsers, variable=self.var_browser_cache)
        self.chk_browser_cache.pack(anchor='w', pady=2)
        self.chk_browser_data = ttk.Checkbutton(self.frame_browsers, variable=self.var_browser_data)
        self.chk_browser_data.pack(anchor='w', pady=2)

        self.btn_disk = ttk.Button(self.tab_disk, command=self.run_disk_cleanup)
        self.btn_disk.pack(pady=10)
        
        # --- TAB 2: UNIVERSAL UNINSTALLER ---
        btn_frame_bloat = ttk.Frame(self.tab_bloat)
        btn_frame_bloat.pack(fill='x', pady=5)
        
        self.btn_scan_apps = ttk.Button(btn_frame_bloat, command=lambda: self.start_app_scan("UWP"))
        self.btn_scan_apps.pack(side='left', padx=5)
        
        self.btn_scan_win32 = ttk.Button(btn_frame_bloat, command=lambda: self.start_app_scan("WIN32"))
        self.btn_scan_win32.pack(side='left', padx=5)
        
        self.btn_remove_bloat = ttk.Button(btn_frame_bloat, command=self.remove_selected_apps, state='disabled')
        self.btn_remove_bloat.pack(side='right', padx=5)
        
        self.app_tree = ttk.Treeview(self.tab_bloat, columns=('Name', 'Type', 'Command'), show='headings', selectmode='extended')
        self.app_tree.pack(fill='both', expand=True, pady=5)
        scrollbar_app = ttk.Scrollbar(self.app_tree, orient="vertical", command=self.app_tree.yview)
        self.app_tree.configure(yscrollcommand=scrollbar_app.set)
        scrollbar_app.pack(side='right', fill='y')
        
        self.app_tree.column('Type', width=80, stretch=tk.NO)
        self.app_tree.column('Command', width=0, stretch=tk.NO) 
        self.app_tree.heading('Type', text='Tipo')

        # --- TAB 3: DYNAMIC REGISTRY ---
        btn_frame_reg = ttk.Frame(self.tab_reg)
        btn_frame_reg.pack(fill='x', pady=5)
        self.btn_scan_reg = ttk.Button(btn_frame_reg, command=self.scan_registry)
        self.btn_scan_reg.pack(side='left', padx=5)
        self.btn_clean_reg = ttk.Button(btn_frame_reg, command=self.clean_selected_registry, state='disabled')
        self.btn_clean_reg.pack(side='left', padx=5)
        
        self.reg_tree = ttk.Treeview(self.tab_reg, columns=('Category', 'ValueName'), show='headings', selectmode='extended')
        self.reg_tree.pack(fill='both', expand=True, pady=5)
        scrollbar_reg = ttk.Scrollbar(self.reg_tree, orient="vertical", command=self.reg_tree.yview)
        self.reg_tree.configure(yscrollcommand=scrollbar_reg.set)
        scrollbar_reg.pack(side='right', fill='y')

        # --- TAB 4: TWEAKS ---
        self.var_telemetry = tk.BooleanVar(value=True)
        self.var_cortana_bg = tk.BooleanVar(value=True)
        self.var_copilot = tk.BooleanVar(value=False)
        self.var_websearch = tk.BooleanVar(value=False)
        self.var_edge_bg = tk.BooleanVar(value=False)
        
        ttk.Label(self.tab_tweaks, text="Geral:", font=("Arial", 9, "bold")).pack(anchor='w', pady=(5,0))
        self.chk_telemetry = ttk.Checkbutton(self.tab_tweaks, variable=self.var_telemetry)
        self.chk_telemetry.pack(anchor='w', pady=2, padx=10)
        self.chk_cortana_bg = ttk.Checkbutton(self.tab_tweaks, variable=self.var_cortana_bg)
        self.chk_cortana_bg.pack(anchor='w', pady=2, padx=10)
        
        ttk.Label(self.tab_tweaks, text="Windows 11 & Edge:", font=("Arial", 9, "bold")).pack(anchor='w', pady=(10,0))
        self.chk_copilot = ttk.Checkbutton(self.tab_tweaks, variable=self.var_copilot)
        self.chk_copilot.pack(anchor='w', pady=2, padx=10)
        self.chk_websearch = ttk.Checkbutton(self.tab_tweaks, variable=self.var_websearch)
        self.chk_websearch.pack(anchor='w', pady=2, padx=10)
        self.chk_edge_bg = ttk.Checkbutton(self.tab_tweaks, variable=self.var_edge_bg)
        self.chk_edge_bg.pack(anchor='w', pady=2, padx=10)
        
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
        
        self.frame_sys.config(text=lang['disk_frame_sys'])
        self.frame_browsers.config(text=lang['disk_frame_browser'])
        self.chk_temp.config(text=lang['disk_chk_temp'])
        self.chk_prefetch.config(text=lang['disk_chk_prefetch'])
        self.chk_browser_cache.config(text=lang['disk_chk_browser_cache'])
        self.chk_browser_data.config(text=lang['disk_chk_browser_data'])
        self.btn_disk.config(text=lang['btn_scan'])
        
        self.btn_scan_apps.config(text=lang['btn_scan_apps'])
        self.btn_scan_win32.config(text=lang['btn_scan_win32'])
        self.btn_remove_bloat.config(text=lang['btn_remove_bloat'])
        self.app_tree.heading('Name', text=lang['col_app_name'])
        self.app_tree.heading('Type', text=lang['col_app_type'])
        
        self.btn_scan_reg.config(text=lang['btn_scan_reg'])
        self.btn_clean_reg.config(text=lang['btn_clean_reg'])
        self.reg_tree.heading('Category', text=lang['col_reg_key'])
        self.reg_tree.heading('ValueName', text=lang['col_reg_val'])
        
        self.chk_telemetry.config(text=lang['tweak_telemetry'])
        self.chk_cortana_bg.config(text=lang['tweak_cortana_bg'])
        self.chk_copilot.config(text=lang['tweak_copilot'])
        self.chk_websearch.config(text=lang['tweak_websearch'])
        self.chk_edge_bg.config(text=lang['tweak_edge_bg'])
        self.btn_tweaks.config(text=lang['btn_apply_tweaks'])
        
        self.lbl_about.config(text=lang['about_text'])
        self.status_var.set(lang['status_ready'] if self.is_admin else lang['admin_warn'])

    # --- LÓGICA DINÂMICA: ESCANEAR UWP / WIN32 ---
    def start_app_scan(self, scan_type):
        lang = LANGUAGES[self.current_lang]
        self.status_var.set(lang['status_scanning'])
        self.btn_scan_apps.config(state='disabled')
        self.btn_scan_win32.config(state='disabled')
        threading.Thread(target=self.scan_apps_thread, args=(scan_type,), daemon=True).start()

    def scan_apps_thread(self, scan_type):
        for item in self.app_tree.get_children():
            self.app_tree.delete(item)
            
        try:
            if scan_type == "UWP":
                cmd = "Get-AppxPackage | Sort-Object Name | Select-Object -ExpandProperty Name"
                result = subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, text=True, shell=True)
                if result.stdout:
                    apps = filter(None, result.stdout.split('\n'))
                    for app in apps:
                        if not any(x in app.lower() for x in ["vclibs", ".net", "framework", "nativeimages"]):
                            self.app_tree.insert('', 'end', values=(app.strip(), 'UWP', app.strip()))
            
            elif scan_type == "WIN32":
                paths = [
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall")
                ]
                
                win32_apps = []
                for root_key, path in paths:
                    try:
                        key = winreg.OpenKey(root_key, path, 0, winreg.KEY_READ)
                        num_subkeys = winreg.QueryInfoKey(key)[0]
                        
                        for i in range(num_subkeys):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                subkey = winreg.OpenKey(key, subkey_name)
                                try:
                                    display_name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                                    uninstall_string, _ = winreg.QueryValueEx(subkey, "UninstallString")
                                    
                                    if display_name and uninstall_string:
                                        if not any(app[0] == display_name for app in win32_apps):
                                            win32_apps.append((display_name, 'Win32', uninstall_string))
                                except OSError: pass 
                                finally: winreg.CloseKey(subkey)
                            except OSError: pass
                        winreg.CloseKey(key)
                    except OSError: pass
                
                win32_apps.sort(key=lambda x: x[0].lower())
                for app in win32_apps:
                    self.app_tree.insert('', 'end', values=app)

            self.root.after(0, self.app_scan_complete)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Falha na varredura: {str(e)}"))

    def app_scan_complete(self):
        lang = LANGUAGES[self.current_lang]
        self.btn_scan_apps.config(state='normal')
        self.btn_scan_win32.config(state='normal')
        self.btn_remove_bloat.config(state='normal')
        self.status_var.set(lang['status_ready'])

    def remove_selected_apps(self):
        lang = LANGUAGES[self.current_lang]
        selected_items = self.app_tree.selection()
        if not selected_items: return
            
        for item in selected_items:
            values = self.app_tree.item(item)['values']
            app_name, app_type, command = values[0], values[1], values[2]
            
            if app_type == 'UWP':
                cmd = f"Get-AppxPackage *{command}* | Remove-AppxPackage"
                subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True, shell=True)
                self.app_tree.delete(item)
            elif app_type == 'Win32':
                try:
                    subprocess.Popen(command, shell=True)
                    self.app_tree.delete(item)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to run uninstaller for {app_name}: {str(e)}")
            
        self.status_var.set(lang['status_success'])

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
                    if val_name not in ["MRUList", "MRUListEx"]:
                        self.reg_tree.insert('', 'end', values=(category, f"{val_name} -> {str(val_data)[:40]}"), tags=(subkey, val_name))
                winreg.CloseKey(key)
            except WindowsError: pass
                
        self.btn_clean_reg.config(state='normal')
        self.status_var.set(lang['status_ready'])

    def clean_selected_registry(self):
        lang = LANGUAGES[self.current_lang]
        selected_items = self.reg_tree.selection()
        if not selected_items: return
            
        for item in selected_items:
            tags = self.reg_tree.item(item)['tags']
            subkey, val_name = tags[0], tags[1]
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey, 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(key, val_name)
                winreg.CloseKey(key)
                self.reg_tree.delete(item)
            except Exception: pass
                
        self.status_var.set(lang['status_success'])
        messagebox.showinfo("PyCleaner", lang['status_success'])

    # --- NOVA FUNÇÃO: LIMPEZA DE NAVEGADORES (DINÂMICA INTEGRADA) ---
    def clean_browsers(self):
        clear_cache = self.var_browser_cache.get()
        clear_data = self.var_browser_data.get()
        
        if not clear_cache and not clear_data:
            return

        cache_targets = ['Cache', 'Code Cache', 'GPUCache', 'CacheStorage', r'Network\Cache']
        data_targets = ['History', 'Cookies', 'Web Data', r'Network\Cookies', 'Login Data']
        
        for name, base_path in self.installed_browsers.items():
            # Pula o navegador se o usuário não marcou o checkbox dele
            if not self.browser_vars.get(name, tk.BooleanVar()).get():
                continue
                
            if name == "Firefox":
                # Limpeza Firefox
                local_app_data = os.environ.get('LOCALAPPDATA', '')
                ff_local = os.path.join(local_app_data, r"Mozilla\Firefox\Profiles") if local_app_data else ""
                ff_roaming = base_path # A raiz retornada por get_installed_browsers para o FF
                
                if clear_cache and os.path.exists(ff_local):
                    for profile in os.listdir(ff_local):
                        target = os.path.join(ff_local, profile, 'cache2')
                        if os.path.exists(target):
                            try: shutil.rmtree(target, ignore_errors=True)
                            except: pass
                            
                if clear_data and os.path.exists(ff_roaming):
                    for profile in os.listdir(ff_roaming):
                        # Mantendo a segurança original: "places.sqlite" (Favoritos) é evitado de propósito.
                        for file in ['cookies.sqlite', 'formhistory.sqlite', 'downloads.sqlite', 'webappsstore.sqlite']:
                            target = os.path.join(ff_roaming, profile, file)
                            if os.path.exists(target):
                                try: os.remove(target)
                                except: pass
            else:
                # Limpeza Família Chromium e Opera
                if not os.path.exists(base_path): continue
                
                profiles = ['Default', ''] + [d for d in os.listdir(base_path) if d.startswith('Profile')]
                
                for profile in set(profiles):
                    profile_path = os.path.join(base_path, profile)
                    if not os.path.exists(profile_path): continue
                    
                    if clear_cache:
                        for folder in cache_targets:
                            target = os.path.join(profile_path, folder)
                            if os.path.exists(target):
                                try: shutil.rmtree(target, ignore_errors=True)
                                except: pass
                                
                    if clear_data:
                        for file in data_targets:
                            target = os.path.join(profile_path, file)
                            if os.path.exists(target):
                                try: os.remove(target)
                                except: pass

    # --- LIMPEZA DE DISCO & TWEAKS ---
    def run_disk_cleanup(self):
        lang = LANGUAGES[self.current_lang]
        
        # Limpa o Windows
        if self.var_temp.get():
            paths = [os.environ.get('TEMP'), os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp')]
            for p in paths:
                if p and os.path.exists(p):
                    for item in os.listdir(p):
                        try:
                            item_path = os.path.join(p, item)
                            shutil.rmtree(item_path) if os.path.isdir(item_path) else os.remove(item_path)
                        except: pass
        if self.var_prefetch.get():
            p = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Prefetch')
            if os.path.exists(p):
                for item in os.listdir(p):
                    try: os.remove(os.path.join(p, item))
                    except: pass
                    
        # Aciona o módulo de limpeza dinâmica dos Navegadores
        self.clean_browsers()
        
        self.status_var.set(lang['status_success'])
        messagebox.showinfo("PyCleaner", lang['status_success'])

    def run_tweaks(self):
        lang = LANGUAGES[self.current_lang]
        try:
            def set_reg(root, path, name, val, val_type=winreg.REG_DWORD):
                try:
                    k = winreg.CreateKeyEx(root, path, 0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(k, name, 0, val_type, val)
                    winreg.CloseKey(k)
                except Exception as e:
                    print(f"Failed to set {name}: {e}")

            if self.var_telemetry.get():
                subprocess.run(["sc", "stop", "DiagTrack"], capture_output=True)
                subprocess.run(["sc", "config", "DiagTrack", "start=", "disabled"], capture_output=True)
                set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "AllowTelemetry", 0)
            
            if self.var_cortana_bg.get():
                set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\Windows Search", "AllowCortana", 0)

            if self.var_copilot.get():
                set_reg(winreg.HKEY_CURRENT_USER, r"Software\Policies\Microsoft\Windows\WindowsCopilot", "TurnOffWindowsCopilot", 1)

            if self.var_websearch.get():
                set_reg(winreg.HKEY_CURRENT_USER, r"Software\Policies\Microsoft\Windows\Explorer", "DisableSearchBoxSuggestions", 1)
                
            if self.var_edge_bg.get():
                set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Edge", "BackgroundModeEnabled", 0)
                set_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Edge", "StartupBoostEnabled", 0)

            self.status_var.set(lang['status_success'])
            messagebox.showinfo("PyCleaner", lang['status_success'])
        except Exception as e:
            messagebox.showerror("PyCleaner", f"{lang['status_error']} {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PyCleanerApp(root)
    root.mainloop()