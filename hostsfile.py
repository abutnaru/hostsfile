#!/usr/bin/env pipenv-shebang

from __future__ import print_function, unicode_literals
from PyInquirer import prompt
from typing import List, Dict

import argparse
import os
import re
import subprocess
import sys


def argument_parser() -> None:
    parser = argparse.ArgumentParser(
                        prog = 'hostsfile',
                        description = 'Adds and remove hostsfile entries so you don\'t have to',
                        epilog = '')
    parser.add_argument('-a', '--add', type=str, nargs='*')
    parser.add_argument('-r', '--remove', type=str, nargs='*')
    args = parser.parse_args()

    hostsfile = Hosts()
    if type(args.add) == list:
        print("Add has been called")
        if len(args.add) == 0:
            hostsfile.insert()
        if len(args.add) == 2:
            if is_ip_address(args.add[0]):
                hostsfile.insert(domain=args.add[1], ip_addr=args.add[0], interactive=False)
            elif is_ip_address(args.add[1]):
                hostsfile.insert(domain=args.add[0], ip_addr=args.add[1], interactive=False)
            else:
                print("Input does not match expected format.\nThe arguments must be DOMAIN and IP_ADDR or vice-versa")
        if len(args.add) == 1 or len(args.add) > 2:
            print("Unexpected number of arguments.\nPlease use the -h or --help command check the example usage")

    if type(args.remove) == list:
        print("Remove has been called")
        if len(args.remove) == 0:
            hostsfile.remove()
        if len(args.remove) == 1:
            hostsfile.remove(args.remove[0], interactive=False)
        if len(args.remove) > 1:
            print("Unexpected number of arguments.\nPlease use the -h or --help command check the example usage")


def is_ip_address(ip_addr:str) -> bool:
    regex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"
    if(re.search(regex, ip_addr)):
        return True
    else:
        return False


class Hosts():
    ADDITION_MARKER = "#! Added through the hostsfile script"
    HOSTSFILE_PATH = "/etc/hosts"


    def __init__(self) -> None:
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
                # TODO: Check the validity of the IP address and domain
                hostsfile.write(f"{answer['ip_addr']}\t{answer['domain']}\t{self.ADDITION_MARKER}\n")
                print("Inserted")
        else:
            with open(self.HOSTSFILE_PATH, "a") as hostsfile:
                hostsfile.write(f"{ip_addr}\t{domain}\t{self.ADDITION_MARKER}\n")
                print("Inserted")


    def remove(self, marker="", interactive=True) -> None:
        options = self.read()
        if interactive:
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
            for answer in answers.values():
                for domain in answer:
                    if options[domain]["addition"] == "automatic":
                        marked_lines.append(options[domain]["line_no"])

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
        else: 
            marked_line = 9_999_999
            if is_ip_address(marker):
                for domain in options:
                    if options[domain]["ip_addr"] == marker:
                        marked_line = options[marker]["line_no"]
            else:
                print(options)
                marked_line = options[marker]["line_no"]


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


if __name__ == "__main__":
    argument_parser()


