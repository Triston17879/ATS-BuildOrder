# optimizer values
import sys
sys.setrecursionlimit(2500)

# how many states do we want to keep?
TRACK_NUM = 100
# Constant values for buildings

# matter cost, energy cost, logistics cost, time, matter production, energy production, logistics production, max matter, max energy
economyBuildings = []
'''matter cost(0), energy cost(1), logistics cost(2), time(3), matter production(4), energy production(5), logistics(6), max matter(7), max energy(8)'''

# base stats
maxMatter = 100
matter = 100
maxEnergy = 100
energy = 100 
logistics = 100
time = 0
power = 0.0

economyBuildingsCount = []

# how many, time to next production cycle (we pretend they all produce at once)
militaryBuildingsCount = []

# what are we making(ids), is this an economy(1) or military(2) id, and when does it finish
queue = []
state = [maxMatter, matter, maxEnergy, energy, logistics, power, economyBuildingsCount, militaryBuildingsCount, queue, time]
'''maxMatter, matter, maxEnergy, energy, logistics, power, economyBuildingsCount, militaryBuildingsCount, queue, time'''
decisions = []
# later move into seperate files?

# coheser
economyBuildings.append((50, 0, 1, 7, 0.5, 0, 0, 0, 0))

# katalyst reactor
economyBuildings.append((20, 0, 0, 15, 0, 0.25, 0, 0, 0))

# cohesion facility
economyBuildings.append((200, 300, 10, 30, 5, 0, 0, 0, 0))

# graviton engine
economyBuildings.append((250, 50, 10, 45, 0, 5, 0, 0, 0))

# base core
economyBuildings.append((5, 10, 0, 10, 0, 0, 5, 0, 0))

# logic center
economyBuildings.append((60, 100, 0, 30, 0, 0, 60, 0, 0))

# matter silo
economyBuildings.append((5, 0, 0, 10, 0, 0, 0, 50, 0))

# energy vault
economyBuildings.append((5, 0, 0, 10, 0, 0, 0, 0, 20))

# refinery would go here but then you need to input how much "available" matter... do it Someday(tm)


# military buildings - abstract "power output" for now, just choose vaguely reasonable values... later maybe add "typing" or simulated combat, GAs to optimize
# defense buildings? Maybe later.

# matter, energy, logistics, build time, "power", production time(of smallest unit production time)
militaryBuildings = []
'''matter(0), energy(1), logistics(2), build time(3), power(4), production time(5)'''

# d4
militaryBuildings.append((30, 0, 4, 15, 2, 15))

# tolly as baseline unit, 1 power
# c1 
militaryBuildings.append((15, 0, 1, 10, 1, 15))

# m4
# reasoning: one otorell can oneshot a tolly with 55x3 damage, every 2.6s, if we pit against 5 it wins handily, struggles against fauss, hemmok(cant hit), or larger nums... feels like reasonable scaling?
militaryBuildings.append((40, 10, 2, 15, 5, 30))

#h9
# reasoning: massive hp pool and 40 armor, immune to most mediums, but terrible dps for cost... again these are vague estimates
militaryBuildings.append((100, 50, 6, 30, 30, 60))

# c25
# reasoning: one of these is a win button if opponent isnt prepared to handle armor/force mult/giant anti-heavy platform, can take on several abroundells
militaryBuildings.append((500, 250, 35, 60, 150, 400))

# redemption foundry aka win button
# reasoning: this thing cant be destroyed without wernos and even so will eat your fleet deathball with its infinite pierce, 12500 damage and 6000 heat will melt tradinos and damage eukodon, wipe all heavies
militaryBuildings.append((2000, 2000, 120, 60, 1200, 60))

for i in range(len(economyBuildings)):
    economyBuildingsCount.append(0) 

for i in range(len(militaryBuildings)):
    militaryBuildingsCount.append([0, militaryBuildings[i][5]])

# calculate one second of actions...
# "goal" is the endpoint optimizing for, milestones represent enemy pressure to avoid death, prunes solutions that don't pass
def estimateMinPower(state, goal):
    print('estimating')
    '''Estimates how much "power" a given state will have by the end assuming you stop building all eco. Terrible estimator right now, unused.'''
    maxMatter = state[0]
    matter = state[1]
    maxEnergy = state[2]
    energy = state[3]
    logistics = state[4]
    power = state[5]
    economyBuildingsCount = state[6]
    militaryBuildingsCount = state[7]
    queue = state[8]
    time = state[9]

    matterIncome = 0
    energyIncome = 0

    for i in range(len(economyBuildings)):
        buildingType = economyBuildings[i]
        matterIncome += buildingType[4] * economyBuildingsCount[i]
        energyIncome += buildingType[5] * economyBuildingsCount[i]
    
    while time < goal:
        matter, energy = min(matter + matterIncome, maxMatter), min(energy + energyIncome, maxEnergy)

        for i in range(len(militaryBuildings)):
            militaryBuildingsCount[i][1] -= 1
            if militaryBuildingsCount[i][1] <= 0:
                power += militaryBuildings[i][4]
                militaryBuildingsCount[i][1] = militaryBuildings[i][5]

        for i in range(len(queue)):
            building = queue[i]
            id = building[0]
            time = building[2]
            time -= 1

            # economy
            if building[1] == 1:
                if time <= 0:
                    buildingType = economyBuildings[id]
                    logistics += buildingType[6]
                    maxMatter += buildingType[7]
                    maxEnergy += buildingType[8]
                    economyBuildingsCount[id] += 1

            # military
            if building[2] == 1:
                if time <= 0:
                    militaryBuildingsCount[id][0] += 1
        
        # yes its terrible (will always buy cheapest, ignores logistics) but too lazy to fix right now... fix after grounding yard production values... or rip out and replace with a calculator that finds the best ratio it can afford as a lazy heuristic
        for i in range(len(militaryBuildings)):
            building = militaryBuildings[i]
            if (matter, energy > building[0], building[1]):
                matter -= building[0]
                energy -= building[1]
                logistics -= building[2]
                queue.append(i, 1, building[3])
        
        time += 1
    return power

