import copy
import itertools
from collections import defaultdict

import networkx as nx

from database.DAO import DAO


class Model:
    def __init__(self):
        self._grafo = nx.DiGraph()
        self.idMap = {}
        self.parziale = []


    def getAllGenres(self):
        return DAO.getAllGenres()


    def buildGraph(self, genre):
        self._grafo.clear()
        self.idMap.clear()

        nodes = DAO.getAllNodes(genre)
        for n in nodes:
            self.idMap[n.ArtistId] = n
        self._grafo.add_nodes_from(nodes)

        artPop = DAO.getArtistPop(genre)
        artist_popularity = {}
        for ap in artPop:
            a = self.idMap[ap[0]]
            artist_popularity[a] = ap[1]

        edges = DAO.getAllEdges(genre)
        for e in edges:
            u = self.idMap[e[0]]
            v = self.idMap[e[1]]

            pop_u = artist_popularity[u]
            pop_v = artist_popularity[v]

            weight = pop_u + pop_v

            if pop_u < pop_v:
                self._grafo.add_edge(u, v, weight=weight)
            elif pop_u > pop_v:
                self._grafo.add_edge(v, u, weight=weight)
            else:
                self._grafo.add_edge(u, v, weight=weight)
                self._grafo.add_edge(v, u, weight=weight)

            # if pop_u > pop_v:
            #     self._grafo.add_edge(u, v, weight=weight)
            # elif pop_u < pop_v:
            #     self._grafo.add_edge(v, u, weight=weight)
            # else:
            #     self._grafo.add_edge(u, v, weight=weight)
            #     self._grafo.add_edge(v, u, weight=weight)





    def getGraphDetails(self):
        return len(self._grafo.nodes), len(self._grafo.edges)

    def getAllEdges(self):
        archi = list(self._grafo.edges(data=True)) # con data = True salviamo tupla 3 elementi: u,v e dizionario attributi (senza true solo u,v)
        archi.sort(key=lambda x: self._grafo[x[0]][x[1]]["weight"],reverse=True)
        return archi

    def getAllNodes(self):
        return self._grafo.nodes()

    def getTopArtista(self):
        artistiPesi = []

        for n in self._grafo.nodes:
            peso = 0
            for e in self._grafo.out_edges(n, data=True):
                peso = peso + e[2]["weight"]
            for e in self._grafo.in_edges(n, data=True):
                peso = peso - e[2]["weight"]
            artistiPesi.append((n, peso))

        artistiPesi.sort(key=lambda x: x[1], reverse=True)

        return artistiPesi[0]




    def getBestPath(self, start):
        self.bestPath = []
        self.parziale = [start]
        self.ricorsione(self.parziale)
        return self.bestPath

    def ricorsione(self, parziale):

        #caso terminale
        if len(parziale) > len(self.bestPath):
            self.bestPath = copy.deepcopy(parziale)


        # caso ricorsivo
        for n in self._grafo.successors(parziale[-1]):
            if n not in parziale:
                if len(parziale) >= 2:
                    arcoAttuale = self._grafo[parziale[-1]][n]["weight"]
                    arcoPrecedente = self._grafo[parziale[-2]][parziale[-1]]["weight"]
                    if arcoAttuale > arcoPrecedente :
                        parziale.append(n)
                        self.ricorsione(parziale)
                        parziale.pop()
                else:
                    parziale.append(n)
                    self.ricorsione(parziale)
                    parziale.pop()



    # BUILD GRAPH DEL PROF
    def buildGraph2(self, genere):
        self._grafo.clear()
        self._artist = DAO.getAllNodes(genere)
        for a in self._artist:
            self.idMap[a.ArtistID] = a

        self._grafo.add_nodes_from(self._artist)

        custom_artist_list = DAO.getCustomerArtistCounts(genere)
        # Cosa restituisce getCustomerArtistCounts("Rock") (una riga per ogni coppia cliente-artista, con il numero di brani del genere comprati):
        #
        # (CustomerId, ArtistId, ntracks)
        # (1, A, 3)
        # (1, B, 1)
        # (2, A, 2)
        # (2, C, 4)
        # (3, B, 2)
        # (3, C, 1)

        customerMap = defaultdict(dict)
        # dizionario di dizionari, si crea da solo

        for customer_id, artist_id, ntracks in custom_artist_list:
            customerMap[customer_id][artist_id] = ntracks
        # Risultato:
        # customerMap = { 1: {A: 3, B: 1},
        #                 2: {A: 2, C: 4},
        #                 3: {B: 2, C: 1} }
        # Ogni cliente ha dentro "gli artisti che ha comprato" e quanti brani per ciascuno.


        # ---------- PASSO 3: POPOLARITÀ di ogni artista ----------
        artist_popularity = defaultdict(int) #  parte da 0 per ogni artista nuovo

        for customer, artists in customerMap.items():
            for artist_id, ntracks in artists.items():
                artist_popularity[artist_id] += ntracks  # sommo i brani di tutti i clienti
        # Risultato: A = 3+2 = 5,  B = 1+2 = 3,  C = 4+1 = 5
        # (D non compare: nessuno l'ha comprato. Non serve, perché non avrà archi.)


        # ---------- PASSO 4: gli ARCHI ----------
        for customer_id, artists in customerMap.items(): # un cliente alla volta

            # tutte le coppie (senza ripetizioni e senza ordine) degli artisti di QUESTO cliente.
            # Se due artisti sono nello stesso dizionario, quel cliente li ha comprati entrambi:
            # è esattamente la condizione "esiste un arco se almeno un cliente ha comprato entrambi".
            for a, b in itertools.combinations(artists.keys(), 2):
                # cliente 1 -> (A,B)   cliente 2 -> (A,C)   cliente 3 -> (B,C)

                pop_a = artist_popularity[a]
                pop_b = artist_popularity[b]

                weight = pop_a + pop_b

                if pop_a < pop_b:
                    self._grafo.add_edge(self.idMap[a], self.idMap[b], weight=weight)
                elif pop_a > pop_b:
                    self._grafo.add_edge(self.idMap[b], self.idMap[a], weight=weight)
                else:
                    self._grafo.add_edge(self.idMap[a], self.idMap[b], weight=weight)
                    self._grafo.add_edge(self.idMap[b], self.idMap[a], weight=weight)

