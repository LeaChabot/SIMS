COUNT=1
for P in 0.01 0.02 0.03 0.04 0.05 0.06 0.07 0.08 0.09 
do
    export PROP=${P} && export COUNT=${COUNT} && envsubst < yaml/ablation.yaml | kubectl create -f -
    (( COUNT++ ))
done 
