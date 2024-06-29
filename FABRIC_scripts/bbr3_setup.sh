#!/bin/bash

# this script should run as root and has been tested with ubuntu 20.04

apt-get update && apt-get -y upgrade
apt-get install -y linux-headers-$(uname -r)
apt-get install -y build-essential make libelf-dev libssl-dev flex bison zlib1g-dev librrd-dev libpcap-dev autoconf automake libarchive-dev htop bmon vim wget pkg-config git python-dev python3-pip libtool iperf3
pip install --upgrade pip

# Load TCP congestion control modules
declare -a cc_modules=("tcp_bbr" "tcp_bbr1" "tcp_cubic" "tcp_reno" "tcp_htcp")

for module in "${cc_modules[@]}"
do
    sudo modprobe $module 2>/dev/null
    if [[ $? -eq 0 ]]; then
        echo "$module loaded successfully."
    else
        echo "Failed to load $module or it is not available as a module."
    fi
done


# Check available TCP congestion control algorithms
sysctl net.ipv4.tcp_available_congestion_control


############################
####     TCP TUNING     ####
############################

#!/bin/bash

# Linux host tuning from https://fasterdata.es.net/host-tuning/linux/
sudo cat >> /etc/sysctl.conf <<EOL
# allow testing with buffers up to 128MB
net.core.rmem_max = 536870912 
net.core.wmem_max = 536870912 
# increase Linux autotuning TCP buffer limit to 64MB
net.ipv4.tcp_rmem = 4096 87380 536870912
net.ipv4.tcp_wmem = 4096 65536 536870912
# recommended default congestion control is htcp  or bbr
net.ipv4.tcp_congestion_control=bbr
# recommended for hosts with jumbo frames enabled
net.ipv4.tcp_mtu_probing=1
# recommended to enable 'fair queueing'
net.core.default_qdisc = fq
#net.core.default_qdisc = fq_codel
EOL

sysctl --system

# Turn on jumbo frames
for dev in `basename -a /sys/class/net/*`; do
    ip link set dev $dev mtu 9000
done

############################
####   Install BBRv3    ####
############################

#set -x
#rm -rf /boot/*GCE /lib/modules/*GCE

wget https://workflow.isi.edu/Poseidon/fabric/kernel-+v3+6e321d1c986a+FABRIC.tar.gz2
tar --no-same-owner -xzvf kernel-+v3+6e321d1c986a+FABRIC.tar.gz2 -C / > /tmp/tar.out.txt

cd /boot
for v in $(ls vmlinuz-* | sed s/vmlinuz-//g); do
    mkinitramfs -k -o initrd.img-${v} ${v}
done
update-grub
