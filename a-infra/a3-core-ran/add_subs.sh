#!/bin/bash
# add_subs.sh <nombre> : ajoute des abonnés dans MongoDB (conteneur « mongo »)
N=${1:-1}
K=465B5CE8B199B49FAA5F0A2EE238A6BC
OPC=E8ED289DEBA952E4283B54E88E6183CA
for i in $(seq 1 $N); do
  IMSI=$(printf "99970%010d" $i)
  docker exec -i mongo mongosh --quiet open5gs <<EOS
db.subscribers.deleteMany({imsi: "$IMSI"});
db.subscribers.insertOne({
  imsi: "$IMSI", schema_version: NumberInt(1), msisdn: [], imeisv: [], mme_host: [], mm_realm: [],
  purge_flag: [], access_restriction_data: 32, subscriber_status: 0, network_access_mode: 0,
  operator_determined_barring: 0, subscribed_rau_tau_timer: 12,
  ambr: { downlink: {value: NumberInt(1), unit: NumberInt(3)},
          uplink: {value: NumberInt(1), unit: NumberInt(3)} },
  security: { k: "$K", amf: "8000", op: null, opc: "$OPC", sqn: NumberLong(0) },
  slice: [{ sst: NumberInt(1), default_indicator: true, session: [{
    name: "internet", type: NumberInt(1), pcc_rule: [],
    ambr: { downlink: {value: NumberInt(1), unit: NumberInt(3)},
            uplink: {value: NumberInt(1), unit: NumberInt(3)} },
    qos: { index: NumberInt(9), arp: { priority_level: NumberInt(8),
           pre_emption_capability: NumberInt(1), pre_emption_vulnerability: NumberInt(1) } } }] }]
});
EOS
done
docker exec mongo mongosh --quiet open5gs --eval 'db.subscribers.countDocuments()'
