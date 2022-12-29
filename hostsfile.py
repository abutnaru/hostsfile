#!/usr/bin/env pipenv-shebang

from __future__ import print_function, unicode_literals
from PyInquirer import prompt
from typing import List,Dict
from rich.console import Console

import argparse
import os
import re
import subprocess
import sys


class Hosts():
    ADDITION_MARKER = "#! Added through the hostsfile script"
    HOSTSFILE_PATH = "/etc/hosts"


    def __init__(self, console: Console) -> None:
        self.console = console
        self.__privilege_escalation__()


    def __privilege_escalation__(self) -> None:
        if os.geteuid() != 0:
            subprocess.call(['sudo', 'python3', *sys.argv])
            sys.exit()


    def read(self) -> Dict:
        hosts = {}
        line_no = 0
        with open(self.HOSTSFILE_PATH, "r") as hostsfile:
            for line in hostsfile.readlines():
                line_no+=1
                if re.search("(?:[0-9]{1,3}\\.){3}[0-9]{1,3}", line) and "#!" in line:
                    components = re.split("\\s", line)
                    hosts[components[1]] = { "ip_addr": components[0], "line_no": line_no }
        return hosts


    def append_to_file(self, ip_addr: str, domain: str) -> None:
        with open(self.HOSTSFILE_PATH, "a") as hostsfile:
            hostsfile.write(f"{ip_addr}\t{domain}\t{self.ADDITION_MARKER}\n")
        self.console.print("\nInsertion details:", style="bold green")
        self.console.print(f"Domain name: [b]{domain}[/b]\nIP Address: {ip_addr}")


    def remove_from_file(self, marked_lines: List, removal_info: List) -> None:
        with open(self.HOSTSFILE_PATH,'r') as read_file:
            lines = read_file.readlines()
        current_line = 1
        with open(self.HOSTSFILE_PATH,'w') as write_file:
            for line in lines:
                if current_line not in marked_lines:
                    write_file.write(line)
                else:
                    pass
                current_line += 1
        self.console.print("\nRemoval details:", style="bold green")
        self.console.print(f"Domain names: [b]{[i['domain'] for i in removal_info]}[/b]")
        self.console.print(f"IP Address: {[i['ip_addr'] for i in removal_info ]}")
            

    def insert(self, domain="", ip_addr="", interactive=True) -> None:
        if interactive:
            questions = [
                {
                    'type': 'input',
                    'name': 'domain',
                    'message': 'Domain Name',
                },
                {
                    'type': 'input',
                    'name': 'ip_addr',
                    'message': 'IP Address',
                    'validate': is_ip_address
                },
            ]
            answer = prompt(questions)
            self.append_to_file(answer['ip_addr'], answer['domain'])
        else:
            self.append_to_file(ip_addr, domain)


    def remove(self, marker="", interactive=True) -> None:
        options = self.read()
        if interactive and options:
            questions = [
                {
                    'type': 'checkbox',
                    'name': 'domains',
                    'message': 'Select entries to remove',
                    'choices': [{"name": domain} for domain in options.keys()]
                },
            ]
            answers = prompt(questions)

            marked_lines = []
            removal_info = []
            for answer in answers.values():
                for domain in answer:
                    marked_lines.append(options[domain]["line_no"])
                    removal_info.append({"domain":domain, "ip_addr": options[domain]["ip_addr"]})
            self.remove_from_file(marked_lines, removal_info)

        elif options: 
            marked_lines = []
            domain = ""
            ip_addr = ""
            if is_ip_address(marker):
                for domain in options:
                    if options[domain]["ip_addr"] == marker:
                        marked_lines = [options[marker]["line_no"]]
                        (domain, ip_addr) = (domain, options[marker]["ip_addr"])
            else:
                marked_lines = [options[marker]["line_no"]]
                (domain, ip_addr) = (marker, options[marker]["ip_addr"])

            self.remove_from_file(marked_lines, [{"domain": domain, "ip_addr": ip_addr}])

        else:
            self.console.print("No custom entries found", style="bold yellow")


    def clean(self):
        domains = self.read()
        marked_lines = [ domain["line_no"] for domain in self.read().values() ]
        removal_info = []
        for domain in domains:
            removal_info.append({"domain": domain, "ip_addr": domains[domain]["ip_addr"]})
            
        self.remove_from_file(marked_lines,removal_info)


def is_ip_address(ip_addr:str) -> bool:
    regex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
    if(re.search(regex, ip_addr)):
        return True
    else:
        return False


if __name__ == "__main__":
    console = Console()
    parser = argparse.ArgumentParser(
                        prog = 'hostsfile',
                        description = 'Adds and remove hostsfile entries so you don\'t have to',
                        epilog = '')
    parser.add_argument('-a', '--add', type=str, nargs='*', help="Domain and IP address combo to add")
    parser.add_argument('-r', '--remove', type=str, nargs='*', help="Domain or IP address to remove")
    parser.add_argument('-c', '--clean', action="store_true", help="Remove all hostfile additions")

    args = parser.parse_args()

    hostsfile = Hosts(console)
    if args.clean:
        hostsfile.clean()

    if type(args.add) == list:
        if len(args.add) == 0:
            hostsfile.insert()
        if len(args.add) == 2:
            if is_ip_address(args.add[0]):
                hostsfile.insert(domain=args.add[1], ip_addr=args.add[0], interactive=False)
            elif is_ip_address(args.add[1]):
                hostsfile.insert(domain=args.add[0], ip_addr=args.add[1], interactive=False)
            else:
                console.print("\nInput does not match expected formatself.\nThe arguments must be DOMAIN and IP_ADDR or vice-versa", style="bold red")
                parser.print_help()
        if len(args.add) == 1 or len(args.add) > 2:
            console.print(f"\nUnexpected number of arguments ({len(args.add)})", style="bold red")
            parser.print_help()

    if type(args.remove) == list:
        if len(args.remove) == 0:
            hostsfile.remove()
        if len(args.remove) == 1:
            hostsfile.remove(args.remove[0], interactive=False)
        if len(args.remove) > 1:
            console.print(f"\nUnexpected number of arguments ({len(args.add)})", style="bold red")
            parser.print_help()


