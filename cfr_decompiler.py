import os
import sys
import shutil
import zipfile
import tempfile
import subprocess
from pathlib import Path
from typing import Union
import stat 

cfr_path = "cfr-0.152.jar"

class CFRDecompiler:
    def __init__(self, cfr_jar_path: Union[str, Path]):
        self.cfr_jar_path = Path(cfr_jar_path)
        if not self.cfr_jar_path.exists():
            raise FileNotFoundError(f"CFR jar not found at: {self.cfr_jar_path}")

    def _run_cfr(self, jar_path: Path, output_dir: Path) -> None:
        print(f"[*] Running CFR for {jar_path.name}...")
        command = [
            "java", "-jar", str(self.cfr_jar_path),
            str(jar_path),
            "--outputdir", str(output_dir),
            "--silent", "true"
        ]
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            print(f"[!] Decompilation error: {e.stderr.decode('utf-8', errors='ignore')}")
            raise

    def _remove_class_files(self, directory: Path) -> None:
        for path in directory.rglob('*.class'):
            try:
                os.chmod(path, stat.S_IWRITE)
                path.unlink()
            except Exception as e:
                print(f"[!] Could not remove file: {path.name}. Error: {e}")

    def _extract_jar_contents(self, jar_path: Path, extract_dir: Path) -> None:
        try:
            with zipfile.ZipFile(jar_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        except Exception as e:
            print(f"[!] Extraction warning: {e}")

    def mode_1_inplace(self, jar_path: Union[str, Path]) -> None:
        jar_path = Path(jar_path)
        print(f"[*] Mode 1: Updating {jar_path.name}...")

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            self._extract_jar_contents(jar_path, tmp_path)
            self._run_cfr(jar_path, tmp_path)
            self._remove_class_files(tmp_path)
            
            with zipfile.ZipFile(jar_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in tmp_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(tmp_path)
                        zipf.write(file_path, arcname)
                        
        print(f"[+] Done! {jar_path.name} updated with sources.")

    def mode_2_to_folder(self, jar_path: Union[str, Path], output_folder: Union[str, Path]) -> None:
        jar_path = Path(jar_path)
        output_dir = Path(output_folder)
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"[*] Mode 2: Exporting to {output_dir.name}...")
        self._extract_jar_contents(jar_path, output_dir)
        self._run_cfr(jar_path, output_dir)
        self._remove_class_files(output_dir)
        print(f"[+] Done! Files saved to '{output_dir}'.")

    def mode_3_gradle_project(self, jar_path: Union[str, Path], project_dir: Union[str, Path]) -> None:
        jar_path = Path(jar_path)
        proj_dir = Path(project_dir)
        java_dir = proj_dir / "src" / "main" / "java"
        res_dir = proj_dir / "src" / "main" / "resources"
        
        java_dir.mkdir(parents=True, exist_ok=True)
        res_dir.mkdir(parents=True, exist_ok=True)

        print(f"[*] Mode 3: Creating Gradle project in {proj_dir.name}...")
        self._run_cfr(jar_path, java_dir)

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            self._extract_jar_contents(jar_path, tmp_path)
            self._remove_class_files(tmp_path)
            
            for root, _, files in os.walk(tmp_path):
                for file in files:
                    src_file = Path(root) / file
                    rel_path = src_file.relative_to(tmp_path)
                    dst_file = res_dir / rel_path
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dst_file)

        build_gradle_content = "plugins {\n    id 'java'\n}\ngroup = 'com.decompiled'\nversion = '1.0-SNAPSHOT'\nrepositories {\n    mavenCentral()\n}\n"
        with open(proj_dir / "build.gradle", "w", encoding="utf-8") as f:
            f.write(build_gradle_content)

        print(f"[+] Done! Project ready at '{proj_dir}'.")

def interactive_mode():
    print("=== JAR Decompiler Helper ===")
    jar_path = input("Target .jar path: ").strip()

    if not os.path.isfile(cfr_path):
        print("[-] Error: CFR jar not found.")
        sys.exit(1)
    if not os.path.isfile(jar_path):
        print("[-] Error: Target jar not found.")
        sys.exit(1)

    try:
        decompiler = CFRDecompiler(cfr_path)
    except Exception as e:
        print(f"[-] {e}")
        sys.exit(1)

    print("\nAvailable modes:")
    print("1 - Inplace (replace .class with .java inside jar)")
    print("2 - Unpack all (sources + resources to folder)")
    print("3 - IDE Ready (create Gradle project structure)")
    
    mode = input("\nSelect mode (1/2/3): ").strip()

    if mode == '1':
        decompiler.mode_1_inplace(jar_path)
    elif mode == '2':
        out_folder = input("Output folder name: ").strip() or f"{Path(jar_path).stem}_extracted"
        decompiler.mode_2_to_folder(jar_path, out_folder)
    elif mode == '3':
        out_folder = input("Project folder name: ").strip() or f"{Path(jar_path).stem}_project"
        decompiler.mode_3_gradle_project(jar_path, out_folder)
    else:
        print("[-] Unknown mode. Exiting.")

if __name__ == "__main__":
    try:
        interactive_mode()
    except KeyboardInterrupt:
        print("\n[*] Aborted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[!] Unexpected error: {e}")
        sys.exit(1)