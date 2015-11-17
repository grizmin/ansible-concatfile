concatfile
===

Concatenates content of loca file to remote file.

Requirements
------------

None

Role Variables
--------------

```
None
```

Dependencies
------------

None

Example Playbook
----------------

Examples:

- Example from Ansible Playbooks

``` 
- concatfile: src=/srv/myfiles/foo.conf dest=/etc/foo.conf
```

- append bashrc.git to remote ~/.bashrc

```
- concatfile: src=bashrc.git dest=~/.bashrc backup=True force=False
```

License
-------

MIT

Author Information
------------------

Use [github](https://github.com/grizmin/ansible-concatfile) to file issues
