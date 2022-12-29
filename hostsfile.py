#!/usr/bin/env pipenv-shebang

from __future__ import print_function, unicode_literals
from PyInquirer import prompt
from typing import List, Dict
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
        """
        Check if the script is ran with administrator privilleges and elevate
        if it's not
        """
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
                    hosts[components[1]] = {
                        "ip_addr": components[0],
                        "line_no": line_no,
                        "addition": "automatic" if "#!" in line else "manual",
                    }
        return hosts


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

            with open(self.HOSTSFILE_PATH, "a") as hostsfile:
                hostsfile.write(f"{answer['ip_addr']}\t{answer['domain']}\t{self.ADDITION_MARKER}\n")
                self.console.print("Insertion details:\n", style="bold green")
                self.console.print(f"Domain name: [b]{answer['domain']}[/b]\nIP Address: {answer['ip_addr']}")
        else:
            with open(self.HOSTSFILE_PATH, "a") as hostsfile:
                hostsfile.write(f"{ip_addr}\t{domain}\t{self.ADDITION_MARKER}\n")
                self.console.print("Insertion details:\n", style="bold green")
                self.console.print(f"Domain name: [b]{domain}[/b]\nIP Address: {ip_addr}")


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
            marked_domains = []
            for answer in answers.values():
                for domain in answer:
                    if options[domain]["addition"] == "automatic":
                        marked_lines.append(options[domain]["line_no"])
                        marked_domains.append((domain, options[domain]["ip_addr"]))

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
            self.console.print("Removal details:\n", style="bold green")
            for pair in marked_domains:
                self.console.print(f"Domain names: [b]{pair[0]}[/b]\nIP Address: {pair[1]}")
        elif options: 
            marked_line = 9_999_999
            marked_domain = ("","")
            if is_ip_address(marker):
                for domain in options:
                    if options[domain]["ip_addr"] == marker:
                        marked_line = options[marker]["line_no"]
                        marked_domain = (domain, options[marker]["ip_addr"])
            else:
                marked_line = options[marker]["line_no"]
                marked_domain = (marker, options[marker]["ip_addr"])

            with open(self.HOSTSFILE_PATH,'r') as read_file:
                lines = read_file.readlines()

            current_line = 1
            with open(self.HOSTSFILE_PATH,'w') as write_file:
                for line in lines:
                    if current_line != marked_line:
                        write_file.write(line)
                    else:
                        pass
                    current_line += 1
            self.console.print("Removal details:\n", style="bold green")
            self.console.print(f"Domain names: [b]{marked_domain[0]}[/b]\nIP Address: {marked_domain[1]}")
        else:
            self.console.print("No custom entries found")


    def clean(self):
        marked_lines = [ domain["line_no"] for domain in self.read().values() ]
        marked_domains = [ domain for domain in self.read().keys() ]
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
        self.console.print(f"Deleted entries: {marked_domains}")


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


