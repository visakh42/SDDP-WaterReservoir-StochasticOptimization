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
w = capData.index.tolist()
ft = capData.columns.tolist()
h = ["h" + str(i) for i in range(1,24*7+1)]

demand = demData.iloc[:,1].tolist()
demand = {i:demand[t.index(i)] for i in t}

exchange = flowData.iloc[:,1].tolist()
tlist = flowData.iloc[:,0].tolist()
exchange = {i:exchange[tlist.index(i)] for i in tlist}
for i in t:
    if i not in exchange:
        exchange[i]=0


wlist = capData.index.tolist()
print(wlist)
wcapacity = {}
for f in ft:
    wcapacitylist = capData[f].tolist()
    for j in wlist:
        wcapacity[(j,f)] = wcapacitylist[wlist.index(j)]


wlist = priceData.index.tolist()
flist = priceData.columns.tolist()

wprices = {}
for f in flist:
    wpricelist = priceData[f].tolist()
    for j in wlist:
        wprices[(j,f)] = wpricelist[wlist.index(j)]

wlist = inflowData.iloc[:,0].tolist()
winflow = inflowData.iloc[:,1].tolist()
winflow = {i:winflow[wlist.index(i)] for i in wlist}

wlist = stochInflowData.index.tolist()
slist = stochInflowData.columns.tolist()
swinflow = {}
for s in slist:
    swinflowlist = stochInflowData[s].tolist()
    for j in wlist:
        swinflow[(s,j)] = swinflowlist[wlist.index(j)]

resmax = {i:106.2e6 if i!='t8736' else 87e6 for i in t}
resmin = {i:10e6 if i!='t8736' else 87e6 for i in t}

wt = []
last = []
first = []
p=0
for i in w:
    for j in h:
        wt.append((i,t[p]))
        if h.index(j)==0:
            last.append((i,t[p]))
        if h.index(j)==len(h)-1:
            first.append((i,t[p]))
        p = p+1    

# wt = tuplelist(wt)
# first = tuplelist(first)
# last = tuplelist(last)

inflow = {i:sum(winflow[j] for j in w if (j,i) in wt)/len(h) for i in t}

capacity = {(i,f):sum(wcapacity[j,f] for j in w if (j,i) in wt) for i in t for f in ft}

gencost = {(i,f):0 if f=="Hydro" else 15 for i in t for f in ["Hydro","Nuclear"] }
for i in t:
    gencost[(i,"HardCoal")] = sum(wprices[j,"HardCoal"] for j in w if (j,i) in wt) + ((2.361*sum(wprices[j,'CO2'] for j in w if (j,i) in wt))/(6.98*0.39))
#############

##########
for i in t:
    if i not in exchange:
        exchange[i]=0
############

capacityKeys = capacity.keys()
##########################################################
#Creating Model
m = Model('DeterministicDam')

#Creating variables
gap = m.addVars(t,name = 'gap') ##Gap generation in T
res = m.addVars(t,name = 'res') ##reservoir energy level at end in T
spill = m.addVars(t,name = 'spill') ##Spillafe in hour t
x = m.addVars(t,ft,name = 'x') ##Generated power in hour t with ft
slackup = m.addVars(t,name = 'slackup') ##Slack for the upper level
slacklo = m.addVars(t,name = 'slacklo') ##Slack for the lower level
                   
#update model
m.update()

#Creating constraints
m.addConstrs(((res[i] - res[t[t.index(i)-1]] + x[i,'Hydro'] + spill[i] == inflow[i]) for i in t) , "Hydraulic continuity" )
m.addConstrs(((quicksum(x[i,f] for f in ft if (i,f) in capacityKeys)  + gap[i] >= demand[i] - exchange[i]) for i in t) , "Demand Satisfaction" )
m.addConstrs(((-res[i] + slackup[i] >= -resmax[i]) for i in t) , "Maximum reservoir level" )
m.addConstrs(((res[i] + slacklo[i] >= resmin[i]) for i in t) , "Minimum reservoir level" )
m.addConstrs(((-x[i,f] >= -capacity[i,f]) for i in t for f in ft if (i,f) in capacityKeys) , "Minimum reservoir level" )

#Setting objective
m.setObjective(
        (
        quicksum(gencost[i,f]*x[i,f] for i in t for f in ft if (i,f) in capacityKeys)
        + 1000*quicksum(gap[i] for i in t)
        + 10e6*quicksum(slackup[i]+slacklo[i] for i in t)
        )
        ,GRB.MINIMIZE)

m.update()


#optimize
m.optimize()

status = m.status
if status == GRB.Status.UNBOUNDED:
    print('The model cannot be solved because it is unbounded')
if status == GRB.Status.OPTIMAL:
    print('The optimal objective is %g' % m.objVal)
if status != GRB.Status.INF_OR_UNBD and status != GRB.Status.INFEASIBLE:
    print('Optimization was stopped with status %d' % status)




