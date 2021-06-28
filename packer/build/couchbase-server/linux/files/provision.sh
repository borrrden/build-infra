# Wait for any ongoing yum stuff to happen before we start installing things
while ps -ef | grep 'yum' | grep -v 'grep'
do
     sleep 5
done

sudo yum install -y \
    aws-cli \
    bc \
    docker \
    ec2-instance-connect \
    jq \
    lvm2 \
    nano \
    python3 \
    python3-pip

# start_worker needs to parse our yaml stackfiles
sudo pip3 install pyyaml

sudo mv /tmp/bootstrap /usr/bin
sudo chmod a+x /usr/bin/bootstrap

sudo mkdir /opt/buildteam

echo "${REGION}" | sudo tee /opt/buildteam/region

echo "region: $(</opt/buildteam/region)"
