from common import *
v5=load(V5); v4=load(V4); ref=load(REF)
print('frame mean L: v4 %.3f v5 %.3f ref %.3f'%(luma(v4).mean(),luma(v5).mean(),luma(ref).mean()))
# check ids alignment: lamp post mask should be dark in v5
for k in G:
    m=idm(k); print(k, m.sum(), 'v5', stats(v5,m,'')[0:0] , end=' ')
    print(stats(v5,m,k))
print()
for k in ['notice','board','drum','chair','lantern','pail','lamp post','left lamp','handcart','dustbins','sacks','gates']:
    m=idm(k); print(stats(v4,m,'v4 '+k)); print(stats(v5,m,'v5 '+k))
