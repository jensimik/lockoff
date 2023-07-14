# Raspberry configuration / notes

set username to lockoff
sudo raspi-config enable wifi, osv.
curl -sS https://apt.edatec.cn/pubkey.gpg | sudo apt-key add -
echo "deb https://apt.edatec.cn/raspbian stable main" | sudo tee /etc/apt/sources.list.d/edatec.list
apt-get update
apt-get upgrade
sudo apt install ed-cm4nano-bsp ed-rtc
systemctl disable ModemManager.service
systemctl stop ModemManager.service
systemctl disable bluetooth.service
systemctl stop bluetooth.service
systemctl disable fake-hwclock.service
systemctl stop fake-hwclock.service

# setup tailscale

curl -fsSL https://tailscale.com/install.sh | sh

# setup docker

curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker lockoff
sudo apt-get install libffi-dev libssl-dev
sudo apt install python3-dev
sudo apt-get install -y python3 python3-pip
sudo pip3 install docker-compose
sudo systemctl enable docker
copy docker-compose.yml
docker-compose pull
docker-compose up -d

# ibeacon

set beacon and frequency to 100ms uuid 812366E1-4479-404B-B4A1-110FBBA9F625
sudo hciconfig hci0 up
sudo hciconfig hci0 leadv 3
sudo hcitool -i hci0 cmd 0x08 0x0008 1E 02 01 06 1A FF 4C 00 02 15 81 23 66 E1 44 79 40 4B B4 A1 11 0F BB A9 F6 25 00 00 00 00 C8 00
sudo hcitool -i hci0 cmd 0x08 0x0006 20 00 A0 00 00 00 00 00 00 00 00 00 00 07 00
sudo hcitool -i hci0 cmd 0x08 0x000A 01
sudo hciconfig hci0 noscan

# make udev rules for opticon

/etc/udev/rules.d/99_opticon.rules
KERNEL=="ttyACM[0-9]", ATTRS{idVendor}=="065a", ATTRS{idProduct}=="a002", SYMLINK+="OPTICON"
