for i in {b,c,e,h}; do echo ------------------------------bgdt${i}1.oxa; ssh bgdt${i}1.oxa tail -n 100 -f /space/Work/francisco/deep.piste/out.log; done
