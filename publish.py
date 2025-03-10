#!/usr/bin/env python3
"""
This script publishes your Python gitguru project as a .deb package for system-wide installation.
It assumes:
  • The Python app is located in the 'app' directory
  • A remote APT repository tree is stored on your VM at /home/rgw/Apps/frontend-sites/files.ryangerardwilson.com/gitguru
  • Requirements are generated dynamically based on app imports without strict versioning
  • Run this script in a virtual environment where dependencies (e.g., packaging) are installed
  • The resulting gitguru binary will be installed to /usr/bin/gitguru via APT

All published files will be placed under:
  /home/rgw/Apps/frontend-sites/files.ryangerardwilson.com/gitguru

SSH details are read from ~/.rgwfuncsrc under the preset "icdattcwsm".
"""
import os
import subprocess
import shutil
import json
import re
from packaging.version import parse as parse_version
import tempfile
import ast
import sys
import importlib.util

# Optionally force a new major version (set to an integer, e.g., 1) or leave as None
MAJOR_RELEASE_NUMBER = 0

###############################################################################
# UTILITY TO FIND IMPORTED PACKAGES
###############################################################################


def get_imported_packages(directory):
    """Recursively find all imported packages in Python files within a directory."""
    imported_packages = set()

    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".py"):
                filepath = os.path.join(root, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    try:
                        tree = ast.parse(f.read(), filename=filepath)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for name in node.names:
                                    pkg = name.name.split(".")[0]
                                    imported_packages.add(pkg)
                            elif isinstance(node, ast.ImportFrom):
                                if node.module:
                                    pkg = node.module.split(".")[0]
                                    imported_packages.add(pkg)
                    except SyntaxError:
                        print(f"[WARNING] Syntax error in {filepath}, skipping...")
                        continue

    stdlib = set(sys.stdlib_module_names)
    return {pkg for pkg in imported_packages if pkg not in stdlib and not pkg.startswith(".")}

###############################################################################
# FILTER EXTERNAL PACKAGES
###############################################################################


def filter_external_packages(packages, app_dir):
    """Filter out internal modules and keep only external packages."""
    external_pkgs = set()
    internal_modules = {'modules'}

    for pkg in packages:
        if pkg in internal_modules:
            continue

        pkg_path = os.path.join(app_dir, pkg)
        if os.path.exists(pkg_path + ".py") or os.path.isdir(pkg_path):
            continue

        spec = importlib.util.find_spec(pkg)
        if spec and spec.origin and "site-packages" in spec.origin:
            external_pkgs.add(pkg)

    return external_pkgs

###############################################################################
# GENERATE LEAN REQUIREMENTS.TXT
###############################################################################


def generate_lean_requirements(app_dir, output_path):
    """Generate a lean requirements.txt with only external package names."""
    imported_pkgs = get_imported_packages(app_dir)
    print(f"[INFO] Detected imported packages: {imported_pkgs}")

    external_pkgs = filter_external_packages(imported_pkgs, app_dir)
    print(f"[INFO] Filtered external packages: {external_pkgs}")

    with open(output_path, "w", encoding="utf-8") as f:
        for pkg in sorted(external_pkgs):
            f.write(f"{pkg}\n")
    print(f"[INFO] Generated lean requirements.txt at {output_path} with {len(external_pkgs)} packages")

###############################################################################
# UPDATE VERSION IN constants.py
###############################################################################


def update_config_version(new_version):
    config_path = os.path.join("app", "modules", "constants.py")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"constants.py not found at {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        contents = f.read()

    updated_contents = re.sub(
        r'VERSION\s*=\s*"[^"]*"',
        f'VERSION = "{new_version}"',
        contents
    )

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(updated_contents)
    print(f"[INFO] Updated constants.py version to: {new_version}")

###############################################################################
# GET NEW VERSION
###############################################################################


def get_new_version(MAJOR_RELEASE_NUMBER=None):
    config_path = os.path.expanduser("~/.rgwfuncsrc")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Cannot find config file: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    vm_presets = data.get("vm_presets", [])
    preset = next((p for p in vm_presets if p.get("name") == "icdattcwsm"), None)
    if not preset:
        raise ValueError("No preset named 'icdattcwsm' found in ~/.rgwfuncsrc")
    host = preset["host"]
    ssh_user = preset["ssh_user"]
    ssh_key_path = preset["ssh_key_path"]

    remote_deb_dir = "/home/rgw/Apps/frontend-sites/files.ryangerardwilson.com/gitguru/debian/dists/stable/main/binary-amd64"
    ssh_cmd = (
        f"ssh -i {ssh_key_path} {ssh_user}@{host} "
        f"\"find {remote_deb_dir} -maxdepth 1 -type f -name 'gitguru_*.deb'\""
    )
    try:
        output = subprocess.check_output(ssh_cmd, shell=True).decode("utf-8").strip()
    except subprocess.CalledProcessError:
        output = ""

    print(f"[DEBUG] SSH command output:\n{output}")

    if not output:
        new_major = int(MAJOR_RELEASE_NUMBER) if MAJOR_RELEASE_NUMBER is not None else 0
        new_version = f"{new_major}.0.1-1"
        print(f"[INFO] No existing .deb found remotely – using initial version {new_version}")
        return new_version

    deb_file_path = output.split("\n")[-1].strip()
    filename = os.path.basename(deb_file_path)

    match = re.match(r"^gitguru_(\d+\.\d+\.\d+)(?:-(\d+))?_amd64\.deb$", filename)
    if not match:
        raise ValueError(f"Could not parse version from deb file name: {filename}")

    version_str = match.group(1)
    revision_str = match.group(2) if match.group(2) is not None else "1"

    major_str, minor_str, patch_str = version_str.split(".")
    server_major = int(major_str)
    server_minor = int(minor_str)
    server_patch = int(patch_str)
    server_revision = int(revision_str)

    if MAJOR_RELEASE_NUMBER is None:
        new_major = server_major
        new_minor = server_minor
        new_patch = server_patch + 1
        new_revision = server_revision
    else:
        user_major = int(MAJOR_RELEASE_NUMBER)
        if user_major == server_major:
            new_major = server_major
            new_minor = server_minor
            new_patch = server_patch + 1
            new_revision = server_revision
        else:
            new_major = user_major
            new_minor = 0
            new_patch = 1
            new_revision = 1

    new_version = f"{new_major}.{new_minor}.{new_patch}-{new_revision}"
    print(f"[INFO] Computed new version: {new_version}")
    return new_version

###############################################################################
# REMOVE OLD REMOTE DEBS
###############################################################################


def remove_old_remote_debs():
    config_path = os.path.expanduser("~/.rgwfuncsrc")
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    vm_presets = data.get("vm_presets", [])
    preset = next((p for p in vm_presets if p.get("name") == "icdattcwsm"), None)
    if not preset:
        raise ValueError("No preset named 'icdattcwsm' found in ~/.rgwfuncsrc")
    host = preset["host"]
    ssh_user = preset["ssh_user"]
    ssh_key_path = preset["ssh_key_path"]
    remote_deb_dir = "/home/rgw/Apps/frontend-sites/files.ryangerardwilson.com/gitguru/debian/dists/stable/main/binary-amd64"

    ssh_cmd = (
        f"ssh -i {ssh_key_path} {ssh_user}@{host} "
        f"\"[ -d {remote_deb_dir} ] && rm -f {remote_deb_dir}/gitguru_*.deb || echo 'Directory does not exist, skipping removal'\""
    )
    print("[INFO] Attempting to remove remote .deb files if directory exists...")
    try:
        output = subprocess.check_output(ssh_cmd, shell=True).decode("utf-8").strip()
        if output:
            print(f"[INFO] Remote output: {output}")
        else:
            print("[INFO] Removed all remote .deb files or none existed.")
    except subprocess.CalledProcessError as e:
        print(f"[WARNING] Failed to execute removal command: {e.output.decode('utf-8')}")

###############################################################################
# PUBLISH RELEASE
###############################################################################


def publish_release(version):
    def build_deb(version):
        print("[INFO] Starting build_deb step…")
        update_config_version(version)

        build_root = os.path.join("debian", "version_build_folders", f"gitguru_{version}")
        if os.path.exists(build_root):
            shutil.rmtree(build_root)
        os.makedirs(build_root, exist_ok=True)

        out_debs_dir = os.path.join("debian", "version_debs")
        os.makedirs(out_debs_dir, exist_ok=True)

        debian_dir = os.path.join(build_root, "DEBIAN")
        os.makedirs(debian_dir, exist_ok=True)

        control_content = f"""Package: gitguru
Version: {version}
Section: utils
Priority: optional
Architecture: amd64
Depends: python3 (>= 3.6), python3-pip
Maintainer: Your Name <ryangerardwilson@gmail.com>
Description: GitGuru - A Git branch management tool
 GitGuru is a command-line tool for managing Git branches with a structured naming convention.
"""
        control_path = os.path.join(debian_dir, "control")
        with open(control_path, "w", encoding="utf-8") as f:
            f.write(control_content)
        print(f"[INFO] Created control file at {control_path}")

        usr_bin_dir = os.path.join(build_root, "usr", "bin")
        usr_lib_dir = os.path.join(build_root, "usr", "lib", "gitguru")
        os.makedirs(usr_bin_dir, exist_ok=True)
        os.makedirs(usr_lib_dir, exist_ok=True)

        shutil.copytree("app", os.path.join(usr_lib_dir, "app"), dirs_exist_ok=True)
        print(f"[INFO] Copied app directory to {usr_lib_dir}")

        bin_script = os.path.join(usr_bin_dir, "gitguru")
        script_content = """#!/bin/bash
PYTHONPATH=/usr/lib/gitguru/site-packages python3 /usr/lib/gitguru/app/main.py "$@"
"""
        with open(bin_script, "w", encoding="utf-8") as f:
            f.write(script_content)
        os.chmod(bin_script, 0o755)
        print(f"[INFO] Created executable script at {bin_script}")

        requirements_path = os.path.join("app", "requirements.txt")
        generate_lean_requirements("app", requirements_path)

        pip_cmd = [
            "pip3", "install", "-r", requirements_path,
            "--target", os.path.join(usr_lib_dir, "site-packages"),
            "--no-deps"
        ]
        try:
            subprocess.check_call(pip_cmd)
            print(f"[INFO] Installed dependencies to {usr_lib_dir}/site-packages")
            print(f"[DEBUG] Site-packages contents: {os.listdir(os.path.join(usr_lib_dir, 'site-packages'))}")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to install dependencies: {e}")
            raise

        output_deb = os.path.join(out_debs_dir, f"gitguru_{version}_amd64.deb")
        subprocess.check_call(["dpkg-deb", "--build", build_root, output_deb])
        print(f"[INFO] Built new .deb: {output_deb}")

    def prepare_deb_for_distribution(version):
        print("[INFO] Starting prepare_deb_for_distribution step…")
        stable_dir = os.path.join("debian", "dists", "stable")
        if os.path.exists(stable_dir):
            shutil.rmtree(stable_dir)
        apt_binary_dir = os.path.join(stable_dir, "main", "binary-amd64")
        os.makedirs(apt_binary_dir, exist_ok=True)

        overrides_path = os.path.join(apt_binary_dir, "overrides.txt")
        if not os.path.exists(overrides_path):
            with open(overrides_path, "w", encoding="utf-8") as f:
                f.write("gitguru optional utils\n")
        print(f"[INFO] Verified overrides.txt at {overrides_path}")

        deb_source = os.path.join("debian", "version_debs", f"gitguru_{version}_amd64.deb")
        if not os.path.exists(deb_source):
            raise FileNotFoundError(f"{deb_source} not found.")
        shutil.copy2(deb_source, apt_binary_dir)
        print(f"[INFO] Copied {deb_source} into {apt_binary_dir}")

        packages_path = os.path.join(apt_binary_dir, "Packages")
        pkg_cmd = ["dpkg-scanpackages", "--multiversion", ".", "overrides.txt"]
        with open(packages_path, "w", encoding="utf-8") as f:
            subprocess.check_call(pkg_cmd, cwd=apt_binary_dir, stdout=f)
        print(f"[INFO] Created Packages file at {packages_path}")

        new_lines = []
        prefix = "dists/stable/main/binary-amd64/"
        with open(packages_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("Filename: ./"):
                    line = line.replace("Filename: ./", f"Filename: {prefix}")
                new_lines.append(line)
        with open(packages_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print("[INFO] Adjusted Filename entries in Packages file.")

        packages_gz_path = os.path.join(apt_binary_dir, "Packages.gz")
        with open(packages_gz_path, "wb") as f_out:
            subprocess.check_call(["gzip", "-9c", "Packages"], cwd=apt_binary_dir, stdout=f_out)
        print(f"[INFO] Created {packages_gz_path}")

        apt_ftppath = os.path.join(stable_dir, "apt-ftparchive.conf")
        conf_content = """APT::FTPArchive::Release {
  Origin "gitguruRepo";
  Label "gitguruRepo";
  Suite "stable";
  Codename "stable";
  Architectures "amd64";
  Components "main";
};
"""
        with open(apt_ftppath, "w", encoding="utf-8") as f:
            f.write(conf_content)

        release_path = os.path.join(stable_dir, "Release")
        apt_ftparchive_cmd = ["apt-ftparchive", "-c", "apt-ftparchive.conf", "release", "."]
        with open(release_path, "w", encoding="utf-8") as rf:
            subprocess.check_call(apt_ftparchive_cmd, cwd=stable_dir, stdout=rf)
        print(f"[INFO] Created Release file at {release_path}")

        sign_cmd = [
            "gpg", "--local-user", "172E2D67FB733C7EB47DEA047FE8FD47C68DC85A",
            "--detach-sign", "--armor", "--output", "Release.gpg", "Release"
        ]
        subprocess.check_call(sign_cmd, cwd=stable_dir)
        print("[INFO] Signed Release file (Release.gpg created).")

    def push_to_server():
        print("[INFO] Starting push_to_server step…")
        funcs_path = os.path.expanduser("~/.rgwfuncsrc")
        with open(funcs_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        vm_presets = data.get("vm_presets", [])
        preset = next((p for p in vm_presets if p.get("name") == "icdattcwsm"), None)
        host = preset["host"]
        ssh_user = preset["ssh_user"]
        ssh_key_path = preset["ssh_key_path"]
        remote_path = "/home/rgw/Apps/frontend-sites/files.ryangerardwilson.com/gitguru"

        ssh_cmd = f"ssh -i {ssh_key_path} {ssh_user}@{host} 'rm -rf {remote_path}/debian'"
        subprocess.check_call(ssh_cmd, shell=True)

        rsync_cmd = (
            f"rsync -avz -e 'ssh -i {ssh_key_path}' "
            "--exclude 'version_build_folders' --exclude 'version_debs' "
            f"debian/ {ssh_user}@{host}:{remote_path}/debian"
        )
        subprocess.check_call(rsync_cmd, shell=True)
        print("[INFO] push_to_server completed successfully.")

    def delete_all_but_last_version_build_folders():
        build_folders_path = os.path.join("debian", "version_build_folders")
        if not os.path.exists(build_folders_path):
            return
        version_folders = [f for f in os.listdir(build_folders_path)
                           if os.path.isdir(os.path.join(build_folders_path, f)) and f.startswith("gitguru_")]
        version_folders.sort(key=lambda x: parse_version(x.split('_')[1]), reverse=True)
        for folder in version_folders[1:]:
            folder_path = os.path.join(build_folders_path, folder)
            print(f"[INFO] Deleting old build folder: {folder_path}")
            shutil.rmtree(folder_path)

    def delete_all_but_last_version_debs():
        debs_dir = os.path.join("debian", "version_debs")
        if not os.path.exists(debs_dir):
            return
        deb_files = [f for f in os.listdir(debs_dir)
                     if os.path.isfile(os.path.join(debs_dir, f)) and f.endswith(".deb")]
        deb_files.sort(key=lambda x: parse_version(x.split('_')[1].replace("_amd64.deb", "")), reverse=True)
        for deb in deb_files[1:]:
            deb_path = os.path.join(debs_dir, deb)
            print(f"[INFO] Deleting old .deb file: {deb_path}")
            os.remove(deb_path)

    build_deb(version)
    prepare_deb_for_distribution(version)
    remove_old_remote_debs()
    push_to_server()
    delete_all_but_last_version_build_folders()
    delete_all_but_last_version_debs()
    print("[INFO] publish_release completed successfully.")

###############################################################################
# PUBLISH INSTALL SCRIPT
###############################################################################


def publish_install_script():
    install_sh_contents = """#!/bin/bash
# This installation script configures the gitguru repository and installs it system-wide
# Run with: bash -c "sh <(curl -fsSL https://files.ryangerardwilson.com/gitguru/install.sh)"
set -e

# Import apt repository key and save it to /usr/share/keyrings/gitguru.gpg
curl -fsSL https://files.ryangerardwilson.com/gitguru/debian/pubkey.gpg | sudo gpg --dearmor -o /usr/share/keyrings/gitguru.gpg

# Add gitguru repository to your system sources list
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/gitguru.gpg] https://files.ryangerardwilson.com/gitguru/debian stable main" | sudo tee /etc/apt/sources.list.d/gitguru.list

# Update apt and install the gitguru package
sudo apt update
sudo apt-get install gitguru

echo "Installation complete. GitGuru is now available at /usr/bin/gitguru."
"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmpfile:
        tmpfile.write(install_sh_contents)
        local_install_script = tmpfile.name

    print("[INFO] Temporary install.sh written to:", local_install_script)

    local_pubkey = "/home/rgw/Documents/credentials/pubkey.gpg"

    funcs_path = os.path.expanduser("~/.rgwfuncsrc")
    with open(funcs_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    vm_presets = data.get("vm_presets", [])
    preset = next((p for p in vm_presets if p.get("name") == "icdattcwsm"), None)
    if not preset:
        raise ValueError("No preset named 'icdattcwsm' found in ~/.rgwfuncsrc")
    host = preset["host"]
    ssh_user = preset["ssh_user"]
    ssh_key_path = preset["ssh_key_path"]

    remote_base_path = "/home/rgw/Apps/frontend-sites/files.ryangerardwilson.com/gitguru"
    remote_install_path = f"{remote_base_path}/install.sh"
    remote_debian_path = f"{remote_base_path}/debian"

    # Ensure remote debian directory exists
    ssh_cmd = f"ssh -i {ssh_key_path} {ssh_user}@{host} 'mkdir -p {remote_debian_path}'"
    subprocess.check_call(ssh_cmd, shell=True)

    # Upload install.sh
    rsync_cmd = (
        f"rsync -avz -e 'ssh -i {ssh_key_path}' {local_install_script} {ssh_user}@{host}:{remote_install_path}"
    )
    subprocess.check_call(rsync_cmd, shell=True)

    # Upload pubkey.gpg
    rsync_cmd_pubkey = (
        f"rsync -avz -e 'ssh -i {ssh_key_path}' {local_pubkey} {ssh_user}@{host}:{remote_debian_path}/pubkey.gpg"
    )
    try:
        subprocess.check_call(rsync_cmd_pubkey, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to upload pubkey.gpg: {e}")
        raise

    # Set permissions
    chmod_cmd = f"ssh -i {ssh_key_path} {ssh_user}@{host} 'chmod 644 {remote_install_path} {remote_debian_path}/pubkey.gpg'"
    subprocess.check_call(chmod_cmd, shell=True)

    os.remove(local_install_script)
    print(f"[INFO] install.sh and pubkey.gpg published to {remote_base_path} with permissions 644")


def main():
    new_version = get_new_version(MAJOR_RELEASE_NUMBER)
    publish_release(new_version)
    publish_install_script()


if __name__ == "__main__":
    main()
