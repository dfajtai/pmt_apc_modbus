import subprocess
import sys
from pathlib import Path

def find_pyside6_uic():
    """Megkeresi a pyside6-uic executable-t a venv-ben"""
    venv_bin = Path(sys.executable).parent  # .venv\Scripts
    
    candidates = [
        venv_bin / "pyside6-uic.exe",
        venv_bin / "pyside6-uic",
        venv_bin / "pyside6-uic-script.py",
        Path("pyside6-uic"),  # PATH-ból
    ]
    
    for candidate in candidates:
        if candidate.exists():
            print(f"✅ Found pyside6-uic: {candidate}")
            return str(candidate)
    
    # Utolsó esély: próbálja meg a PATH-ból
    try:
        subprocess.run(["pyside6-uic", "--version"], capture_output=True, check=True)
        print("✅ pyside6-uic found in PATH")
        return "pyside6-uic"
    except:
        pass
    
    raise FileNotFoundError(
        f"pyside6-uic not found!\n"
        f"Venv Scripts: {venv_bin}\n"
        f"Check: poetry add 'pyside6[tools]'"
    )

def build_ui(ui_path, py_path):
    """UI fájlt Pythonba fordít subprocess-szel"""
    ui = Path(ui_path).resolve()
    py = Path(py_path).resolve()
    
    print(f"📁 UI: {ui} (exists: {ui.exists()})")
    print(f"📁 PY: {py}")
    
    if not ui.exists():
        raise FileNotFoundError(f"UI file not found: {ui}")
    
    uic_exe = find_pyside6_uic()
    cmd = [uic_exe, str(ui), "-o", str(py)]
    
    print(f"🔨 Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
    except FileNotFoundError as e:
        print(f"❌ pyside6-uic not executable: {e}")
        return False
    except Exception as e:
        print(f"❌ UI compile exception: {e}")
        return False

    if result.returncode == 0:
        print(f"✅ UI compiled: {py}")
        return True
    else:
        print(f"❌ UI compile failed:\n{result.stderr}")
        return False

if __name__ == "__main__":
    script_dir = Path(__file__).parent
    
    # Abszolút utak a script mappájából
    build_ui(script_dir / "apc_main_window.ui", script_dir / "apc_main_window_ui.py")
    build_ui(script_dir / "channel_view_widget.ui", script_dir / "channel_view_widget_ui.py")
    
    print("🎉 All UIs compiled!")
