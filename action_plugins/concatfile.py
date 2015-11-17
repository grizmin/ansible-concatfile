# (c) 2015, Konstantin Krastev <grizmin@gmail.com>
#
# This file is part of Ansible
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.plugins.action import ActionBase
from ansible.utils.boolean import boolean


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        src        = self._task.args.get('src', None)

        if src is None:
            result['failed'] = True
            result['msg'] = "src is required"
            return result

        if self._task._role is not None:
            src = self._loader.path_dwim_relative(self._task._role._role_path, 'files', src)
        else:
            src = self._loader.path_dwim_relative(self._loader.get_basedir(), 'files', src)
        if tmp is None or "-tmp-" not in tmp:
            tmp = self._make_tmp_path()

        tmp_src = self._connection._shell.join_path(tmp, os.path.basename(src))
        self._connection.put_file(src, tmp_src)

        if self._play_context.become and self._play_context.become_user != 'root':
            if not self._play_context.check_mode:
                self._remote_chmod('a+r', tmp_src)

        new_module_args = self._task.args.copy()
        new_module_args.update(
            dict(
                src=tmp_src,
            )
        )
        result.update(self._execute_module('concatfile', module_args=new_module_args, task_vars=task_vars))
        return result
