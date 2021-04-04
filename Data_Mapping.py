from gurobipy import *
import pandas as pd

dir = "E:\\F18\\CS 719\\Project\\"
demData = pd.read_excel(dir+"water.xls",sheetname="t_Demand",header=0)
flowData = pd.read_excel(dir+"water.xls",sheetname="t_Flow",header=0)
capData = pd.read_excel(dir+"water.xls",sheetname="w_Capacity",header=1)
priceData = pd.read_excel(dir+"water.xls",sheetname="w_Prices",header=1)
inflowData = pd.read_excel(dir+"water.xls",sheetname="w_Inflow",header=0)
stochInflowData = pd.read_excel(dir+"water.xls",sheetname="sw_Inflow",header=1)



t = demData.iloc[:,0].tolist()
print("t = ",t)
w = capData.index.tolist()
print("w = ",w)
ft = capData.columns.tolist()
print("ft = ",ft)
h = ["h" + str(i) for i in range(1,24*7+1)]
print("h = ",h)

demand = demData.iloc[:,1].tolist()
demand = {i:demand[t.index(i)] for i in t}
print("demand = ",demand)

exchange = flowData.iloc[:,1].tolist()
tlist = flowData.iloc[:,0].tolist()
exchange = {i:exchange[tlist.index(i)] for i in tlist}
for i in t:
    if i not in exchange:
        exchange[i]=0
################################
# for i in t:
#     if i not in exchange:
#         exchange[i]=0
################################        

print("exchange = ",exchange)

wlist = capData.index.tolist()
print("wlist = ",wlist)

wcapacity = {}
for f in ft:
    wcapacitylist = capData[f].tolist()
    for j in wlist:
        wcapacity[(j,f)] = wcapacitylist[wlist.index(j)]
print("wcapacity = ",wcapacity)

wlist = priceData.index.tolist()
flist = priceData.columns.tolist()

print("flist = ",flist)

wprices = {}
for f in flist:
    wpricelist = priceData[f].tolist()
    for j in wlist:
        wprices[(j,f)] = wpricelist[wlist.index(j)]

# #print("wpricelist = ",wpricelist)
# print("wprices = ",wprices)

# wlist = inflowData.iloc[:,0].tolist()
# winflow = inflowData.iloc[:,1].tolist()
# winflow = {i:winflow[wlist.index(i)] for i in wlist}
# print("winflow = ",winflow)

# wlist = stochInflowData.index.tolist()
# slist = stochInflowData.columns.tolist()
# print("slist =",slist)
# swinflow = {}
# for s in slist:
#     swinflowlist = stochInflowData[s].tolist()
#     for j in wlist:
#         swinflow[(s,j)] = swinflowlist[wlist.index(j)]
# print("swinflow = ",swinflow)

# resmax = {i:106.2e6 if i!='t8736' else 87e6 for i in t}
# resmin = {i:10e6 if i!='t8736' else 87e6 for i in t}
# print("resmax = ",resmax)
# print("resmin = ",resmin)
# wt = []
# last = []
# first = []
# p=0
# for i in w:
#     for j in h:
#         wt.append((i,t[p]))
#         if h.index(j)==0:
#             last.append((i,t[p]))
#         if h.index(j)==len(h)-1:
#             first.append((i,t[p]))
#         p = p+1    

# # wt = tuplelist(wt)
# # first = tuplelist(first)
# # last = tuplelist(last)

# print("wt = ",wt)
# print("first = ",first)
# print("last = ",last)

# inflow = {i:sum(winflow[j] for j in w if (j,i) in wt)/len(h) for i in t}
# print("inflow = ", inflow)
# capacity = {(i,f):sum(wcapacity[j,f] for j in w if (j,i) in wt) for i in t for f in ft}
# print("capacity = ", capacity)
# gencost = {(i,f):0 if f=="Hydro" else 15 for i in t for f in ["Hydro","Nuclear"] }

# for i in t:
#     gencost[(i,"HardCoal")] = sum(wprices[j,"HardCoal"] for j in w if (j,i) in wt) + ((2.361*sum(wprices[j,'CO2'] for j in w if (j,i) in wt))/(6.98*0.39))
# print("gencost = ",gencost)
# capacityKeys = capacity.keys()
# print("capacityKeys = ",capacityKeys)

# ### For multistage scenario/node based : Weekly
# demandNew = {a:0 for a in wlist}
# exchangeNew = {a:0 for a in wlist}
# for (x,y) in wt:
#     demandNew[x] += demand[y]
#     exchangeNew[x] += exchnage[y] 
# print("demandNew = ",demandNew)
# print("exchangeNew =",exchangeNew)

## Weekly cost
wgencost = {}
wgencost = {(i,f):0 if f=="Hydro" else 15 for i in w for f in ["Hydro","Nuclear"] }

for i in w:
    wgencost[(i,"HardCoal")] = (wprices[i,"HardCoal"]) + ((2.361*wprices[i,'CO2'])/(6.98*0.39))
print("wgencost = ",wgencost)