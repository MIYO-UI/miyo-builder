import os
import json
import argparse
import subprocess
import requests
from pathlib import Path

FLATPAK_MANIFEST_TEMPLATE = {
    "app-id": "org.example.App",
    "runtime": "org.gnome.Sdk",
    "runtime-version": "45",
    "sdk": "org.gnome.Sdk",
    "command": "myapp",
    "finish-args": ["--share=network", "--socket=wayland"],
    "modules": []
}

class FlatpakBuilder:
    def __init__(self, repo_url):
        self.repo_url = repo_url
        self.repo_name = repo_url.split("/")[-1]
        self.manifest = FLATPAK_MANIFEST_TEMPLATE.copy()
        self.work_dir = Path(f"build-{self.repo_name}")
        
    def _detect_project_type(self):
        try:
            response = requests.get(f"{self.repo_url}/contents/")
            files = [f['name'] for f in response.json()]
            
            if 'CMakeLists.txt' in files:
                return 'cmake'
            if 'package.json' in files:
                return 'nodejs'
            if 'setup.py' in files:
                return 'python'
            return 'autotools'
            
        except Exception as e:
            print(f"Error detecting project type: {e}")
            return 'generic'

    def _create_build_module(self):
        project_type = self._detect_project_type()
        module = {
            "name": self.repo_name,
            "buildsystem": project_type,
            "sources": [{
                "type": "git",
                "url": self.repo_url,
                "branch": "main"
            }]
        }
        
        if project_type == 'cmake':
            module["config-opts"] = ["-DCMAKE_INSTALL_PREFIX=/app"]
        elif project_type == 'nodejs':
            module["build-commands"] = ["npm install", "npm run build"]
        elif project_type == 'python':
            module["build-commands"] = ["python3 -m pip install ."]
            
        return module

    def _add_python_dependencies(self):
        try:
            response = requests.get(f"{self.repo_url}/contents/requirements.txt")
            content = response.json()['content']
            requirements = base64.b64decode(content).decode('utf-8').splitlines()
            
            pip_module = {
                "name": "python-pip",
                "buildsystem": "simple",
                "build-commands": [
                    "python3 -m pip install --prefix=/app " + " ".join(requirements)
                ]
            }
            self.manifest["modules"].insert(0, pip_module)
            
        except Exception as e:
            print(f"Couldn't find Python requirements: {e}")

    def generate_manifest(self):
        main_module = self._create_build_module()
        self.manifest["app-id"] = f"org.{self.repo_name}.App"
        self.manifest["command"] = self.repo_name.lower()
        self.manifest["modules"].append(main_module)
        
        if self._detect_project_type() == 'python':
            self._add_python_dependencies()

        manifest_path = self.work_dir / f"{self.repo_name}.json"
        with open(manifest_path, 'w') as f:
            json.dump(self.manifest, f, indent=2)
            
        return manifest_path

    def build(self):
        self.work_dir.mkdir(exist_ok=True)
        manifest_path = self.generate_manifest()
        
        build_cmd = [
            "flatpak-builder",
            "--force-clean",
            "--repo=myrepo",
            "--user",
            "build-dir",
            str(manifest_path)
        ]
        
        try:
            subprocess.run(build_cmd, check=True)
            print("\nSuccessfully built Flatpak package!")
            print(f"Install with: flatpak --user install myrepo {self.manifest['app-id']}")
        except subprocess.CalledProcessError as e:
            print(f"Build failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="Auto Flatpak Builder for GitHub Projects")
    parser.add_argument("repo_url", help="GitHub repository URL")
    args = parser.parse_args()
    
    builder = FlatpakBuilder(args.repo_url)
    builder.build()

if __name__ == "__main__":
    main()