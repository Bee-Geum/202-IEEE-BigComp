import osmnx as ox
import networkx as nx
import pickle
import os
import numpy as np


def get_graph(string):
    place_name = string
    graph = ox.graph_from_place(place_name, network_type='drive')
    graph = ox.add_edge_bearings(graph)

    return graph


def node_ascending_order(graph):
    # 노드 번호 0부터 오름차순으로 바꾸기
    new_node_id_mapping = {}
    new_id = 0
    for old_node_id in graph.nodes():
        new_node_id_mapping[old_node_id] = new_id
        new_id += 1

    new_graph = nx.relabel_nodes(graph, new_node_id_mapping)

    return new_graph


def add_time(graph):
    # travl_time 추가 위해 필수
    graph = ox.add_edge_speeds(graph)
    graph = ox.add_edge_travel_times(graph)

    # 각 노드에서의 대기시간 더해주기
    w = 20
    k = 30
    node_wait_times = {}

    for node, degree in graph.degree():
        if degree <= 2:
            wait_time = w
        else:
            wait_time = w + k * (degree - 2)

        node_wait_times[node] = wait_time

    # multidigraph에서 digraph로 변환
    for s, t, key, data in graph.edges(keys=True, data=True):
        # 도착 vertex만 할당, 나중에 path에서 계산할때는 끝 vertex 시간 빼주기. 시작점과 끝점 시간은 빼주기로 했음
        wait_time = node_wait_times[t]
        data["travel_time"] += wait_time

    return graph


def remove_dup(graph):
    edges_to_remove = set()  # 중복된 엣지 추가 방지

    # 각 노드 쌍에 대해 가장 짧은 엣지만을 선택하고 나머지는 제거
    for u, v in graph.edges():
        if graph.number_of_edges(u, v) > 1:
            min_length = float('inf')
            data_to_keep = None
            
            # 해당 노드 쌍의 모든 엣지를 순회하며 가장 짧은 길이를 찾음
            for key, data in graph[u][v].items():
                if data['length'] < min_length:
                    min_length = data['length']
                    data_to_keep = key
                       
            # 가장 짧은 엣지를 제외하고 나머지를 제거 대상 목록에 추가
            for key, data in graph[u][v].items():
                if key != data_to_keep:
                    edges_to_remove.add((u, v, key))

    # 엣지 제거
    for u, v, key in edges_to_remove:
        graph.remove_edge(u, v, key)

    return graph


def save_graph(graph, string):
    city = string.split(',')[0]

    with open(os.path.join('../graph_data', city + "_graph.pkl"), 'wb') as file:
        pickle.dump(graph, file)


def type_fix(G):
    for u, v, data in G.edges(data=True):
        data['length']      = np.float16(data['length'])
        data['travel_time'] = np.float16(data['travel_time'])

    return G




def main():
    with open(os.path.join('../txt', 'cities.txt'), 'r', encoding='UTF-8') as file:
        for line in file:
            city = line.strip()

            G         = get_graph(city)
            graph     = node_ascending_order(G)
            t_graph   = add_time(graph)
            digraph   = remove_dup(t_graph)
            f16_graph = type_fix(digraph)
            save_graph(f16_graph, city)


if __name__ == "__main__":
    main()