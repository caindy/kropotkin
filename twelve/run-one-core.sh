cd ~/projects/kropotkin/core; export TARGET=$1 PORT=$2 TEST_PORT=3141; ./run.rkt >> /tmp/$TARGET.log 2>&1 &