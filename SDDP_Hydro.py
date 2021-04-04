from gurobipy import *
import pandas as pd
import project_data as data
import random
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
resmax = data.resmax
resmin = data.resmin
s = data.slist
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
inflow = data.inflow
capacity = data.capacity
gencost = data.wgencost ## 
capacityKeys = capacity.keys()

w = w[:8]
#s = s[:3]
t  = w
resmax = 106.2e6 #data.resmax
resmin = 10e6 #data.resmin
wdemand = {a:0 for a in wlist}
wexchange = {a:0 for a in wlist}
#wcapacity = {(a,f):0 for a in wlist for f in ft}
for (x,y) in wt:
    wdemand[x] += demand[y]
    wexchange[x] += exchange[y] 
    # for f in ft:
    # 	wcapacity[x,f] += capacity[y,f]
capacity = data.wcapacity   
#print(wcapacity)
##########################################################
#Creating Model
m = Model('SDDP_Hydro')
m.params.logtoconsole=0
#Creating variables
gap = m.addVars(t,name = 'gap') ##Gap generation in T
res = m.addVars(t,name = 'res') ##reservoir energy level at end in T
spill = m.addVars(t,name = 'spill') ##Spillafe in hour t
x = m.addVars(t,ft,name = 'x') ##Generated power in hour t with ft
slackup = m.addVars(t,name = 'slackup') ##Slack for the upper level
slacklo = m.addVars(t,name = 'slacklo') ##Slack for the lower level
alpha = m.addVars(t,name = 'alpha')               
#update model
m.update()

#Creating constraints
hyd = m.addConstrs(((res[i] - res[t[t.index(i)-1]] + x[i,'Hydro'] + spill[i] <= winflow[i]) for i in t if i!= 'w1') , "Hydraulic continuity" )
m.addConstrs(((quicksum(x[i,f] for f in ft if (i,f) in capacityKeys)  + gap[i] >= wdemand[i] - wexchange[i]) for i in t) , "Demand Satisfaction" )
m.addConstrs(((-res[i] + slackup[i] >= -resmax) for i in t) , "Maximum reservoir level" )
m.addConstrs(((res[i] + slacklo[i] >= resmin) for i in t) , "Minimum reservoir level" )
m.addConstrs(((-x[i,f] >= capacity[i,f]) for i in t for f in ft if (i,f) in capacityKeys) , "Capacity limit" )
#hyd1 = m.addConstr((res['w1'] - resmin + x['w1','Hydro'] + spill['w1'] == winflow['w1']) , "Hydraulic continuity" )
#Setting objective
# m.setObjective(
#         (
#         quicksum(gencost[i,f]*x[i,f] for i in t for f in ft if (i,f) in capacityKeys)
#         + 1000*quicksum(gap[i] for i in t)
#         + 10e6*quicksum(slackup[i]+slacklo[i] for i in t)+ quicksum(alpha[i] for i in w)
#         )
#         ,GRB.MINIMIZE)

m.update()


converge = 1
resVal = {}
objVal = {}
iteration = 0
ub_it = {}
lb_it = {}


