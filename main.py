import json, subprocess, os, sys, re, urllib.request, urllib.error

# --- Configuration ---
REGISTRY_URL = "https://raw.githubusercontent.com/Aleksander-Sapieha/Pylib/main/libs.json"
LIBS_DIR = "libs"
CMAKE_FILE = "CMakeLists.txt"

# --- Helper functions ---

def fetch_url(url):
    """Fetch content from a URL, handle redirects and decode properly"""
    try:
        with urllib.request.urlopen(url) as response:
            return response.read().decode("utf-8")
    except urllib.error.URLError as e:
        print(f"Error fetching URL: {e}")
        sys.exit(1)

def load_registry():
    """Load the JSON registry from remote URL"""
    print("Fetching remote registry...")
    text = fetch_url(REGISTRY_URL)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print("Failed to parse JSON from registry. Here's the content fetched:")
        print(text[:500])  # print first 500 chars
        sys.exit(1)

def get_main_target():
    """Try to detect the main target from CMakeLists.txt"""
    if not os.path.exists(CMAKE_FILE):
        return None
    with open(CMAKE_FILE) as f:
        content = f.read()
    match = re.search(r"add_executable\s*\(\s*(\w+)", content)
    if match:
        return match.group(1)
    return None

def update_cmake(pkg_name):
    """Add the library to CMakeLists.txt automatically"""
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

def install_package(pkg_name, version="latest", packages=None, installed=None):
    """Install a package (and dependencies)"""
    if installed is None:
        installed = set()
    if pkg_name in installed:
        return
    if pkg_name not in packages:
        print(f"Package '{pkg_name}' not found in registry.")
        return

    info = packages[pkg_name]
    # Install dependencies first
    for dep in info.get("dependencies", []):
        install_package(dep, "latest", packages, installed)

    url = info['url']
    versions = info.get("versions", {})
    commit = versions.get(version, versions.get("latest", "master"))
    dest = os.path.join(LIBS_DIR, pkg_name)

    if os.path.exists(dest):
        print(f"{pkg_name} already installed. Pulling latest changes...")
        subprocess.run(["git", "-C", dest, "pull"])
        subprocess.run(["git", "-C", dest, "checkout", commit])
    else:
        os.makedirs(LIBS_DIR, exist_ok=True)
        print(f"Installing {pkg_name} ({commit}) from {url}...")
        subprocess.run(["git", "clone", url, dest])
        subprocess.run(["git", "-C", dest, "checkout", commit])

    update_cmake(pkg_name)
    installed.add(pkg_name)

def list_packages(packages):
    print("Available packages:")
    for name, info in packages.items():
        desc = info.get("description", "")
        versions = ", ".join(info.get("versions", {}).keys())
        deps = ", ".join(info.get("dependencies", []))
        dep_str = f" (depends on: {deps})" if deps else ""
        print(f"- {name}: {desc} (versions: {versions}){dep_str}")

# --- Main CLI ---

def main():
    if len(sys.argv) < 2:
        print("Usage: python cpp_pip.py [install|list] <package> [version]")
        return

    command = sys.argv[1]
    packages = load_registry()

    if command == "install" and len(sys.argv) >= 3:
        pkg_name = sys.argv[2]
        version = sys.argv[3] if len(sys.argv) >= 4 else "latest"
        install_package(pkg_name, version, packages)
    elif command == "list":
        list_packages(packages)
    else:
        print("Invalid command.")

if __name__ == "__main__":
    main()
