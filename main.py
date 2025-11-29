import json, subprocess, os, sys, re
import urllib.request

REGISTRY_URL = "https://raw.githubusercontent.com/yourusername/cpp-pip-registry/main/packages.json"
LIBS_DIR = "libs"
CMAKE_FILE = "CMakeLists.txt"

def load_registry():
    print("Fetching package registry...")
    with urllib.request.urlopen(REGISTRY_URL) as response:
        return json.load(response)

def get_main_target():
    if not os.path.exists(CMAKE_FILE):
        return None
    with open(CMAKE_FILE) as f:
        content = f.read()
    match = re.search(r"add_executable\s*\(\s*(\w+)", content)
    if match:
        return match.group(1)
    return None

def update_cmake(pkg_name):
    if not os.path.exists(CMAKE_FILE):
        print(f"{CMAKE_FILE} not found. Skipping CMake integration.")
        return
    target = get_main_target()
    if not target:
        print("Could not detect main CMake target. Please add manually.")
        return
    with open(CMAKE_FILE, "a") as f:
        f.write(f"\n# Added by cpp_pip\n")
        f.write(f"add_subdirectory({LIBS_DIR}/{pkg_name})\n")
        f.write(f"target_link_libraries({target} PRIVATE {pkg_name})\n")
    print(f"{pkg_name} linked to target '{target}' in {CMAKE_FILE}")

def install_package(pkg_name, packages):
    if pkg_name not in packages:
        print(f"Package '{pkg_name}' not found in registry.")
        return
    url = packages[pkg_name]['url']
    dest = os.path.join(LIBS_DIR, pkg_name)
    if os.path.exists(dest):
        print(f"{pkg_name} is already installed. Use 'update {pkg_name}' to refresh.")
        return
    os.makedirs(LIBS_DIR, exist_ok=True)
    print(f"Installing {pkg_name} from {url}...")
    subprocess.run(["git", "clone", url, dest])
    print(f"{pkg_name} installed in {dest}!")
    update_cmake(pkg_name)

def update_package(pkg_name):
    dest = os.path.join(LIBS_DIR, pkg_name)
    if not os.path.exists(dest):
        print(f"{pkg_name} is not installed. Use 'install {pkg_name}' first.")
        return
    print(f"Updating {pkg_name}...")
    subprocess.run(["git", "-C", dest, "pull"])
    print(f"{pkg_name} updated!")

def list_packages(packages):
    print("Available packages:")
    for name, info in packages.items():
        print(f"- {name}: {info.get('description', '')}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python cpp_pip.py [install|update|list] <package>")
        return

    command = sys.argv[1]
    packages = load_registry()

    if command == "install" and len(sys.argv) == 3:
        install_package(sys.argv[2], packages)
    elif command == "update" and len(sys.argv) == 3:
        update_package(sys.argv[2])
    elif command == "list":
        list_packages(packages)
    else:
        print("Invalid command or missing package name.")

if __name__ == "__main__":
    main()
