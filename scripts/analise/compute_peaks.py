# Dia de maior e menor expressão de cada dimensão do humor -> peaks.json
import json
C=json.load(open('cross.json'))
NM=['Vigor','Fadiga','TMD','Tensao','Depressao','Raiva','Confusao']
peaks={}
for k in NM:
    days={int(d):v for d,v in C['dec'][k]['dm'].items()}
    mxd=max(days,key=days.get); mnd=min(days,key=days.get)
    peaks[k]=dict(max_day=mxd,max_val=round(days[mxd],2),min_day=mnd,min_val=round(days[mnd],2))
json.dump(peaks,open('peaks.json','w'),indent=1)
print('peaks.json:',{k:'D%d'%v['max_day'] for k,v in peaks.items()})
