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

gpg_home_dir="/path/to/dir/with/gpg/executable"

# A path to file storing the keys - set this if getting error like
# gnupg: potential problem: ERROR: add_keyblock_resource 33587201
# gnupg: potential problem: ERROR: keydb_search 33554445
# otherwise set to gpg_keyring_dir=None
# Examples below shows direct paths to the file 
# but path to containing folder seems to work too
# gpg_keyring_dir="c:\\Users\\ExampleWinUser\\.gnupg\\pubring.kbx"
# gpg_keyring_dir="/home/ExampleLinuxUser/.gnupg/pubring.kbx"

# Set this to attachment size limit used by email provider. This number is not strictly enforced by the script[^1] - actual videos attached in alerts may be bigger - so this number should be accordingly lower than the actual limit used by the email provider.
max_attachment_bytes = 20 * 2**20


# [^1] Rather than stopping video when max_attachment_bytes is actually reached there is a time limit set on the video - it is derived from max_attachment_size and the video bitrate)
```
2. Install python dependencies:
```
# python wrapper for gnupg (more info at: https://gnupg.readthedocs.io/en/latest/)
pip install python-gnupg
# numpy
pip install numpy

# install picamera library. Optional step for RPi Lite OS. Other versions of RPi OS should already have it
sudo apt install -y python3-picamera2 --no-install-recommends

```

Setting up gpg with email client on mobile; 
TIP: protonmail seems to do something weird. The mime headers in my protonmail inbox differ from the ones that left the python script.
https://support.mozilla.org/en-US/kb/openpgp-thunderbird-android-howto

#run 
run in background with `nohup python do_monitoring.p &`