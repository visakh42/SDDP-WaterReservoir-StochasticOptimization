from gurobipy import *
import pandas as pd

import project_data as data

t = data.t
w = data.w
ft = data.ft 
h = data.h
demand = data.demand
exchange = data.exchange
wlist = data.wlist
wcapacity = data.wcapacity
flist = data.flist
wprices = data.wprices
winflow = data.winflow
swinflow = data.swinflow
resmax = 106.2e6 #data.resmax
resmin = 10e6 #data.resmin

wt = data.wt
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

# wt = tuplelist(wt)
# first = tuplelist(first)
# last = tuplelist(last)

demandNew = {a:0 for a in wlist}
exchangeNew = {a:0 for a in wlist}
wcapacity = data.wcapacity# {(a,f):0 for a in wlist for f in ft}

for (x,y) in wt:
    demandNew[x] += demand[y]
    exchangeNew[x] += exchange[y] 
s = data.slist # Contains the list pf scenarios

inflow = data.inflow  ## Not used 
capacity = wcapacity #data.wcapacity
gencost = data.wgencost  ## Weekly 
capacityKeys = capacity.keys()


n= [] # Node List
timeN={}
ancestorN= {}
scenN = {}
j=0
root = [0]
p = {}
####
w = w[:8]
#s = s[:3]
p[0] = 1
timeN[0] = 'w0'
for weeks in w:
	prev = root
	root = []

	for nodes in prev:
		for scen in s:
			j+=1
			n.append(j)
			timeN[j] = weeks
			ancestorN[j] = nodes
			scenN[j] = scen
			p[j] = (1/len(s))*p[nodes]
			root.append(j)
print(n)
# print(timeN)
# print(ancestorN)
# print(p)

Nlist  = n +[0]
##########################################################
#Creating Model
m = Model('NodeDam')

#Creating variables
gap = m.addVars(n,name = 'gap') ##Gap generation in T
res = m.addVars(n,name = 'res') ##reservoir energy level at end in T
spill = m.addVars(n,name = 'spill') ##Spillafe in hour t
x = m.addVars(n,ft,name = 'x') ##Generated power in hour t with ft
slackup = m.addVars(n,name = 'slackup') ##Slack for the upper level
slacklo = m.addVars(n,name = 'slacklo') ##Slack for the lower level
                   
#update model
m.update()

#Creating constraints
#m.addConstr(res[0] == resmax, "Initial reservoir level")
m.addConstrs(((res[i] - res[ancestorN[i]] + x[i,'Hydro'] + spill[i] == swinflow[scenN[i],timeN[i]]) for i in  n if ancestorN[i]!=0) , "Hydraulic continuity" )
m.addConstrs(((quicksum(x[i,f] for f in ft if (timeN[i],f) in capacityKeys)  + gap[i] >= demandNew[timeN[i]] - exchangeNew[timeN[i]]) for i in n) , "Demand Satisfaction" )
m.addConstrs(((-res[i] + slackup[i] >= -resmax) for i in n) , "Maximum reservoir level" )
m.addConstrs(((res[i] + slacklo[i] >= resmin) for i in n) , "Minimum reservoir level" )
m.addConstrs(((-x[i,f] >= -capacity[timeN[i],f]) for i in n for f in ft if (timeN[i],f) in capacityKeys) , "Minimum reservoir level" )
m.addConstrs(((res[i] - resmin + x[i,'Hydro'] + spill[i] == swinflow[scenN[i],timeN[i]]) for i in n if ancestorN[i] == 0 ) , "Hydraulic continuity For Node1" )
#Setting objective
m.setObjective(
        (
        quicksum(gencost[timeN[i],f]*x[i,f] for i in n for f in ft if (timeN[i],f) in capacityKeys)
        + 1000*quicksum(gap[i] for i in n)
        + 10e6*quicksum(slackup[i]+slacklo[i] for i in n)
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