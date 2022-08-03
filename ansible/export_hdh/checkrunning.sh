for i in {b,c,e,h}; do echo ------------------------------bgdt${i}1.oxa; ssh bgdt${i}1.oxa pgrep -f -u francisco .*python.*dpiste.*export.*; done
