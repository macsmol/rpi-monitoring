# setup
1. Next main srcipt create a config.py file with the desired data
```
send_from = "exampleAccount@foo.com"
send_to   = "dest@bar.com"

password  = "passwordTo exampleAccount@foo.com"

# address of smtp server for send_from account
server_url  = "smtp.wp.pl"
server_port = 465

gpg_home_dir="/path/to/dir/with/gpg"
```
2. Install python wrapper for GnuPG.
```
pip install python-gnupg
```
or see the instructions how to do it at: https://gnupg.readthedocs.io/en/latest/
