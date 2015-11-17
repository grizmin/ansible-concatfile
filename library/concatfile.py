#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2015, Konstantin Krastev <grizmin@mail.com>
#
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import os
import tempfile

DOCUMENTATION = '''
---
module: concatfile
version_added: "initial"
short_description: Concatenates file to remote file.
description:
     - The M(concatfile) module concatenates file from the local box to remote file.
options:
  src:
    description:
      - Local path to a file to concatenate to the remote server; can be absolute or relative.
    required: True
    default: null
    aliases: []
    version_added: "initial"
  dest:
    description:
      - Remote absolute path where the file should be copied to. 
    required: true
    default: null
    version_added: "initial"
  backup:
    description:
      - Create a backup file including the timestamp information so you can get
        the original file back if you somehow clobbered it incorrectly.
    required: false
    choices: [ "yes", "no" ]
    default: "no"
    version_added: "initial"
  force:
    description:
      - the default is C(yes), which will concatinate the content of source file on the destination even if the content of source is already there.
    required: false
    choices: [ "yes", "no" ]
    default: "yes"
    aliases: [ "thirsty" ]
    version_added: "initial"

extends_documentation_fragment:
    - files
author:
    - "Ansible Core Team"
    - "Michael DeHaan"
notes:
   - concatfile module is 3rd party ansible module.
     For alternative, see synchronize module, which is a wrapper around rsync.
'''

EXAMPLES = '''
# Example from Ansible Playbooks
- concatfile: src=/srv/myfiles/foo.conf dest=/etc/foo.conf

# Cncatenate bashrc.git to remote ~/.bashrc in roder to add git completition
- concatfile: src=bashrc.git dest=~/.bashrc backup=True force=False

'''

RETURN = '''
dest:
    description: destination file/path
    returned: success
    type: string
    sample: "/path/to/file.txt"
src:
    description: source file used for the copy on the target machine
    returned: changed
    type: string
    sample: "/home/httpd/.ansible/tmp/ansible-tmp-1423796390.97-147729857856000/source"
md5sum:
    description: md5 checksum of the file after running copy
    returned: when supported
    type: string
    sample: "2a5aeecc61dc98c4d780b14b330e3282"
checksum:
    description: checksum of the file after running copy
    returned: success
    type: string
    sample: "6e642bb8dd5c2e027bf21dd923337cbb4214f827"
backup_file:
    description: name of backup file created
    returned: changed and if backup=yes
    type: string
    sample: "/path/to/file.txt.2015-02-12@22:09~"
gid:
    description: group id of the file, after execution
    returned: success
    type: int
    sample: 100
group:
    description: group of the file, after execution
    returned: success
    type: string
    sample: "httpd"
owner:
    description: owner of the file, after execution
    returned: success
    type: string
    sample: "httpd"
uid:
    description: owner id of the file, after execution
    returned: success
    type: int
    sample: 100
mode:
    description: permissions of the target, after execution
    returned: success
    type: string
    sample: "0644"
size:
    description: size of the target, after execution
    returned: success
    type: int
    sample: 1220
state:
    description: state of the target, after execution
    returned: success
    type: string
    sample: "file"
'''

def main():
    module = AnsibleModule(
        # not checking because of daisy chain to file module
        argument_spec = dict(
            src               = dict(required=False),
            original_basename = dict(required=False), # used to handle 'dest is a directory' via template, a slight hack
            content           = dict(required=False, no_log=True),
            dest              = dict(required=True),
            backup            = dict(default=False, type='bool'),
            force             = dict(default=True, aliases=['thirsty'], type='bool'),
        ),
        add_file_common_args=True,
        supports_check_mode=True,
    )

    src = module.params['src']
    dest   = os.path.expanduser(module.params['dest'])
    backup = module.params['backup']
    force  = module.params['force']
    original_basename = module.params.get('original_basename',None)
    follow = module.params['follow']
    mode   = module.params['mode']
    check  = module.check_mode

    if not os.path.exists(src):
        module.fail_json(msg="Source %s not found" % (src))
    if not os.access(src, os.R_OK):
        module.fail_json(msg="Source %s not readable" % (src))

    checksum_src = module.sha1(src)
    checksum_dest = None
    # Backwards compat only.  This will be None in FIPS mode
    try:
        md5sum_src = module.md5(src)
    except ValueError:
        md5sum_src = None

    changed = False

    if os.path.exists(dest):
        if os.path.islink(dest):
            dest = os.path.realpath(dest)
        if (os.path.isdir(dest)):
            module.fail_json(msg="Source %s is directory, must be file" % (dest))
        if os.access(dest, os.R_OK):
            checksum_dest = module.sha1(dest)
    else:
        module.fail_json(msg="Destination %s doesn't exists" % (dest))

    backup_file = None
    try:
        # allow for conversion from symlink.
        if os.path.islink(dest):
            os.unlink(dest)
            open(dest, 'w').close()
        with open (src, 'r') as lfd:
            sourcefile = lfd.read()

        if not force and not check:
            with open (dest, 'r') as dfd:
                destfile = dfd.read()
            if sourcefile in destfile:
                changed = False
            else:
                if backup:
                    backup_file = module.backup_local(dest)
                module.append_to_file(dest, sourcefile)
                changed = True
        elif not check:
            if backup:
                backup_file = module.backup_local(dest)
            module.append_to_file(dest, sourcefile)
            changed = True
        else:
            with open (dest, 'r') as dfd:
                destfile = dfd.read()
            if sourcefile in destfile:
                 changed = False
            else:
                changed = True
    except IOError:
        module.fail_json(msg="failed to append: %s to %s" % (src, dest))

    res_args = dict(
        dest = dest, src = src, md5sum = md5sum_src, checksum = checksum_src,check = check, changed = changed
    )
    if backup_file:
        res_args['backup_file'] = backup_file

    file_args = module.load_file_common_arguments(module.params)
    res_args['changed'] = module.set_fs_attributes_if_different(file_args, res_args['changed'])

    module.exit_json(**res_args)

# import module snippets
from ansible.module_utils.basic import *
main()
