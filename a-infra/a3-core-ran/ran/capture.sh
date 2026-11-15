#!/bin/bash
# capture.sh : captures N2/N3 (enregistrement), puis comparaison trafic en clair / encapsulé
TMP=/tmp/pcap; OUT=$HOME/pcap
rm -rf $TMP; mkdir -p $TMP $OUT; chmod 777 $TMP

echo "== Capture 1 : NG Setup + enregistrement + session PDU + trafic =="
sudo tshark -i ens37 -f "sctp or udp port 2152" -w $TMP/n2n3.pcap -a duration:40 &
sleep 3
docker restart gnb >/dev/null; sleep 4          # provoque un nouveau NG Setup
docker restart ue1 >/dev/null                   # provoque enregistrement + session PDU
until ip link show uesimtun0 >/dev/null 2>&1; do sleep 0.5; done
sleep 2
ping -I uesimtun0 -c 10 192.168.60.20
wait

echo "== Capture 2 : trafic en clair (uesimtun0) et encapsulé (ens37) =="
sudo tshark -i ens37 -f "udp port 2152" -w $TMP/gtpu.pcap -a duration:15 &
sudo tshark -i uesimtun0 -w $TMP/uesimtun0.pcap -a duration:15 &
sleep 3
ping -I uesimtun0 -c 5 192.168.60.20
wait

sudo cp $TMP/*.pcap $OUT/
sudo chown $USER:$USER $OUT/*.pcap
ls -lh $OUT