while converge == 1 and iteration < 100:
	ub_trial = {}
	lb_trial = {}

	iteration = iteration + 1
	Cons = {}
	trialSet = random.sample(s,3)
	hyd1 = m.addConstr((res['w1'] - resmin + x['w1','Hydro'] + spill['w1'] == winflow['w1']) , "Hydraulic continuity" )
	for trial in trialSet:
		ub_trial[trial]=0.0
		m.reset()
		for weeks in w:
			# Optimize and get the reservoir level values per week 
			# (Used deterministic inflow)
			print(trial, weeks)
			if weeks == 'w1':

				hyd1.RHS = swinflow[trial,'w1']
			else:
				hyd[weeks].RHS = swinflow[trial,weeks]
				print(swinflow[trial,weeks])


			if weeks == w[-1]:

				m.setObjective((quicksum(gencost[weeks,f]*x[weeks,f] for f in ft if (weeks,f) in capacityKeys)
							+ 1000*(gap[weeks])
							+ 10e6*(slackup[weeks]+slacklo[weeks])),GRB.MINIMIZE) # NO alpha here
				
			else:
				m.setObjective((quicksum(gencost[weeks,f]*x[weeks,f] for f in ft if (weeks,f) in capacityKeys)+ 1000*gap[weeks]+10e6*(slackup[weeks]+slacklo[weeks])+ alpha[w[w.index(weeks)+1]]),GRB.MINIMIZE)
			m.update()
			m.optimize() 
			resVal[(trial,weeks)] = res[weeks].X
			objVal[(trial,weeks)] = m.objval

			if weeks != w[-1]:
				nextWeek = w[w.index(weeks)+1]
				ub_trial[trial] += (m.objval - alpha[nextWeek].X)
			else:
				ub_trial[trial] += (m.objval)

			if weeks == w[0]:
				lb_trial[trial]=m.objval
			# Fix res level using the previous week
			# if weeks !='w1':
			# 	m.remove(Cons[w[w.index(weeks)-1]])
			# 	m.Update()
			Cons[weeks] = m.addConstr(res[weeks] == resVal[(trial,weeks)],"ForwardPassFix")

		for i in w:
			m.remove(Cons[i])
			m.update()
		#print(resVal)
		#print(objVal)
		# Set the lower bound to week 1's objective value.
		lb = objVal[(trial,'w1')]
	for i in w:
			m.remove(Cons[i])
			m.update()
	m.remove(hyd1)
	## Backward Pass
	Benders = []

	ub_it[iteration]= sum(i for i in ub_trial.values())/len(trialSet)
	lb_it[iteration]= sum(i for i in lb_trial.values())/len(trialSet)

	for trial in trialSet:
		# for weeks in w:
		# 	# Fixing the res
		# 	Cons[weeks] = m.addConstr(res[weeks] == resVal[(trial,weeks)],"FixResVal")
		# 	m.update()

		for consts in Benders:
			m.remove(consts)
			m.update()
		Benders = []
		# Starting from last week
		for weeks in w[::-1]:
			prevWeek  = w[w.index(weeks)-1]
			
			#m.remove(Cons[weeks])
			m.update()
			m.reset()
			for scen in s:
				print(trial,weeks,scen)
				prevWeek  = w[w.index(weeks)-1]
				fix1 = m.addConstr(res[prevWeek] >= resVal[(trial,prevWeek)],"backwardPassFix1")
				fix2 = m.addConstr(res[prevWeek] <= resVal[(trial,prevWeek)],"backwardPassFix2")
				m.update()
				m.reset()
				if weeks == 'w1':
					hyd1 = m.addConstr((res['w1'] - resmin + x['w1','Hydro'] + spill['w1'] == swinflow[scen,'w1']) , "HydraulicContinuity" )
					#hyd1.RHS = swinflow[scen,'w1']
				else:
					hyd[weeks].RHS = swinflow[scen,weeks]
					print(swinflow[scen,weeks])


				if weeks == w[-1]:
					m.setObjective((quicksum(gencost[weeks,f]*x[weeks,f] for f in ft if (weeks,f) in capacityKeys)
								+ 1000*(gap[weeks])
								+ 10e6*(slackup[weeks]+slacklo[weeks])),GRB.MINIMIZE)
					
				else:
					# Constraint - Bender's cuts
					m.setObjective((quicksum(gencost[weeks,f]*x[weeks,f] for f in ft if (weeks,f) in capacityKeys)+ 1000*gap[weeks]+10e6*(slackup[weeks]+slacklo[weeks])+ alpha[w[w.index(weeks)+1]]),GRB.MINIMIZE)
				
				m.write("check.lp")
				m.update()
				m.reset()
				m.optimize()
				status = m.status
				if status == GRB.Status.INFEASIBLE:
					m.computeIIS()
					m.write("INFEASIBLE.ilp")
				obj  = m.objval
				# Get lambda
				if weeks == 'w1':
					lamdaVal = hyd1.Pi	
				else:
					lamdaVal = hyd[weeks].Pi
				# Add Benders cuts - For every scenario - Multicuts
					Benders.append(m.addConstr(alpha[weeks] >= obj - (lamdaVal*resVal[trial,prevWeek]) + (lamdaVal*res[prevWeek])))
					
					m.update()	
				m.remove(fix1)
				m.remove(fix2)
				if weeks==w[0]:
					m.remove(hyd1)
				m.update()
				m.reset()
				
			#BendersCuts[()] = m.addConstr((alpha[] ))
		# Remove the Benders

				# Get Benders' cut 
	if iteration > 20:
		converge = 0
	for i in ub_it.keys():
		print("bounds")
		print(lb_it[i],ub_it[i])

	






