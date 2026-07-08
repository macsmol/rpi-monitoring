# setup
1. Next to do_monitoring.py srcipt create a config.py file with the desired data
```
send_from = "exampleAccount@foo.com"

# email address that will receive the notifications
send_to   = "dest@bar.com"

password  = "passwordTo exampleAccount@foo.com"

# address of smtp server for send_from account
server_url  = "smtp.wp.pl"
server_port = 465

gpg_home_dir="/path/to/dir/with/gpg"

# A path to file storing the keys - set this if getting error like
# gnupg: potential problem: ERROR: add_keyblock_resource 33587201
# gnupg: potential problem: ERROR: keydb_search 33554445
# otherwise set to gpg_keyring_dir=None
# Example below shows direct path to the file 
# but path to containing folder seems to work too
gpg_keyring_dir="c:\\Users\\ExampleWinUser\\.gnupg\\pubring.kbx"
```
2. Install python wrapper for GnuPG.
```
pip install python-gnupg
```
or see the instructions how to do it at: https://gnupg.readthedocs.io/en/latest/

Setting up gpg with email client on mobile; 
TIP: protonmail seems to do something weird. The mime headers in my protonmail inbox differ from the ones that left the python script.
https://support.mozilla.org/en-US/kb/openpgp-thunderbird-android-howto

# known bugs/issues
- For whatever reason the gpg fails with  with "BrokenPipeError: [Errno 32] Broken pipe" when sending email to protonmail address (confirmed to work when sending to @wp.pl addresses)