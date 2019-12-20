import sys
import socket
import time
import threading

UPDATE_INTERVAL = 1
file = sys.argv[1]
network = {}  # {'A': {'B': '6.5', 'C': '2.2'}}
ROUTE_UPDATE_INTERVAL = 30

# get file information
with open(file) as f:
    neighbours = {}  # {'B': {'cost': '6.5', 'port': '5001'}, 'F': {'cost': '2.2', 'port': '5005'}}
    for line in f:
        if len(line.split(' ')) == 2:
            router_id = line.split(' ')[0]
            router_port = line.split(' ')[1].replace('\n', '')
        elif len(line.split()) == 3:
            neighbour = line.split(' ')[0]
            cost = line.split(' ')[1]
            port = line.split(' ')[2].replace('\n', '')
            neighbours[neighbour] = {'cost': cost, 'port': port}
        else:
            continue
neighbours_cost = {}
for neighbour in neighbours:
    neighbours_cost[neighbour] = neighbours[neighbour]['cost']
network[router_id] = neighbours_cost  # network dictionary initialization
send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receive_time = {}


# boardcast thread
def boardcast():
    seq = 0
    while True:
        ls_packet = ''
        for neighbour in neighbours:
            ls_packet += str(seq) + ' ' + router_id + ' ' + router_port + ' ' + neighbour + ' ' + neighbours[neighbour]['cost'] + ' ' +\
                neighbours[neighbour]['port'] + '\n'
        ls_packet = ls_packet.strip('\n')
        for neighbour in neighbours:
            send_socket.sendto(bytes(ls_packet, 'utf-8'), ('127.0.0.1', int(neighbours[neighbour]['port'])))
        seq = seq + 1
        time.sleep(1)


# receive thread
def receive():
    receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receive_socket.bind(('127.0.0.1', int(router_port)))
    receive_seq = {}
    # receive time initialization
    for neighbour in neighbours:
        receive_time[neighbour] = time.time()
    while True:
        packet, address = receive_socket.recvfrom(2048)
        received_packet = packet.decode()
        for r in receive_time:
            if time.time() - receive_time[r] > 10 * UPDATE_INTERVAL:
                if r in network:
                    network.pop(r)
                    receive_seq[r] = []
        packet_sender = received_packet.split('\n')[0].split(' ')[1]  # find packet sender
        packet_seq = received_packet.split('\n')[0].split(' ')[0]  # packet sequence
        packet_information = received_packet.split('\n')
        neighbours_cost = {}
        received_neighbour = []
        # read packet information
        for i in packet_information:
            received_neighbour.append(i.split(' ')[3])
            neighbours_cost[i.split(' ')[3]] = i.split(' ')[4]
        if packet_sender not in receive_seq:
            receive_seq[packet_sender] = [packet_seq]
            receive_time[packet_sender] = time.time()
        # update network and forward
        else:
            if packet_seq not in receive_seq[packet_sender]:
                receive_seq[packet_sender].append(packet_seq)
                receive_time[packet_sender] = time.time()  # 当接收到新的包时，如果这个包没收到过就记录他的时间
                network[packet_sender] = neighbours_cost
                for neighbour in neighbours:
                    if neighbour != packet_sender and neighbour not in received_neighbour:
                        send_socket.sendto(bytes(received_packet, 'utf-8'), ('127.0.0.1', int(neighbours[neighbour]['port'])))


# dijkstra algorithm
def dijkstra():
    while True:
        time.sleep(ROUTE_UPDATE_INTERVAL)
        nodes = [node for node in network]  # 找到网络中的所有router
        N = []
        if router_id in nodes:
            N.append(router_id)
        D = {}  # save distance cost
        p = {}  # save last node
        # distance cost initialization
        for v in nodes:
            if v == router_id:
                continue
            elif v in neighbours:
                D[v] = float(neighbours[v]['cost'])
            else:
                D[v] = float('inf')
        # find shortest distance cost
        while len(N) != len(nodes):
            min_cost = float('inf')
            for i in D:
                if i not in N:
                    if D[i] < min_cost:
                        min_cost = D[i]
            for j in D:
                if D[j] == min_cost and j not in N:
                    w = j
            N.append(w)
            for v in network[w].keys():
                if v == router_id:
                    continue
                elif v in network:
                    if D[w] + float(network[w][v]) < D[v]:
                        D[v] = D[w] + float(network[w][v])
                        p[v] = w
                else:
                    continue
        # print path and the shortest cost
        for node in nodes:
            if node == router_id:
                continue
            elif time.time() - receive_time[node] > 10 * UPDATE_INTERVAL:
                D.pop(node)
        print(f'I am Router {router_id}')
        if D:
            for i in D:
                if i not in p.keys():
                    print(f'Least cost path to router {i}:{router_id}{i} and cost is {D[i]:.1f}')
                else:
                    reversed_path = []
                    point = i
                    while point in p.keys():
                        if point not in reversed_path:
                            reversed_path.append(point)
                        reversed_path.append(p[point])
                        point = p[point]
                    reversed_path.append(router_id)
                    path = ''.join(reversed(reversed_path))
                    print(f'Least cost path to router {i}:{path} and cost is {D[i]:.1f}')


# start three thread
t1 = threading.Thread(target=boardcast)
t2 = threading.Thread(target=receive)
t3 = threading.Thread(target=dijkstra)
t1.start()
t2.start()
t3.start()
