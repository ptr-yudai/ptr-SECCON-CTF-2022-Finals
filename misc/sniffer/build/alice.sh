#!/bin/sh
cd /home/pi; \
    export FLAG1="SECCON{c4bl3_ch0k1ch0k1}"; \
    export FLAG2="SECCON{DH_1s_n0t_s4f3_4g41n5t_p4ck3t_m4n1pul4t10n}"; \
    nohup python alice.py &
