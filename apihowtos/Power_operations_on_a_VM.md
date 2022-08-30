```secret
username=
password=
```

```env
apiurl=https://linatest.bcn.abiquo.com:443/api
vmlabel=yVM_mj
version=5.2
```

Power operations on a VM
========================

Here is a set of basic VM power operations
1. Perform a GET request to retrieve the VM by label
2. Obtain the VM state link and the VM reset link
3. Send a PUT request with a shutdown virtualmachinestate object to the VM state link
4. Send a PUT request with a start virtualmachinestate object to the VM state link
5. Sent a POST request to the VM reset link


Get the Abiquo token
--------------------
```bash
curl -s -v -k https://linatest.bcn.abiquo.com/api/login -u $username:$password 2>&1 >/dev/null | sed -n -e 's/^\< X-Abiquo-Token: //p'
```


Get the state of the VM
-----------------------
Who knows what the VM is doing!

```bash
curl -X GET "$apiurl/cloud/virtualmachines?vmlabel=$vmlabel" \
  -v -k -u $username:$password | jq '.collection[0].state'
```

Get the VM state link
---------------------
Perform a GET request to get the VM by its friendly name and obtain the URL of the State link entity.

```bash
curl -X GET "$apiurl/cloud/virtualmachines?vmlabel=$vmlabel" \
  -k -u $username:$password | jq -r '.. | objects | select(.rel=="state") | .href' > statelink.txt
```

Shut down the VM
----------------
Perform a PUT request to the State URL with a shutdown state object.
```bash
curl -X PUT `cat statelink.txt` \
  -H "Accept: application/vnd.abiquo.acceptedrequest+json; version=$version" \
  -H "Content-Type: application/vnd.abiquo.virtualmachinestate+json; version=$version" \
  -d '{"state": "OFF"}' \
  -k -u $username:$password | jq .
```

Get the VM's Reset link
-----------------------
While the VM is shutting down, get the Reset link to fill in time!

```bash
curl -X GET "$apiurl/cloud/virtualmachines?vmlabel=$vmlabel" \
  -k -u $username:$password | jq -r '.. | objects | select(.rel=="reset") | .href' > resetlink.txt
```

Sleep for 100 while waiting for the VM...
```bash
echo "Sleep for 100 while waiting for the VM to shut down"
for x in `seq 0 100`; do
    sleep 1
done
```


Start up the VM
---------------
Perform a PUT request to the State link with a startup state object.
```bash
curl -X PUT `cat statelink.txt` \
  -H "Accept: application/vnd.abiquo.acceptedrequest+json; version=$version" \
  -H "Content-Type: application/vnd.abiquo.virtualmachinestate+json; version=$version" \
  -d '{"state": "ON"}' \
  -k -u $username:$password | jq .
```

Sleep for 100 while waiting for the VM...
```bash
echo "Sleep for 100 while waiting for the VM to start up"
for x in `seq 0 100`; do
    sleep 1
done
```



Reset the VM
------------
Perform a POST request to the Reset link
```bash
curl -X POST `cat resetlink.txt` \
  -k -u $username:$password | jq .
```

The End! :-) 
