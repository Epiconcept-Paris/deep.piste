ssh bgdth1.oxa 'echo ls -l dpiste/screening/*/*/* | sftp -b - HDH_deeppiste@procom2.front2' | awk '{sum+=$5;count+=1;} END{print count; print sum/(1024*1024);}'
