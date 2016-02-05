import simpy as sp
import numpy as np
import matplotlib.pyplot as plt
plt.style.use('ggplot')


'''
Passengers with seats are sequenced according to some logic
Enter one at a time
Each aisle is a resource of capacity 1 that must be used to get to the next aisle
Using the aisle means walking across for some amount of time, dependent on walk speed
Upon reaching seat, while using aisle, put luggage away
Enter row of seats:  each seat is a resource as well
If some other passenger is in seat, passing seat resource requires extra time
There is no constraint on number of people in a seat, but will never be more than the number of seats per side


minimize loading time with various strategies
-represent strategies as weights on things like front to back, window to aisle, 
-genetic algorithm?  binary combinations of weights, choose randomly + mutation



'''


# seat_id:  (5, 3) = aisle seat on right?

NUM_AISLE = 10
NUM_SEATS_PER_SIDE = 3
SIDES=['L','R']

'''TIME'''
AISLE_TRAVERSE_TIME = 1
BAGGAGE_FIDDLY_TIME = 3
SEAT_TRAVERSE_TIME = 1
SEAT_TRAVERSE_OCCUPIED = 2

env = sp.Environment()
aisle_dict = {a:sp.Resource(env, capacity = 1) for a in range(NUM_AISLE)}
left_seats = {a:{i:sp.Resource(env, capacity=1) for i in range(NUM_SEATS_PER_SIDE)} for a in range(NUM_AISLE)}
right_seats = {a:{i:sp.Resource(env, capacity=1) for i in range(NUM_SEATS_PER_SIDE)} for a in range(NUM_AISLE)}

seat_is_occupied = {a:{s:{b:False for b in range(NUM_SEATS_PER_SIDE)} for s in SIDES} for a in range(NUM_AISLE) }
# print(left_seats)


''' To increase variability, make the baggage fiddly time random'''
def generate_baggage_fiddly_time():
	# V1:  Use simple discrete uniform
	while True:
		yield np.random.randint(2,8)+np.random.choice([0]*98+[1]*2)*20

# random number generator for baggage fiddly time
bag_time = generate_baggage_fiddly_time()



def traverse(env, passenger_num, seat_assgn, record):	
	ais_num, seat_num, side = seat_assgn
	aisle_path = [aisle_dict[i] for i in range(ais_num+1)]
	seat_path = [right_seats[ais_num][i] for i in range(seat_num+1)]
	if side=="L":
		seat_path = [left_seats[ais_num][i] for i in range(seat_num+1)]

	total_time = env.now
	print('Starting passenger',passenger_num)
	# walk to correct aisle
	for aisle in aisle_path[:-1]:
		# for each aisle, wait until empty and traverse
		print('Passenger',passenger_num,'entering aisle',aisle_path.index(aisle))
		with aisle.request() as req:
			yield req
			yield env.timeout(AISLE_TRAVERSE_TIME)
	last_aisle = aisle_path[-1]
	# in last aisle, occupy while putting away luggage
	with last_aisle.request() as req:
		print('Passenger',passenger_num,'entering last aisle',aisle_path.index(last_aisle))
		yield req
		yield env.timeout(AISLE_TRAVERSE_TIME+next(bag_time))
	
	for seat in seat_path:
		with seat.request() as req:
			print('Passenger',passenger_num,'entering seat',seat_path.index(seat))
			yield req
			if seat_is_occupied[ais_num][side][seat_num]:
				yield env.timeout(SEAT_TRAVERSE_OCCUPIED)
			else:
				yield env.timeout(SEAT_TRAVERSE_TIME)
	seat_is_occupied[seat_path[-1]] = True
	total_time = env.now-total_time
	print('Passenger %d seated after time %d' % (passenger_num, total_time))
	record.append((passenger_num, total_time))



def generate_seat_sequence(sorting_style):
	# output: list  (7,1,L) = (aisle 7, seat 1, side left)
	seat_seq = []
	[[[seat_seq.append((a,i,s)) for s in SIDES] for i in range(NUM_SEATS_PER_SIDE)] for a in range(NUM_AISLE)]
	
	# default: sorted sequence by aisle, row, and side
	seat_seq.sort()

	if sorting_style == 'random':
		seat_seq = [seat_seq[i] for i in np.random.choice(range(len(seat_seq)), len(seat_seq), replace = False)]
	
	if sorting_style == 'window_first':
		seat_seq = sorted(seat_seq, key = lambda x:-x[0]) #last aisle loaded first
		seat_seq = sorted(seat_seq, key = lambda x:-x[1]) # window loaded first

	if sorting_style == 'aisle_first':
		seat_seq = sorted(seat_seq, key = lambda x:-x[0]) # last aisle loaded first
		seat_seq = sorted(seat_seq, key = lambda x:x[1]) # aisle loaded first

	if sorting_style == 'rev_alternating_rows':
		seat_seq = sorted(seat_seq, key = lambda x:-x[0]) #last aisle loaded first
		seat_seq = sorted(seat_seq, key = lambda x:-x[1]) # window loaded first
		seat_seq = sorted(seat_seq, key = lambda x:x[0]%2) # even rows first


	return seat_seq

algo = 'random'
algo = 'rev_alternating_rows'
algo = 'None'
seat_seq = generate_seat_sequence(algo)
# a record list to keep track of the time spent finding a seat
record = []
# initiate all passengers at front of plane
[env.process(traverse(env, i, seat_seq[i], record)) for i in range(NUM_AISLE*NUM_SEATS_PER_SIDE*2)]
# start all loading
env.run()

# When simulation is finished, create a chart
x,y =zip(*record)
plt.bar(x,y, width = .5, align = 'center')
plt.title('Time to Find Seat, '+algo+' Assignment')
plt.xlabel("Passenger")
plt.ylabel('Time (seconds)')
plt.show()




