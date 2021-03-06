# 2. start containers on AKS

Start pods & services on AKS by following steps:

1. [start rabbitmq cluster](#start-rabbitmq-cluster-on-aks)
1. [start mongodb cluster](#start-mondodb-cluster-on-aks)
1. [start ambassador](#start-ambassador-on-aks)
1. [start authorization & authentication servie](#start-authorization--authentication-service-on-aks)
1. [start fiware orion](#start-fiware-orion-on-aks)
1. [start fiware IDAS(iotagent-ul)](#start-fiware-idasiotagent-ul-on-aks)
1. [start fiware cygnus](#start-fiware-cygnus-on-aks)
1. [build libraries for controller services](#build-libraries-for-controller-services)
1. [start reception service](#start-reception-service-on-aks)
1. [start destination service](#start-destination-service-on-aks)
1. [start storage service](#start-storage-service-on-aks)
1. [start ledger service](#start-ledger-service-on-aks)
1. [start guidance service](#start-guidance-service-on-aks)
1. [start autoreturn service](#start-autoreturn-service-on-aks)
1. [start monitoring](#start-monitoring-on-aks)
1. [start logging](#start-logging-on-aks)
1. [start cronjob](#start-cronjob-on-aks)

## start rabbitmq cluster on AKS

[RabbitMQ](https://www.rabbitmq.com/)

```bash
mac:$ docker run -it -v $(pwd)/secrets:/etc/letsencrypt certbot/certbot certonly --manual --domain mqtt.tech-sketch.jp --email nobuyuki.matsui@gmail.com --agree-tos --manual-public-ip-logging-ok --preferred-challenges dns
```

* Another terminal
```bash
mac-another:$ az network dns record-set txt add-record --resource-group dns-zone --zone-name "tech-sketch.jp" --record-set-name "_acme-challenge.mqtt" --value "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
mac-another:$ az network dns record-set list --resource-group dns-zone --zone-name "tech-sketch.jp" | jq '.[] | {"fqdn": .fqdn, "type": .type}'
{
  "fqdn": "tech-sketch.jp.",
  "type": "Microsoft.Network/dnszones/NS"
}
{
  "fqdn": "tech-sketch.jp.",
  "type": "Microsoft.Network/dnszones/SOA"
}
{
  "fqdn": "_acme-challenge.mqtt.tech-sketch.jp.",
  "type": "Microsoft.Network/dnszones/TXT"
}
```

* Press 'ENTER' at original terminal when `_acme-challenge.mqtt.tech-sketch.jp.` txt record is created.

* After completion of certbot
```bash
mac-another:$ az network dns record-set txt remove-record --resource-group dns-zone --zone-name "tech-sketch.jp" --record-set-name "_acme-challenge.mqtt" --value "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

```bash
mac:$ kubectl create secret generic rabbitmq-certifications --from-file=./secrets/live/mqtt.tech-sketch.jp/fullchain.pem --from-file=./secrets/live/mqtt.tech-sketch.jp/cert.pem --from-file=./secrets/live/mqtt.tech-sketch.jp/privkey.pem
```

```bash
mac:$ kubectl get secrets
NAME                                                          TYPE                                  DATA      AGE
default-token-gdql9                                           kubernetes.io/service-account-token   3         41m
fiware-etcd-etcd-operator-etcd-backup-operator-token-ztqfd    kubernetes.io/service-account-token   3         8m
fiware-etcd-etcd-operator-etcd-operator-token-jw724           kubernetes.io/service-account-token   3         8m
fiware-etcd-etcd-operator-etcd-restore-operator-token-xq6rl   kubernetes.io/service-account-token   3         8m
rabbitmq-certifications                                       Opaque                                3         7s
```

```bash
mac:$ kubectl apply -f rabbitmq/rabbitmq-rbac.yaml
```
```bash
mac:$ kubectl apply -f rabbitmq/rabbitmq-azure-services.yaml
```
```bash
mac:$ kubectl get services -l app=rabbitmq
NAME             TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)              AGE
rabbitmq         ClusterIP      None           <none>        5672/TCP             9s
rabbitmq-amqp    ClusterIP      10.0.190.158   <none>        15672/TCP,5672/TCP   9s
rabbitmq-mqtt    ClusterIP      10.0.101.206   <none>        1883/TCP             9s
rabbitmq-mqtts   LoadBalancer   10.0.131.94    <pending>     8883:30271/TCP       9s
```
```bash
mac:$ kubectl apply -f rabbitmq/rabbitmq-azure-statefulset.yaml
```
```bash
mac:$ $ kubectl get pods -l app=rabbitmq
NAME         READY     STATUS    RESTARTS   AGE
rabbitmq-0   1/1       Running   0          4m
rabbitmq-1   1/1       Running   0          3m
rabbitmq-2   1/1       Running   0          1m
```

```bash
mac:$ kubectl exec rabbitmq-0 -- rabbitmqctl cluster_status
Cluster status of node rabbit@rabbitmq-0.rabbitmq.default.svc.cluster.local ...
[{nodes,[{disc,['rabbit@rabbitmq-0.rabbitmq.default.svc.cluster.local',
                'rabbit@rabbitmq-1.rabbitmq.default.svc.cluster.local',
                'rabbit@rabbitmq-2.rabbitmq.default.svc.cluster.local']}]},
 {running_nodes,['rabbit@rabbitmq-2.rabbitmq.default.svc.cluster.local',
                 'rabbit@rabbitmq-1.rabbitmq.default.svc.cluster.local',
                 'rabbit@rabbitmq-0.rabbitmq.default.svc.cluster.local']},
 {cluster_name,<<"rabbit@rabbitmq-0.rabbitmq.default.svc.cluster.local">>},
 {partitions,[]},
 {alarms,[{'rabbit@rabbitmq-2.rabbitmq.default.svc.cluster.local',[]},
          {'rabbit@rabbitmq-1.rabbitmq.default.svc.cluster.local',[]},
          {'rabbit@rabbitmq-0.rabbitmq.default.svc.cluster.local',[]}]}]
```
```bash
mac:$ kubectl exec rabbitmq-0 -- rabbitmqctl change_password guest $(cat /dev/urandom | LC_CTYPE=C tr -dc 'a-zA-Z0-9' | head -c 32)
mac:$ kubectl exec rabbitmq-0 -- rabbitmqctl add_user iotagent <<password_of_iotagent>>
mac:$ kubectl exec rabbitmq-0 -- rabbitmqctl set_permissions -p / iotagent ".*" ".*" ".*"
mac:$ kubectl exec rabbitmq-0 -- rabbitmqctl add_user button_sensor <<password_of_button_sensor>>
mac:$ kubectl exec rabbitmq-0 -- rabbitmqctl set_permissions -p / button_sensor ".*" ".*" ".*"
mac:$ kubectl exec rabbitmq-0 -- rabbitmqctl add_user pepper <<password_of_pepper>>
mac:$ kubectl exec rabbitmq-0 -- rabbitmqctl set_permissions -p / pepper ".*" ".*" ".*"
mac:$ kubectl exec rabbitmq-0 -- rabbitmqctl add_user dest_led <<password_of_dest_led>>
mac:$ kubectl exec rabbitmq-0 -- rabbitmqctl set_permissions -p / dest_led ".*" ".*" ".*"
mac:$ kubectl exec rabbitmq-0 -- rabbitmqctl add_user dest_human_sensor <<password_of_dest_human_sensor>>
mac:$ kubectl exec rabbitmq-0 -- rabbitmqctl set_permissions -p / dest_human_sensor ".*" ".*" ".*"
mac:$ kubectl exec rabbitmq-0 -- rabbitmqctl add_user ros <<password_of_ros>>
mac:$ kubectl exec rabbitmq-0 -- rabbitmqctl set_permissions -p / ros ".*" ".*" ".*"
```
```bash
mac:$ kubectl exec rabbitmq-0 -- rabbitmqctl list_users
Listing users ...
ros	[]
dest_led	[]
button_sensor	[]
guest	[administrator]
dest_human_sensor	[]
pepper	[]
iotagent	[]
```

```bash
mac:$ kubectl get services -l app=rabbitmq -l service=mqtts
NAME             TYPE           CLUSTER-IP    EXTERNAL-IP   PORT(S)          AGE
rabbitmq-mqtts   LoadBalancer   10.0.131.94   WW.XX.YY.ZZ   8883:30271/TCP   21m
```
```bash
mac:$ export MQTTS_IPADDR=$(kubectl get services -l app=rabbitmq -l service=mqtts -o jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}');echo ${MQTTS_IPADDR}
mac:$ az network dns record-set a add-record --resource-group dns-zone --zone-name "tech-sketch.jp" --record-set-name "mqtt" --ipv4-address "${MQTTS_IPADDR}"
```
```bash
mac:$ nslookup mqtt.tech-sketch.jp
```

* XXXXXXXXXXXX is the password of `iotagent`
```text
mac:$ mosquitto_sub -h mqtt.tech-sketch.jp -p 8883 --cafile ./secrets/DST_Root_CA_X3.pem -d -t /# -u iotagent -P XXXXXXXXXXXX
...
```
* check the authentication of `button_sensor`, `pepper`, `dest_led`, `dest_human_sensor` and `ros` using a command like above

## start mondodb cluster on AKS

[mongodb](https://www.mongodb.com/)

```bash
mac:$ kubectl apply -f mongodb/mongodb-cluster-azure.yaml
```

```bash
mac:$ kubectl get PersistentVolumeClaims -l app=mongodb
NAME                              STATUS    VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS      AGE
mongodb-storage-claim-mongodb-0   Bound     pvc-aafd0623-5f1c-11e8-92d3-0a58ac1f13ee   30Gi       RWO            managed-premium   8m
mongodb-storage-claim-mongodb-1   Bound     pvc-121ca1c4-5f1d-11e8-92d3-0a58ac1f13ee   30Gi       RWO            managed-premium   5m
mongodb-storage-claim-mongodb-2   Bound     pvc-72a215e7-5f1d-11e8-92d3-0a58ac1f13ee   30Gi       RWO            managed-premium   2m
```

```bash
mac:$ kubectl get pods -l app=mongodb
NAME        READY     STATUS    RESTARTS   AGE
mongodb-0   2/2       Running   0          9m
mongodb-1   2/2       Running   0          6m
mongodb-2   2/2       Running   0          4m
```

```bash
mac:$ kubectl get services -l app=mongodb
NAME      TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)     AGE
mongodb   ClusterIP   None         <none>        27017/TCP   10m
```

```bash
mac:$ kubectl exec mongodb-0 -c mongodb -- mongo --eval 'printjson(rs.status().members.map(function(e) {return {name: e.name, stateStr:e.stateStr};}))'
MongoDB shell version v3.6.5
connecting to: mongodb://127.0.0.1:27017
MongoDB server version: 3.6.5
[
	{
		"name" : "mongodb-0.mongodb.default.svc.cluster.local:27017",
		"stateStr" : "PRIMARY"
	},
	{
		"name" : "mongodb-1.mongodb.default.svc.cluster.local:27017",
		"stateStr" : "SECONDARY"
	},
	{
		"name" : "mongodb-2.mongodb.default.svc.cluster.local:27017",
		"stateStr" : "SECONDARY"
	}
]
```

## start ambassador on AKS

[ambassador](https://www.getambassador.io/)

```bash
mac:$ docker run -it -v $(pwd)/secrets:/etc/letsencrypt certbot/certbot certonly --manual --domain api.tech-sketch.jp --email nobuyuki.matsui@gmail.com --agree-tos --manual-public-ip-logging-ok --preferred-challenges dns
```

* Another terminal
```bash
mac-another:$ az network dns record-set txt add-record --resource-group dns-zone --zone-name "tech-sketch.jp" --record-set-name "_acme-challenge.api" --value "YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY"
mac-another:$ az network dns record-set list --resource-group dns-zone --zone-name "tech-sketch.jp" | jq '.[] | {"fqdn": .fqdn, "type": .type}'
{
  "fqdn": "tech-sketch.jp.",
  "type": "Microsoft.Network/dnszones/NS"
}
{
  "fqdn": "tech-sketch.jp.",
  "type": "Microsoft.Network/dnszones/SOA"
}
{
  "fqdn": "_acme-challenge.api.tech-sketch.jp.",
  "type": "Microsoft.Network/dnszones/TXT"
}
{
  "fqdn": "mqtt.tech-sketch.jp.",
  "type": "Microsoft.Network/dnszones/A"
}
```

* Press 'ENTER' at original terminal when `_acme-challenge.api.tech-sketch.jp.` txt record is created.

* After completion of certbot
```bash
mac-another:$ az network dns record-set txt remove-record --resource-group dns-zone --zone-name "tech-sketch.jp" --record-set-name "_acme-challenge.api" --value "YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY"
```

```bash
mac:$ kubectl create secret tls ambassador-certs --cert=$(pwd)/secrets/live/api.tech-sketch.jp/fullchain.pem --key=$(pwd)/secrets/live/api.tech-sketch.jp/privkey.pem
```

```bash
mac:$ kubectl get secrets
NAME                                                          TYPE                                  DATA      AGE
ambassador-certs                                              kubernetes.io/tls                     2         8s
default-token-gdql9                                           kubernetes.io/service-account-token   3         1h
fiware-etcd-etcd-operator-etcd-backup-operator-token-ztqfd    kubernetes.io/service-account-token   3         29m
fiware-etcd-etcd-operator-etcd-operator-token-jw724           kubernetes.io/service-account-token   3         29m
fiware-etcd-etcd-operator-etcd-restore-operator-token-xq6rl   kubernetes.io/service-account-token   3         29m
rabbitmq-certifications                                       Opaque                                3         7s
```

```bash
mac:$ kubectl apply -f ambassador/ambassador-azure-services.yaml
```
```bash
mac:$ kubectl get services -l service=ambassador
NAME         TYPE           CLUSTER-IP    EXTERNAL-IP   PORT(S)                      AGE
ambassador   LoadBalancer   10.0.159.92   <pending>     443:31954/TCP,80:31958/TCP   29s
```

```bash
mac:$ kubectl apply -f ambassador/ambassador-deployment.yaml
```

```bash
mac:$ kubectl get pods -l service=ambassador
NAME                          READY     STATUS    RESTARTS   AGE
ambassador-79768bd968-7n4vl   2/2       Running   0          50s
ambassador-79768bd968-cpl5j   2/2       Running   0          50s
ambassador-79768bd968-h2ct2   2/2       Running   0          50s
```

```bash
mac:$ kubectl get services -l service=ambassador
NAME         TYPE           CLUSTER-IP    EXTERNAL-IP   PORT(S)                      AGE
ambassador   LoadBalancer   10.0.159.92   ww.xx.yy.zz   443:31954/TCP,80:31958/TCP   3m
```

```bash
mac:$ export HTTPS_IPADDR=$(kubectl get services -l service=ambassador -o json | jq '.items[0].status.loadBalancer.ingress[0].ip' -r);echo ${HTTPS_IPADDR}
mac:$ az network dns record-set a add-record --resource-group dns-zone --zone-name "tech-sketch.jp" --record-set-name "api" --ipv4-address "${HTTPS_IPADDR}"
```
```bash
mac:$ nslookup api.tech-sketch.jp
```

```bash
mac:$ curl -i https://api.tech-sketch.jp
HTTP/1.1 404 Not Found
date: Fri, 25 May 2018 00:47:41 GMT
server: envoy
content-length: 0
```

## start authorization & authentication service on AKS
* create random string
```bash
mac:$ cat /dev/urandom | LC_CTYPE=C tr -dc 'a-zA-Z0-9' | head -c 32; echo ""
```

* create `secrets/auth-tokens.json` like below:
```json
{
  "bearer_tokens": [
    {
      "token": "7aiplWERkMJdS11q79Nwtvy848CU7peT",
      "allowed_paths": ["^/orion/.*$", "^/idas/.*$", "^/destinations(/)?$", "^/storage/faces(/)?$"]
    }, {
      "token": "wSTjNyVqUsH27oIttz3qSl2fDqcpTCur",
      "allowed_paths": ["^/destinations(/)?$", "^/storage/faces(/)?$"]
    }, {
      "token": "age9ZQ9pk9WsWV79D8jN4MFEN1WqXnI7",
      "allowed_paths": ["^/destinations(/)?$"]
    }
  ],
  "basic_auths": []
}
```

```bash
mac:$ kubectl create secret generic auth-tokens --from-file=./secrets/auth-tokens.json
```

```bash
mac:$ kubectl get secrets
NAME                                                          TYPE                                  DATA      AGE
ambassador-certs                                              kubernetes.io/tls                     2         1h
ambassador-token-69r9s                                        kubernetes.io/service-account-token   3         1h
auth-tokens                                                   Opaque                                1         29s
default-token-gdql9                                           kubernetes.io/service-account-token   3         2h
fiware-etcd-etcd-operator-etcd-backup-operator-token-ztqfd    kubernetes.io/service-account-token   3         2h
fiware-etcd-etcd-operator-etcd-operator-token-jw724           kubernetes.io/service-account-token   3         2h
fiware-etcd-etcd-operator-etcd-restore-operator-token-xq6rl   kubernetes.io/service-account-token   3         2h
vernemq-certifications                                        Opaque                                3         2h
vernemq-passwd                                                Opaque                                1         2h
```

```bash
mac:$ kubectl apply -f ambassador/fiware-ambassador-auth.yaml
```

```bash
mac:$ kubectl get pods -l pod=ambassador-auth
NAME                           READY     STATUS    RESTARTS   AGE
ambassador-auth-6fffdbd9c9-7kkpr   1/1       Running   0          56s
ambassador-auth-6fffdbd9c9-qxw6m   1/1       Running   0          56s
ambassador-auth-6fffdbd9c9-sdn5b   1/1       Running   0          56s
```

```bash
mac:$ kubectl get services -l service=ambassador-auth
NAME          TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
ambassador-auth   ClusterIP   10.0.129.102   <none>        3000/TCP   2m
```

```bash
mac:$ curl -i https://api.tech-sketch.jp
HTTP/1.1 401 Unauthorized
content-type: application/json; charset=utf-8
www-authenticate: Bearer realm="token_required"
date: Tue, 14 Aug 2018 00:43:54 GMT
content-length: 60
x-envoy-upstream-service-time: 2
server: envoy

{"authorized":false,"error":"missing Header: authorization"}
```

## start fiware orion on AKS

[fiware orion](https://catalogue-server.fiware.org/enablers/publishsubscribe-context-broker-orion-context-broker)

```bash
mac:$ kubectl apply -f orion/orion.yaml
```

```bash
mac:$ kubectl get pods -l app=orion
NAME                     READY     STATUS    RESTARTS   AGE
orion-54f5cdcb5d-d2pt5   1/1       Running   0          56s
orion-54f5cdcb5d-hv274   1/1       Running   0          56s
orion-54f5cdcb5d-xbnx2   1/1       Running   0          56s
```

```bash
mac:$ kubectl get services -l app=orion
NAME      TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)    AGE
orion     ClusterIP   10.0.44.126   <none>        1026/TCP   1m
```

```bash
mac:$ TOKEN=$(cat secrets/auth-tokens.json | jq '.bearer_tokens[0].token' -r);curl -i -H "Authorization: bearer ${TOKEN}" https://api.tech-sketch.jp/orion/v2/entities/
HTTP/1.1 200 OK
content-length: 2
content-type: application/json
fiware-correlator: 4731eb48-4dc1-11e8-b1a2-0a580af4010a
date: Wed, 02 May 2018 04:28:35 GMT
x-envoy-upstream-service-time: 5
server: envoy

[]
```

```bash
mac:$ TOKEN=$(cat secrets/auth-tokens.json | jq '.bearer_tokens[0].token' -r);curl -i -H "Authorization: bearer ${TOKEN}" https://api.tech-sketch.jp/orion/v2/subscriptions/
HTTP/1.1 200 OK
content-length: 2
content-type: application/json
fiware-correlator: 5a4ecc6e-4dc1-11e8-b1a2-0a580af4010a
date: Wed, 02 May 2018 04:29:07 GMT
x-envoy-upstream-service-time: 2
server: envoy

[]
```

## start fiware idas(iotagent-ul) on AKS

[fiware IDAS(iotagent-ul)](https://catalogue-server.fiware.org/enablers/backend-device-management-idas)

```bash
mac:$ docker build -t ${REPOSITORY}/tech-sketch/iotagent-ul:290a1fa idas/iotagent-ul/
```
```bash
mac:$ az acr login --name ogcacr
```
```bash
mac:$ docker push ${REPOSITORY}/tech-sketch/iotagent-ul:290a1fa
```

```bash
mac:$ az acr repository list --name ogcacr --output table
Result
---------------------------------
tech-sketch/iotagent-ul
```

* XXXXXXXXXXXX is the password of "iotagent"
```bash
mac:$ env IOTA_PASSWORD=XXXXXXXXXXXX envsubst < idas/config.js > /tmp/config.js
mac:$ kubectl create secret generic iotagent-config --from-file /tmp/config.js
mac:$ rm /tmp/config.js
```
```bash
mac:$ envsubst < idas/iotagent-ul.yaml | kubectl apply -f -
```

```bash
mac:$ kubectl get pods -l app=iotagent-ul
NAME                           READY     STATUS    RESTARTS   AGE
iotagent-ul-79685b64bf-8krps   1/1       Running   0          3m
iotagent-ul-79685b64bf-m6nlg   1/1       Running   0          3m
iotagent-ul-79685b64bf-mjpbl   1/1       Running   0          3m
```

```bash
mac:$ kubectl get services -l app=iotagent-ul
NAME          TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)             AGE
iotagent-ul   ClusterIP   10.0.180.155   <none>        4041/TCP,7896/TCP   43s
```

```bash
mac:$ TOKEN=$(cat secrets/auth-tokens.json | jq '.bearer_tokens[0].token' -r);curl -i -H "Authorization: bearer ${TOKEN}" -H "Fiware-Service: demo1" -H "Fiware-Servicepath: /*" https://api.tech-sketch.jp/idas/ul20/manage/iot/services/
HTTP/1.1 200 OK
x-powered-by: Express
fiware-correlator: c114fc5e-b4a2-40f6-b7fe-1d68369784e5
content-type: application/json; charset=utf-8
content-length: 25
etag: W/"19-WMYe0U6ocKhQjp+oaVnMHLdbylc"
date: Wed, 02 May 2018 06:16:18 GMT
x-envoy-upstream-service-time: 9
server: envoy

{"count":0,"services":[]}
```

```bash
mac:$ TOKEN=$(cat secrets/auth-tokens.json | jq '.bearer_tokens[0].token' -r);curl -i -H "Authorization: bearer ${TOKEN}" -H "Fiware-Service: demo1" -H "Fiware-Servicepath: /" https://api.tech-sketch.jp/idas/ul20/manage/iot/devices/
HTTP/1.1 200 OK
x-powered-by: Express
fiware-correlator: 1d1ee2f1-83e4-454e-8ef5-a10fd49630ab
content-type: application/json; charset=utf-8
content-length: 24
etag: W/"18-90KiBjq8YRQpT/NsVf7vo89XXWw"
date: Wed, 02 May 2018 06:16:58 GMT
x-envoy-upstream-service-time: 8
server: envoy

{"count":0,"devices":[]}
```

## start fiware cygnus on AKS

[fiware cygnus](https://catalogue-server.fiware.org/enablers/cygnus)

**In this demonstration, we use re-configured cygnus in order to revoke unnecessary sinks.**

```bash
mac:$ az acr login --name ogcacr
mac:$ docker build -t ${REPOSITORY}/tech-sketch/cygnus-ngsi:1.8.0 ./cygnus/fiware-cygnus/
mac:$ docker push ${REPOSITORY}/tech-sketch/cygnus-ngsi:1.8.0
```

```bash
mac:$ az acr repository list --name ogcacr --output table
Result
---------------------------------
tech-sketch/cygnus-ngsi
tech-sketch/iotagent-ul
```

```bash
mac:$ envsubst < cygnus/cygnus.yaml | kubectl apply -f -
```

```bash
mac:$ kubectl get pods -l app=cygnus
NAME                      READY     STATUS    RESTARTS   AGE
cygnus-5c68fb6578-fdmtg   1/1       Running   0          44s
cygnus-5c68fb6578-stmds   1/1       Running   0          44s
cygnus-5c68fb6578-z85lp   1/1       Running   0          44s
```

```bash
mac:$ kubectl get services -l app=cygnus
NAME      TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)             AGE
cygnus    ClusterIP   10.103.255.240   <none>        5050/TCP,8081/TCP   1m
```

## build libraries for controller services
```bash
mac:$ pip install wheel
mac:$ sh ./controller/controllerlibs/build.sh
mac:$ ls -al controller/controllerlibs/dist/controllerlibs-0.1.0-py3-none-any.whl
-rw-r--r--  1 nmatsui  staff  6270  8  7 16:19 controller/controllerlibs/dist/controllerlibs-0.1.0-py3-none-any.whl
```

## start reception service on AKS
```bash
mac:$ az acr login --name ogcacr
mac:$ docker build --build-arg SERVICE_PATH="./controller/reception" -t ${REPOSITORY}/tech-sketch/reception:0.1.0 -f ./controller/docker/Dockerfile .
mac:$ docker push ${REPOSITORY}/tech-sketch/reception:0.1.0
```
```bash
mac:$ env PEPPER_SERVICE="pepper" PEPPER_SERVICEPATH="/" PEPPER_TYPE="pepper" PEPPER_1_ID="pepper_0000000000000001" PEPPER_2_ID="pepper_0000000000000002" PEPPER_IDPATTERN="pepper.*" envsubst < controller/reception.yaml | kubectl apply -f -
```
```bash
mac:$ kubectl get pods -l pod=reception
NAME                         READY     STATUS    RESTARTS   AGE
reception-5d99f87f55-5srqq   1/1       Running   0          36s
reception-5d99f87f55-dm2fd   1/1       Running   0          36s
reception-5d99f87f55-qz6cg   1/1       Running   0          36s
```
```bash
mac:$ kubectl get services -l service=reception
NAME        TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)    AGE
reception   ClusterIP   10.0.163.98   <none>        8888/TCP   1m
```

## start destination service on AKS
```bash
mac:$ az acr login --name ogcacr
mac:$ docker build --build-arg SERVICE_PATH="./controller/destination" -t ${REPOSITORY}/tech-sketch/destination:0.1.0 -f ./controller/docker/Dockerfile .
mac:$ docker push ${REPOSITORY}/tech-sketch/destination:0.1.0
```
```bash
mac:$ envsubst < controller/destination.yaml | kubectl apply -f -
```
```bash
mac:$ kubectl get pods -l pod=destination
NAME                           READY     STATUS    RESTARTS   AGE
destination-84b86b54f6-7wkl9   1/1       Running   0          19s
destination-84b86b54f6-rqjjc   1/1       Running   0          19s
destination-84b86b54f6-sjqhb   1/1       Running   0          19s
```
```bash
mac:$ kubectl get services -l service=destination
NAME          TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)    AGE
destination   ClusterIP   10.0.81.101   <none>        8888/TCP   1m
```
```bash
mac:$ TOKEN=$(cat secrets/auth-tokens.json | jq '.bearer_tokens[0].token' -r);curl -sS -H "Authorization: bearer ${TOKEN}" https://api.tech-sketch.jp/destinations/ | jq .
[]
```

## start storage service on AKS
```bash
mac:$ export MANAGED_CLUSTER=$(az resource show --resource-group ogc-poc1 --name ogc-poc1-aks --resource-type Microsoft.ContainerService/managedClusters --query properties.nodeResourceGroup -o tsv);echo ${MANAGED_CLUSTER}
mac:$ az storage account create --resource-group ${MANAGED_CLUSTER} --name fiwareaksstorageaccount --location japaneast --sku Standard_LRS
```
```bash
mac:$ kubectl create clusterrole system:azure-cloud-provider --verb=get,create --resource=secrets
mac:$ kubectl create clusterrolebinding system:azure-cloud-provider --clusterrole=system:azure-cloud-provider --serviceaccount=kube-system:persistent-volume-binder
```

```bash
mac:$ kubectl apply -f controller/shared-storage-azure.yaml
```
```bash
mac:$ kubectl get storageclasses
NAME                PROVISIONER                AGE
azurefile           kubernetes.io/azure-file   1m
default (default)   kubernetes.io/azure-disk   6h
managed-premium     kubernetes.io/azure-disk   6h
```
```bash
mac:$ kubectl get persistentvolumeclaims
NAME                              STATUS    VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS      AGE
face-upload-shared-storage        Bound     pvc-76d0dcd2-790e-11e8-9053-563fd79e0d5d   10Gi       RWX            azurefile         1m
mongodb-storage-claim-mongodb-0   Bound     pvc-01706875-78ed-11e8-9053-563fd79e0d5d   30Gi       RWO            managed-premium   4h
mongodb-storage-claim-mongodb-1   Bound     pvc-65adcba8-78ed-11e8-9053-563fd79e0d5d   30Gi       RWO            managed-premium   3h
mongodb-storage-claim-mongodb-2   Bound     pvc-c3e47e57-78ed-11e8-9053-563fd79e0d5d   30Gi       RWO            managed-premium   3h
```
```bash
mac:$ az acr login --name ogcacr
mac:$ docker build --build-arg SERVICE_PATH="./controller/storage" -t ${REPOSITORY}/tech-sketch/storage:0.1.0 -f ./controller/docker/Dockerfile_pillow .
mac:$ docker push ${REPOSITORY}/tech-sketch/storage:0.1.0
```
```bash
mac:$ envsubst < controller/storage.yaml | kubectl apply -f -
```
```bash
mac:$ kubectl get pods -l pod=storage
NAME                       READY     STATUS    RESTARTS   AGE
storage-6956d9b5ff-87ws5   1/1       Running   0          37s
storage-6956d9b5ff-f9ztr   1/1       Running   0          37s
storage-6956d9b5ff-wc2xq   1/1       Running   0          37s
```
```bash
mac:$ kubectl get services -l service=storage
NAME      TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)    AGE
storage   ClusterIP   10.0.91.62   <none>        8888/TCP   1m
```

```bash
mac:$ TOKEN=$(cat secrets/auth-tokens.json | jq '.bearer_tokens[0].token' -r);curl -sS -H "Authorization: bearer ${TOKEN}" -H "Content-Type: multipart/form-data" https://api.tech-sketch.jp/storage/faces/ -X POST -F face=@face.jpg | jq .
{
  "path": "/shared/faces/xBlzQGubIM5YYr1S.JPEG",
  "url": ""
}
```

## start ledger service on AKS
```bash
mac:$ az acr login --name ogcacr
mac:$ docker build --build-arg SERVICE_PATH="./controller/ledger" -t ${REPOSITORY}/tech-sketch/ledger:0.1.0 -f ./controller/docker/Dockerfile .
mac:$ docker push ${REPOSITORY}/tech-sketch/ledger:0.1.0
```
```bash
mac:$ echo ${FACE_API_BASEURL}
https://japaneast.api.cognitive.microsoft.com/face/v1.0
$ echo ${FACE_API_KEY}
ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ
mac:$ env PEPPER_SERVICE="pepper" PEPPER_SERVICEPATH="/" PEPPER_TYPE="pepper" PEPPER_1_ID="pepper_0000000000000001" PEPPER_2_ID="pepper_0000000000000002" ROBOT_SERVICE="robot" ROBOT_SERVICEPATH="/" ROBOT_TYPE="guide_robot" ROBOT_FLOOR_MAP="{\"guide_robot_0000000000000001\": 1, \"guide_robot_0000000000000002\": 2}" envsubst < controller/ledger.yaml | kubectl apply -f -
```
```bash
mac:$ kubectl get pods -l pod=ledger
NAME                     READY     STATUS    RESTARTS   AGE
ledger-df7789d46-mtx8j   1/1       Running   0          27s
ledger-df7789d46-nsws8   1/1       Running   0          27s
ledger-df7789d46-x5mxk   1/1       Running   0          27s
```
```bash
mac:$ kubectl get services -l service=ledger
NAME      TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)    AGE
ledger    ClusterIP   10.0.229.79   <none>        8888/TCP   50s
```

## start guidance service on AKS
```bash
mac:$ az acr login --name ogcacr
mac:$ docker build --build-arg SERVICE_PATH="./controller/guidance" -t ${REPOSITORY}/tech-sketch/guidance:0.1.0 -f ./controller/docker/Dockerfile .
mac:$ docker push ${REPOSITORY}/tech-sketch/guidance:0.1.0
```
```bash
mac:$ env ROBOT_SERVICE="robot" ROBOT_SERVICEPATH="/" ROBOT_TYPE="guide_robot" ROBOT_FLOOR_MAP="{\"guide_robot_0000000000000001\": 1, \"guide_robot_0000000000000002\": 2}" DEST_LED_SERVICE="dest_led" DEST_LED_SERVICEPATH="/" DEST_LED_TYPE="dest_led" envsubst < controller/guidance.yaml | kubectl apply -f -
```
```bash
mac:$ kubectl get pods -l pod=guidance
NAME                        READY     STATUS    RESTARTS   AGE
guidance-644f7f6755-2s4bq   1/1       Running   0          21s
guidance-644f7f6755-7ttpm   1/1       Running   0          21s
guidance-644f7f6755-sc5m8   1/1       Running   0          21s
```
```bash
mac:$ kubectl get services -l service=guidance
NAME       TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
guidance   ClusterIP   10.0.222.146   <none>        8888/TCP   58s
```

## start autoreturn service on AKS
```bash
mac:$ az acr login --name ogcacr
mac:$ docker build --build-arg SERVICE_PATH="./controller/autoreturn" -t ${REPOSITORY}/tech-sketch/autoreturn:0.1.0 -f ./controller/docker/Dockerfile_noflask .
mac:$ docker push ${REPOSITORY}/tech-sketch/autoreturn:0.1.0
```
```bash
mac:$ env ROBOT_SERVICE="robot" ROBOT_SERVICEPATH="/" ROBOT_TYPE="guide_robot" ROBOT_FLOOR_MAP="{\"guide_robot_0000000000000001\": 1, \"guide_robot_0000000000000002\": 2}" DEST_LED_SERVICE="dest_led" DEST_LED_SERVICEPATH="/" DEST_LED_TYPE="dest_led" envsubst < controller/autoreturn.yaml | kubectl apply -f -
```
```bash
mac:$ kubectl get pods -l pod=autoreturn
NAME                          READY     STATUS    RESTARTS   AGE
autoreturn-84648989c9-9v8tc   1/1       Running   0          16s
```

## start monitoring on AKS

[prometheus](https://prometheus.io/)  
[grafana](https://grafana.com/)

* enable coreos helm
```bash
mac:$ helm repo add coreos https://s3-eu-west-1.amazonaws.com/coreos-charts/stable/
```

* install coreos/prometheus-operator

```bash
mac:$ helm install coreos/prometheus-operator --name ogc-prometheus-operator --namespace monitoring
```
```bash
mac:$ kubectl get deployments --namespace monitoring
NAME                      DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
ogc-prometheus-operator   1         1         1            1           6m
```
```bash
mac:$ kubectl get pods --namespace monitoring
NAME                                          READY     STATUS      RESTARTS   AGE
ogc-prometheus-operator-6574f68ff9-498hk      1/1       Running     0          5m
ogc-prometheus-operator-create-sm-job-bbz9n   0/1       Completed   0          5m
```
```bash
mac:$ kubectl get jobs --namespace monitoring
NAME                                    DESIRED   SUCCESSFUL   AGE
ogc-prometheus-operator-create-sm-job   1         1            6m
```

* install coreos/kube-prometheus

```bash
mac:$ env GRAFANA_ADMIN_PASSWORD=YYYYYYYYYYYYYYYY envsubst < monitoring/kube-prometheus-azure.yaml | helm install coreos/kube-prometheus --name ogc-kube-prometheus --namespace monitoring -f -
```
```bash
mac:$ kubectl get daemonsets --namespace monitoring
NAME                                DESIRED   CURRENT   READY     UP-TO-DATE   AVAILABLE   NODE SELECTOR   AGE
ogc-kube-prometheus-exporter-node   4         4         4         4            4           <none>          4m
```
```bash
mac:$ kubectl get deployments --namespace monitoring
NAME                                      DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
ogc-kube-prometheus-exporter-kube-state   1         1         1            1           6m
ogc-kube-prometheus-grafana               1         1         1            1           6m
ogc-prometheus-operator                   1         1         1            1           28m
```
```bash
mac:$ kubectl get statefulsets --namespace monitoring
NAME                               DESIRED   CURRENT   AGE
alertmanager-ogc-kube-prometheus   1         1         6m
prometheus-ogc-kube-prometheus     1         1         6m
```
```bash
mac:$ kubectl get pods --namespace monitoring
NAME                                                       READY     STATUS      RESTARTS   AGE
alertmanager-ogc-kube-prometheus-0                         2/2       Running     0          3m
ogc-kube-prometheus-exporter-kube-state-6b47d67cf6-jj69r   2/2       Running     0          3m
ogc-kube-prometheus-exporter-node-7vq6x                    1/1       Running     0          3m
ogc-kube-prometheus-exporter-node-cwc7d                    1/1       Running     0          3m
ogc-kube-prometheus-exporter-node-lstm6                    1/1       Running     0          3m
ogc-kube-prometheus-exporter-node-xtb6h                    1/1       Running     0          3m
ogc-kube-prometheus-grafana-78d984b4f5-59j4r               2/2       Running     0          3m
ogc-prometheus-operator-6574f68ff9-498hk                   1/1       Running     0          12m
ogc-prometheus-operator-create-sm-job-bbz9n                0/1       Completed   0          12m
prometheus-ogc-kube-prometheus-0                           3/3       Running     1          3m
```
```bash
mac:$ kubectl get services --namespace monitoring
NAME                                      TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)             AGE
alertmanager-operated                     ClusterIP   None           <none>        9093/TCP,6783/TCP   8m
ogc-kube-prometheus                       ClusterIP   10.0.12.222    <none>        9090/TCP            8m
ogc-kube-prometheus-alertmanager          ClusterIP   10.0.100.232   <none>        9093/TCP            8m
ogc-kube-prometheus-exporter-kube-state   ClusterIP   10.0.221.39    <none>        80/TCP              8m
ogc-kube-prometheus-exporter-node         ClusterIP   10.0.141.146   <none>        9100/TCP            8m
ogc-kube-prometheus-grafana               ClusterIP   10.0.92.166    <none>        80/TCP              8m
prometheus-operated                       ClusterIP   None           <none>        9090/TCP            8m
```
```bash
mac:$ kubectl get persistentvolumeclaims --namespace monitoring
NAME                                                                     STATUS    VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS      AGE
alertmanager-ogc-kube-prometheus-db-alertmanager-ogc-kube-prometheus-0   Bound     pvc-94a3e841-9e98-11e8-8646-02af8659316c   30Gi       RWO            managed-premium   9m
prometheus-ogc-kube-prometheus-db-prometheus-ogc-kube-prometheus-0       Bound     pvc-94d234c0-9e98-11e8-8646-02af8659316c   30Gi       RWO            managed-premium   9m
```

* patch `kube-dns-v20` because Azure AKS does not export dns metrics
    * https://github.com/Azure/AKS/issues/345

```bash
mac:$ kubectl patch deployment -n kube-system kube-dns-v20 --patch "$(cat monitoring/kube-dns-metrics-patch.yaml)"
```

* patch `kube-prometheus-exporter-kubelets`
    * https://github.com/coreos/prometheus-operator/issues/926

```bash
mac:$ kubectl -n monitoring get servicemonitor ogc-kube-prometheus-exporter-kubelets -o yaml | sed 's/https/http/' | kubectl replace -f -
```

* delete monitor of apiserver because apiserver of Azure AKS does not allow to connect apiserver directry
    * https://github.com/coreos/prometheus-operator/issues/1522

```bash
mac:$ kubectl -n monitoring delete servicemonitor ogc-kube-prometheus-exporter-kubernetes
```
```bash
$ kubectl edit prometheusrules ogc-kube-prometheus --namespace monitoring
```
```diff
       for: 10m
       labels:
         severity: warning
-    - alert: DeadMansSwitch
-      annotations:
-        description: This is a DeadMansSwitch meant to ensure that the entire Alerting
-          pipeline is functional.
-        summary: Alerting DeadMansSwitch
-      expr: vector(1)
-      labels:
-        severity: none
     - expr: process_open_fds / process_max_fds
       record: fd_utilization
     - alert: FdExhaustionClose
```
```bash
$ kubectl edit prometheusrules ogc-kube-prometheus-exporter-kubernetes --namespace monitoring
```
```diff
       for: 10m
       labels:
         severity: critical
-    - alert: K8SApiserverDown
-      annotations:
-        description: No API servers are reachable or all have disappeared from service
-          discovery
-        summary: No API servers are reachable
-      expr: absent(up{job="apiserver"} == 1)
-      for: 20m
-      labels:
-        severity: critical
     - alert: K8sCertificateExpirationNotice
       annotations:
         description: Kubernetes API Certificate is expiring soon (less than 7 days)
```
```bash
$ kubectl edit prometheusrules ogc-kube-prometheus-exporter-kube-controller-manager --namespace monitoring
```
```diff
 spec:
   groups:
   - name: kube-controller-manager.rules
-    rules:
-    - alert: K8SControllerManagerDown
-      annotations:
-        description: There is no running K8S controller manager. Deployments and replication
-          controllers are not making progress.
-        runbook: https://coreos.com/tectonic/docs/latest/troubleshooting/controller-recovery.html#recovering-a-controller-manager
-        summary: Controller manager is down
-      expr: absent(up{job="kube-controller-manager"} == 1)
-      for: 5m
-      labels:
-        severity: critical
+    rules: []
```
```bash
$ kubectl edit prometheusrules ogc-kube-prometheus-exporter-kube-scheduler --namespace monitoring
```
```diff
       labels:
         quantile: "0.5"
       record: cluster:scheduler_binding_latency_seconds:quantile
-    - alert: K8SSchedulerDown
-      annotations:
-        description: There is no running K8S scheduler. New pods are not being assigned
-          to nodes.
-        runbook: https://coreos.com/tectonic/docs/latest/troubleshooting/controller-recovery.html#recovering-a-scheduler
-        summary: Scheduler is down
-      expr: absent(up{job="kube-scheduler"} == 1)
-      for: 5m
-      labels:
-        severity: critical
```

## start logging on AKS

[ElasticSearch](https://www.elastic.co/products/elasticsearch)  
[fluentd](https://www.fluentd.org/)  
[Kibana](https://www.elastic.co/products/kibana)

* create `logging` namespace
```bash
mac:$ kubectl apply -f logging/namespace.yaml
```

* start elasticsearch
```bash
mac:$ kubectl apply -f logging/elasticsearch.yaml
```
```bash
mac:$ kubectl get statefulsets -n monitoring -l k8s-app=elasticsearch-logging
NAME                    DESIRED   CURRENT   AGE
elasticsearch-logging   2         2         16m
```
```bash
mac:$ kubectl get pods -n monitoring -l k8s-app=elasticsearch-logging
NAME                      READY     STATUS    RESTARTS   AGE
elasticsearch-logging-0   1/1       Running   0          16m
elasticsearch-logging-1   1/1       Running   0          14m
```
```bash
mac:$ kubectl get services -n monitoring -l k8s-app=elasticsearch-logging
NAME                    TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
elasticsearch-logging   ClusterIP   10.0.204.122   <none>        9200/TCP   16m
```
```bash
mac:$ kubectl get persistentvolumeclaims -n monitoring -l k8s-app=elasticsearch-logging
NAME                                            STATUS    VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS      AGE
elasticsearch-logging-elasticsearch-logging-0   Bound     pvc-568875fa-a03a-11e8-9995-467fb626d835   64Gi       RWO            managed-premium   22m
elasticsearch-logging-elasticsearch-logging-1   Bound     pvc-4aa6e308-a03b-11e8-9995-467fb626d835   64Gi       RWO            managed-premium   15m
```

```bash
mac:$ kubectl exec -it elasticsearch-logging-0 -n monitoring -- curl -H "Content-Type: application/json" -X PUT http://elasticsearch-logging:9200/_cluster/settings -d '{"transient": {"cluster.routing.allocation.enable":"all"}}'
{"acknowledged":true,"persistent":{},"transient":{"cluster":{"routing":{"allocation":{"enable":"all"}}}}
```

* stert fluentd
```bash
mac:$ kubectl apply -f logging/fluentd-es-configmap.yaml
```
```bash
mac:$ kubectl get configmap -n monitoring
NAME                                       DATA      AGE
fluentd-es-config-v0.1.4                   6         8s
ogc-kube-prometheus-grafana                10        36m
ogc-prometheus-operator                    1         40m
prometheus-ogc-kube-prometheus-rulefiles   10        36m
```
```bash
mac:$ kubectl apply -f logging/fluentd-es-ds.yaml
```
```bash
mac:$ kubectl get daemonsets -n monitoring -l k8s-app=fluentd-es
NAME                DESIRED   CURRENT   READY     UP-TO-DATE   AVAILABLE   NODE SELECTOR   AGE
fluentd-es-v2.2.0   4         4         4         4            4           <none>          27m
```
```bash
mac:$ kubectl get pods -n monitoring -l k8s-app=fluentd-es
NAME                      READY     STATUS    RESTARTS   AGE
fluentd-es-v2.2.0-4cvl9   1/1       Running   0          6m
fluentd-es-v2.2.0-5v6mz   1/1       Running   0          6m
fluentd-es-v2.2.0-chvdk   1/1       Running   0          6m
fluentd-es-v2.2.0-lptz9   1/1       Running   0          6m
```

* start kibana
```bash
mac:$ kubectl apply -f logging/kibana.yaml
```
```bash
mac:$ kubectl get deployments -n monitoring -l k8s-app=kibana-logging
NAME             DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
kibana-logging   1         1         1            1           2m
```
```bash
mac:$ kubectl get pods -n monitoring -l k8s-app=kibana-logging
NAME                             READY     STATUS    RESTARTS   AGE
kibana-logging-86b5665bb-7kcn4   1/1       Running   0          2m
```
```bash
mac:$ kubectl get services -n monitoring -l k8s-app=kibana-logging
NAME             TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
kibana-logging   ClusterIP   10.0.187.100   <none>        5601/TCP   3m
```

* register curator job
```bash
mac:$ kubectl apply -f logging/curator-configmap.yaml
```
```bash
mac:$ kubectl get configmaps -n monitoring
NAME                                       DATA      AGE
curator-config                             2         32s
fluentd-es-config-v0.1.4                   6         3m
ogc-kube-prometheus-grafana                10        40m
ogc-prometheus-operator                    1         43m
prometheus-ogc-kube-prometheus-rulefiles   10        39m
```
```bash
mac:$ kubectl apply -f logging/curator-cronjob.yaml
```
```bash
$ kubectl get cronjobs -n monitoring -l k8s-app=elasticsearch-curator
NAME                    SCHEDULE     SUSPEND   ACTIVE    LAST SCHEDULE   AGE
elasticsearch-curator   0 18 * * *   False     0         7m              11m
```

after cronjob triggered

```bash
mac:$ kubectl get jobs -n monitoring
NAME                               DESIRED   SUCCESSFUL   AGE
elasticsearch-curator-1534311000   1         1            1m
```

## start cronjob on AKS

* start cronjob to restart `iotagent-ul` on each day (02:00 JST).

```bash
$ docker build -t ${REPOSITORY}/tech-sketch/iotagent-ul-restarter:0.1.0 idas/restarter/
$ az acr login --name ogcacr
$ docker push ${REPOSITORY}/tech-sketch/iotagent-ul-restarter:0.1.0
```
```bash
$ az acr repository list --name ogcacr --output table
Result
---------------------------------
tech-sketch/cygnus-ngsi
tech-sketch/destination
tech-sketch/guidance
tech-sketch/iotagent-ul
tech-sketch/iotagent-ul-restarter
tech-sketch/ledger
tech-sketch/reception
tech-sketch/storage
```

```bash
$ envsubst < idas/restart-iotagent-ul-cronjob.yaml | kubectl apply -f -
```
```bash
$ kubectl get cronjobs
NAME                    SCHEDULE     SUSPEND   ACTIVE    LAST SCHEDULE   AGE
iotagent-ul-resterter   0 17 * * *   False     0         <none>          23s
```

* after the job to restart `iotagent-ul` fired

```bash
$ kubectl get cronjobs
NAME                    SCHEDULE     SUSPEND   ACTIVE    LAST SCHEDULE   AGE
iotagent-ul-resterter   0 17 * * *   False     0         5h              17h
```
```bash
$ kubectl get jobs
NAME                               DESIRED   SUCCESSFUL   AGE
iotagent-ul-resterter-1534957200   1         1            5h
```
```bash
$ kubectl describe deployments iotagent-ul
Name:                   iotagent-ul
Namespace:              default
CreationTimestamp:      Fri, 17 Aug 2018 19:12:25 +0900
#...(snip)...
Pod Template:
  Labels:       app=iotagent-ul
  Annotations:  lastUpdate=2018-08-22T17:00:10.1534957210Z
  Containers:
   iotagent-ul:
    Image:        ogcacr.azurecr.io/tech-sketch/iotagent-ul:1.7.0.plus
#...(snip)...
```
```bash
$ kubectl get replicasets -l app=iotagent-ul
NAME                     DESIRED   CURRENT   READY     AGE
iotagent-ul-7d5d4fdc67   0         0         0         5d
iotagent-ul-7fbd59976    3         3         3         5h
```
```bash
$ kubectl get pods -l app=iotagent-ul
NAME                          READY     STATUS    RESTARTS   AGE
iotagent-ul-7fbd59976-g9djb   1/1       Running   0          5h
iotagent-ul-7fbd59976-ltcd2   1/1       Running   0          5h
iotagent-ul-7fbd59976-rgk6g   1/1       Running   0          5h
```