def calculateTick(state, decisions, passTime, goal, milestones):
    '''Calculates one second of actions and brute-forces every possible state. Returns the end state and build order as a tuple.'''
    time = state[9]
    if time >= goal:
        # print(f"Finished run with state: {state}")
        return (state, decisions)
    
    maxMatter = state[0]
    matter = state[1]
    maxEnergy = state[2]
    energy = state[3]
    logistics = state[4]
    power = state[5]
    economyBuildingsCount = state[6]
    militaryBuildingsCount = state[7]
    queue = state[8]

    if passTime:  
        time += 1
        # base income from light platform
        matterIncome = 2.5
        energyIncome = 1

        for i in range(len(economyBuildings)):
            buildingType = economyBuildings[i]
            matterIncome += buildingType[4] * economyBuildingsCount[i]
            energyIncome += buildingType[5] * economyBuildingsCount[i]
        
        matter, energy = min(matter + matterIncome, maxMatter), min(energy + energyIncome, maxEnergy)

        for i in range(len(militaryBuildings)):
            militaryBuildingsCount[i][1] -= 1
            if militaryBuildingsCount[i][1] <= 0:
                power += militaryBuildings[i][4]
                militaryBuildingsCount[i][1] = militaryBuildings[i][5]

        for i in range(len(queue)):
            building = queue[i]
            id = building[0]
            building[2] -= 1

            # economy
            if building[1] == 1:
                if building[2] <= 0:
                    buildingType = economyBuildings[id]
                    logistics += buildingType[6]
                    maxMatter += buildingType[7]
                    maxEnergy += buildingType[8]
                    economyBuildingsCount[id] += 1
                    del building

            # military
            elif building[2] == 1:
                if time <= 0:
                    militaryBuildingsCount[id][0] += 1
                    del building
    state = [maxMatter, matter, maxEnergy, energy, logistics, power, economyBuildingsCount, militaryBuildingsCount, queue, time]
    if matter < 15:
        return(calculateTick(state, decisions, True, goal, milestones))
    
    else:
        endStates = []
        # print("Able to build, waiting...")
        # print(time, matter, energy) 
        endStates.append(calculateTick(state, decisions, True, goal, milestones))
        for i in range(len(economyBuildings)):
            building = economyBuildings[i]
            if (matter >= building[0] and energy >= building[1] and logistics >= building[2]):
                # print(f"Trying to build economy with id {i}")
                matter -= building[0]
                energy -= building[1]
                logistics -= building[2]
                queue.append([i, 1, building[3]])
                decisions = decisions + (f"\nBuild economy building #{i} at {time}")
                state = [maxMatter, matter, maxEnergy, energy, logistics, power, economyBuildingsCount, militaryBuildingsCount, queue, time]
                endStates.append(calculateTick(state, decisions, False, goal, milestones))

        for i in range(len(militaryBuildings)):
            building = militaryBuildings[i]
            if (matter >= building[0] and energy >= building[1] and logistics >= building[2]):
                # print(f"Trying to build military with id {i}")
                matter -= building[0]
                energy -= building[1]
                logistics -= building[2]
                queue.append([i, 1, building[3]])
                decisions = decisions + (f"\nBuild military building #{i} at {time}")
                state = [maxMatter, matter, maxEnergy, energy, logistics, power, economyBuildingsCount, militaryBuildingsCount, queue, time]
                endStates.append(calculateTick(state, decisions, False, goal, milestones))
        
        highestSeen = 0
        currentHighest = None
        # print(len(endStates))
        for i in range(len(endStates)):
            # print(i)
            try:
                endState = endStates[i]
                # print(endState[0][5])
                power = endState[0][5]
                if power > highestSeen:
                    highestSeen = power
                    currentHighest = endState
            except:
                print("oh noes")
        return currentHighest
    

    


milestones = [(int, float)]
'''TODO: Make milestones work. time(seconds), power'''

goal = 2
'''end time(seconds)'''

print(calculateTick(state, "", False, goal, milestones))
print("done")