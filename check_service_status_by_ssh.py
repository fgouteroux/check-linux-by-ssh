#!/usr/bin/env python2

# Copyright (C) 2015-:
#     Gabes Jean, naparuba@gmail.com
#     Pasche Sebastien, sebastien.pasche@leshop.ch
#     Francois Gouteroux, francois.gouteroux@gmail.com 
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#

import os
import sys
import optparse
import base64

# Ok try to load our directory to load the plugin utils.
my_dir = os.path.dirname(__file__)
sys.path.insert(0, my_dir)

try:
    import schecks
except ImportError:
    print "ERROR : this plugin needs the local schecks.py lib. Please install it"
    sys.exit(2)


VERSION = "0.1"


def get_service_status(client, service_name, custom_cmd, custom_search):

    # Beware of the export!
    if custom_cmd:
        _, stdout, stderr = client.exec_command(custom_cmd)
    else:
        _, stdout, stderr = client.exec_command("service {0} status".format(service_name))
    
    result = dict()
    result_stdout = "" 

    for line in stdout:
        line = line.strip()
        if custom_cmd:
            if not line or not custom_search in line:
                continue
        else:
            if not line or not ("pid" in line or line.startswith(service_name)): 
                continue
        result_stdout += line + "\n"
        result["stdout"] = result_stdout.strip()

    for line in stderr:
        result["stderr"] = line.strip()

    # Before return, close the client
    client.close()

    return result





parser = optparse.OptionParser(
    "%prog [options]", version="%prog " + VERSION)
parser.add_option('-H', '--hostname',
    dest="hostname",
    help='Hostname to connect to')
parser.add_option('-p', '--port',
    dest="port", type="int", default=22,
    help='SSH port to connect to. Default : 22')
parser.add_option('-i', '--ssh-key',
    dest="ssh_key_file", 
    help='SSH key file to use. By default will take ~/.ssh/id_rsa.')
parser.add_option('-u', '--user',
    dest="user",
    help='remote use to use. By default shinken.')
parser.add_option('-P', '--passphrase',
    dest="passphrase",
    help='SSH key passphrase. By default will use void')
parser.add_option('-s', '--service-name',
    dest="service_name",
    help='Service name to check.')
parser.add_option('--custom-cmd',
    dest="custom_cmd",
    help='Custom command to check a service state.')
parser.add_option('--custom-search',
    dest="custom_search",
    help='Search a string in the custom command stdout.')
parser.add_option('--stdout-exp',
    dest="stdout_exp",
    help='Stdout expected for a service state.')

if __name__ == '__main__':
    # Ok first job : parse args
    opts, args = parser.parse_args()
    if args:
        parser.error("Does not accept any argument.")

    port = opts.port
    hostname = opts.hostname or ''

    ssh_key_file = opts.ssh_key_file or os.path.expanduser('~/.ssh/id_rsa')
    user = opts.user or 'shinken'
    passphrase = opts.passphrase or ''
    service_name = opts.service_name
    custom_cmd = opts.custom_cmd
    custom_search = opts.custom_search
    stdout_exp = opts.stdout_exp

    # Ok now connect, and try to get values for memory
    client = schecks.connect(hostname, port, ssh_key_file, passphrase, user)
    output = get_service_status(client, service_name, custom_cmd, custom_search)
    
    if not output:
        print "Critical : cannot connect with your ssh credentials"
        sys.exit(2)
    elif "stdout" in output:
        for line in output["stdout"].split("\n"):
            if custom_cmd:
                if stdout_exp in line:
                    print "OK => " + line
                    exit_code = 0
                else:
                    print "Critical => Not the expected state: " + line
                    exit_code = 1
            else:
		if line.endswith('is running...') or line.endswith('is up...'):
		    print "OK => " + line
		    exit_code = 0
		if line.endswith('is stopped'):
		    print "Critical => " + line
		    exit_code = 1
		if line.endswith('dead but pid file exists'):
		    print "Critical => " + line
		    exit_code = 1

    elif "stderr" in output:
        print "Fatal => " + output["stderr"]
        exit_code = 2
    else:
        print "Fatal: unknow command ouput"
        exit_code = 3

    if exit_code:
        sys.exit(exit_code)
