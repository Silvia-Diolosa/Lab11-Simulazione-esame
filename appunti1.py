"""
╔══════════════════════════════════════════════════════════════════╗
║              TdP — TEMPLATE RAPIDO PER L'ESAME                  ║
║         Copia-incolla le sezioni che ti servono                  ║
╚══════════════════════════════════════════════════════════════════╝
"""

# ================================================================
# IMPORT COMUNI
# ================================================================

import networkx as nx
import itertools
from collections import defaultdict
import copy
from dataclasses import dataclass
import flet as ft

# ================================================================
# 2. DAO — STRUTTURA BASE (model/DAO.py)
# ================================================================

"""
import mysql.connector

from model.nome_oggetto import NomeOggetto

class DAO:
    @staticmethod
    def getAllGenres():
        conn = DAO.getConnection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM genre ORDER BY Name"
        cursor.execute(query)
        result = []
        for row in cursor:
            result.append(row["Name"])
        cursor.close()
        conn.close()
        return result

    @staticmethod
    def getAllNodes(parametro):
        conn = DAO.getConnection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT ... FROM ... WHERE ... = %s"
        cursor.execute(query, (parametro,))
        result = []
        for row in cursor:
            result.append(NomeOggetto(row["Id"], row["Name"]))
        cursor.close()
        conn.close()
        return result
"""

# ================================================================
# 3. MODEL — STRUTTURA BASE (model/model.py)
# ================================================================

class Model:
    def __init__(self):
        self._graph = nx.Graph()       # oppure nx.DiGraph()
        self._idMap = {}
        self._bestPath = []
        self._bestScore = 0

    def getGraphDetails(self):
        return len(self._graph.nodes), len(self._graph.edges)


# ================================================================
# 4. COSTRUZIONE GRAFO — BUILD GRAPH
# ================================================================

    # Template generico
    def buildGraph(self, parametro):
        self._graph.clear()

        # 1) Nodi
        nodes = []  # DAO.getAllNodes(parametro)
        self._idMap = {}
        for n in nodes:
            self._idMap[n.id] = n
        self._graph.add_nodes_from(nodes)

        # 2) Archi (scegli la casistica sotto)
        self._addEdges(parametro)


# ================================================================
# 5. ARCHI — TUTTE LE CASISTICHE
# ================================================================
# ────────────────────────────────────────────────────────────────
# CASO A — Arco esplicito nel DB, senza peso
# Esempio: Metro Paris (tabella connessione con id_stazP, id_stazA)
# ────────────────────────────────────────────────────────────────

    def _addEdges_casoA(self):
        edges = []  # DAO.getAllEdges()
        for e in edges:
            u = self._idMap[e.id_partenza]
            v = self._idMap[e.id_arrivo]
            self._graph.add_edge(u, v)


# ────────────────────────────────────────────────────────────────
# CASO B — Arco esplicito, peso = conteggio SQL
# SQL: SELECT col1, col2, COUNT(*) as peso FROM ... GROUP BY col1, col2
# ────────────────────────────────────────────────────────────────
    def _addEdges_casoB(self):
        edges = []  # DAO.getAllEdges()
        for e in edges:
            u = self._idMap[e.id1]
            v = self._idMap[e.id2]
            if u in self._graph and v in self._graph:
                if self._graph.has_edge(u, v):
                    self._graph[u][v]["weight"] += e.peso
                else:
                    self._graph.add_edge(u, v, weight=e.peso)

# ────────────────────────────────────────────────────────────────
# CASO C — Self-join SQL, peso = conteggio condiviso
# Quando: peso = n. elementi in comune (tracce, clienti, playlist)
# SQL: self-join con <  e COUNT(DISTINCT)
# ────────────────────────────────────────────────────────────────
    # SQL:
    # SELECT t1.col, t2.col, COUNT(DISTINCT ...) as peso
    # FROM tabella t1, tabella t2
    # WHERE t1.elemento_condiviso = t2.elemento_condiviso
    # AND t1.col < t2.col
    # GROUP BY t1.col, t2.col

    def _addEdges_casoC(self):
        edges = []  # DAO.getEdges() -> lista di (id1, id2, peso)
        for id1, id2, peso in edges:
            self._graph.add_edge(self._idMap[id1], self._idMap[id2], weight=peso)


# ────────────────────────────────────────────────────────────────
# CASO D — Python: defaultdict(list) + combinations
# Quando: la catena SQL è troppo lunga per il self-join
#         oppure il peso = conteggio dell'elemento condiviso
# Query SQL semplice: SELECT elemento_condiviso, nodo_id FROM ... GROUP BY ...
# ────────────────────────────────────────────────────────────────

    def _addEdges_casoD(self):
        result = []  # DAO.getResult() -> (elemento_condiviso, nodo_id)

        # raggruppa per elemento condiviso
        condivisoMap = defaultdict(list) #oppure dict
        for condiviso, nodo in result:
            condivisoMap[condiviso].append(nodo)

        # crea archi con peso = n. elementi condivisi
        pesoArco = defaultdict(int)
        for condiviso, nodi in condivisoMap.items():
            for a, b in itertools.combinations(nodi, 2):
                pesoArco[(a, b)] += 1

        for (a, b), peso in pesoArco.items():
            self._graph.add_edge(self._idMap[a], self._idMap[b], weight=peso)

# ────────────────────────────────────────────────────────────────
# CASO E — Python: con VERSO (grafo orientato)
# Quando: arco dal nodo con valore maggiore verso quello minore
#         peso = somma dei valori dei due nodi
# Query SQL: SELECT elemento_condiviso, nodo_id FROM ... GROUP BY ...
# ────────────────────────────────────────────────────────────────

    def _addEdges_casoE(self):
        result = []  # DAO.getResult() -> (elemento_condiviso, nodo_id)

        # raggruppa per elemento condiviso
        condivisoMap = defaultdict(list)
        for condiviso, nodo in result:
            condivisoMap[condiviso].append(nodo)

        # popolarità globale per nodo
        popolarita = defaultdict(int)
        for condiviso, nodo in result:
            popolarita[nodo] += 1

        # coppie (senza duplicati)
        coppie = set()
        for condiviso, nodi in condivisoMap.items():
            for a, b in itertools.combinations(nodi, 2):
                coppie.add((a, b))

        # archi con verso
        for (a, b) in coppie:
            pop_a = popolarita[a]
            pop_b = popolarita[b]
            weight = pop_a + pop_b

            if pop_a > pop_b:
                self._graph.add_edge(self._idMap[a], self._idMap[b], weight=weight)
            elif pop_a < pop_b:
                self._graph.add_edge(self._idMap[b], self._idMap[a], weight=weight)
            else:
                self._graph.add_edge(self._idMap[a], self._idMap[b], weight=weight)
                self._graph.add_edge(self._idMap[b], self._idMap[a], weight=weight)


# ────────────────────────────────────────────────────────────────
# CASO F — Python: defaultdict(dict) per 3 valori dalla query
# Quando: la query restituisce (condiviso, nodo, valore)
#         e ti serve il valore per calcolare popolarità/peso
# ────────────────────────────────────────────────────────────────

    def _addEdges_casoF(self):
        result = []  # DAO.getResult() -> (condiviso, nodo_id, valore)

        condivisoMap = defaultdict(dict)
        for condiviso, nodo, valore in result:
            condivisoMap[condiviso][nodo] = valore

        # popolarità globale
        popolarita = defaultdict(int)
        for condiviso, nodi in condivisoMap.items():
            for nodo, valore in nodi.items():
                popolarita[nodo] += valore

        # coppie + archi (identico a CASO E)
        coppie = set()
        for condiviso, nodi in condivisoMap.items():
            for a, b in itertools.combinations(nodi.keys(), 2):
                coppie.add((a, b))

        for (a, b) in coppie:
            pop_a = popolarita[a]
            pop_b = popolarita[b]
            weight = pop_a + pop_b
            if pop_a > pop_b:
                self._graph.add_edge(self._idMap[a], self._idMap[b], weight=weight)
            elif pop_a < pop_b:
                self._graph.add_edge(self._idMap[b], self._idMap[a], weight=weight)
            else:
                self._graph.add_edge(self._idMap[a], self._idMap[b], weight=weight)
                self._graph.add_edge(self._idMap[b], self._idMap[a], weight=weight)


# ────────────────────────────────────────────────────────────────
# CASO G — Grafo completo (tutti i nodi collegati tra loro)
# Quando: la traccia dice "tutti collegati" — nessuna query archi
# ────────────────────────────────────────────────────────────────

    def _addEdges_casoG(self):
        edges = list(itertools.combinations(self._graph.nodes, 2))
        self._graph.add_edges_from(edges)
        # pesi calcolati dopo, in un loop separato
        # mapValori = DAO.getValori(...)
        # for u, v in self._graph.edges:
        #     self._graph[u][v]["weight"] = mapValori[u] + mapValori[v]


# ════════════════════════════════════════════════════════════════
# QUANDO USARE COSA — REGOLA RAPIDA
# ════════════════════════════════════════════════════════════════
#
# Peso = conteggio elemento condiviso   → CASO C (SQL) o CASO D (Python)
#   (tracce in comune, clienti in comune, playlist in comune)
#
# Peso = proprietà dei singoli nodi sommate  → CASO E o F (Python obbligatorio)
#   (popolarità A + popolarità B, durata A + durata B)
#
# Catena corta (1-2 tabelle)  → SQL self-join (CASO C)
# Catena lunga (3+ tabelle)   → Python (CASO D, E, F)
#
# Verso (orientato)           → CASO E o F
# Grafo completo              → CASO G
# ════════════════════════════════════════════════════════════════


# ================================================================
# 6. ANALISI GRAFO — FUNZIONI UTILI
# ================================================================

    # --- Info base ---
    # len(self._graph.nodes)
    # len(self._graph.edges)
    # self._graph.edges(data=True)   → lista (u, v, {"weight": w})

    # --- Vicini ---
    # self._graph.neighbors(nodo)    → Graph non orientato, nodi adiacenti a quello selezionato (es in flight)
    # self._graph.successors(nodo)   → DiGraph (solo uscenti)
    # self._graph.predecessors(nodo) → DiGraph (solo entranti)

    def getVicini(self, source):
        vicini = self._grafo.neighbors(source)
        viciniTuples = []
        for v in vicini:
            viciniTuples.append((v, self._grafo[source][v]["weight"]))

        viciniTuples.sort(key=lambda x: x[1], reverse=True)

        return viciniTuples

    # --- Grado ---
    # self._graph.degree(nodo)       → Graph
    # self._graph.out_degree(nodo)   → DiGraph uscenti
    # self._graph.in_degree(nodo)    → DiGraph entranti

    # --- Archi con peso ---
    # self._graph.edges(nodo, data=True)      → Graph
    # self._graph.out_edges(nodo, data=True)   → DiGraph uscenti
    # self._graph.in_edges(nodo, data=True)    → DiGraph entranti

    # --- Connettività (solo Graph) ---
    # nx.node_connected_component(self._graph, nodo)  → set nodi raggiungibili:
        return v1 in nx.node_connected_component(self._graph, v0) #true se esiste cammino tra v0e v1
    # nx.number_connected_components(self._graph)      → intero
    # components = list(nx.connected_components(self._graph))
    # largest = max(components, key=len)

    # --- Sotto-grafo ---
    # subgraph = self._graph.subgraph(largest).copy()

    # --- Cammini minimi ---
    # nx.dijkstra_path(self._graph, u, v)              → percorso tra due nodi[u, ..., v]
    # costo, path = nx.single_source_dijkstra(self._graph, u, v)

    #VEDI ALTRI PERCORSI IN FLIGHT DELAY MODEL-GET PATH

    # --- Visite ---
    # archi = nx.bfs_edges(self._graph, source)  → coppie (u,v) ampiezza
    # archi = nx.dfs_edges(self._graph, source)  → coppie (u,v) profondità
    # nodi_raggiunti = [v for u, v in nx.bfs_edges(self._graph, source)]

    # --- Top 5 influenza (DiGraph) ---
    def getTop5Influenza(self):
        scores = []
        for n in self._graph.nodes:
            out = sum(d["weight"] for _, _, d in self._graph.out_edges(n, data=True))
            in_ = sum(d["weight"] for _, _, d in self._graph.in_edges(n, data=True))
            scores.append((n, out - in_))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:5]

    # --- Top 5 peso totale (Graph) ---
    def getTop5PesoTotale(self):
        scores = []
        for n in self._graph.nodes:
            score = sum(d["weight"] for _, _, d in self._graph.edges(n, data=True))
            scores.append((n, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:5]

    # --- Top 5 archi per peso ---
    def getTop5Archi(self):
        archi = [(u, v, d["weight"]) for u, v, d in self._graph.edges(data=True)]
        archi.sort(key=lambda x: x[2], reverse=True)
        return archi[:5]


# ================================================================
# 7. RICORSIONE — TUTTE LE CASISTICHE
# ================================================================
    def cercaCammino(self, nodoPartenza, ____):
        self._bestPath = []
        self._bestScore = 0  # oppure togliere se uso len()
        parziale = [nodoPartenza]

        # SCELTA 5: primo passo fuori? (solo se vincolo usa parziale[-2])
        # SE SÌ:
        #     for v in self._graph._______(nodoPartenza):
        #         parziale.append(v)
        #         self._ricorsione(parziale, ____)
        #         parziale.pop()
        # SE NO:
        #     self._ricorsione(parziale, ____)
        return self._bestPath, self._bestScore

    def _ricorsione(self, parziale, ____):
        # ──────────────────────────────────────
        # SCELTA 3: c'è un nodo finale?
        # SE SÌ (senza lunghezza esatta):
        #     if parziale[-1] == ____:
        # SE NO:
        #     (salvo sempre, senza if)
        # ──────────────────────────────────────

        # ──────────────────────────────────────
        # SCELTA 1: cosa ottimizzo?
        # LUNGHEZZA:  if len(parziale) > len(self._bestPath):
        # PESO:       if self._score(parziale) > self._bestScore:
        # ──────────────────────────────────────
        self._bestPath = copy.deepcopy(parziale)
        # ──────────────────────────────────────
        # SCELTA 2: c'è un limite?
        # ESATTA:   if len(parziale) == lun:
        #               (mettere ottimalità + nodo finale QUI DENTRO, non sopra)
        #               return
        # MASSIMA:  if len(parziale) == t + 1:
        #               return
        # NESSUNO:  (niente return)
        # ──────────────────────────────────────

        # ──────────────────────────────────────
        # ESPANSIONE
        # ──────────────────────────────────────
        for n in self._graph._______(parziale[-1]):
            #                neighbors (Graph) o successors (DiGraph)
            # SCELTA 4: vincolo sull'espansione?
            # NESSUNO:      if n not in parziale:
            # PESO CRESC:   if n not in parziale and peso_nuovo > peso_prec:
            # PESO DECRESC: if n not in parziale and peso_nuovo < peso_prec:
                    for n in self._graph.successors(parziale[-1]):  # DiGraph → successors
                        peso_prec = self._graph[parziale[-2]][parziale[-1]]["weight"]
                        peso_nuovo = self._graph[parziale[-1]][n]["weight"]
                        if n not in parziale and peso_nuovo > peso_prec:
                            parziale.append(n)
                            self._ricorsione(parziale)
                            parziale.pop()

                    #ALTRO MODO UGUALE PER NON DOVER FARE IL PRIMO PASSO FUORI
                        def cercaCammino(self, nodoPartenza):
                            self._bestPath = []
                            parziale = [nodoPartenza]
                            self._ricorsione(parziale, -1)  # -1 così qualsiasi peso è > di lastWeight
                            return self._bestPath
                        #ESPANSIONE
                            for _, vicino, data in self._graph.out_edges(parziale[-1], data=True):
                                peso = data["weight"]
                                if peso > lastWeight and vicino not in parziale:
                                    parziale.append(vicino)
                                    self._ricorsione(parziale, peso)
                                    parziale.pop()

            # ATTRIBUTO:    if n not in parziale and n.attr == parziale[-1].attr:

            #if n not in parziale ____:
                parziale.append(n)
                self._ricorsione(parziale, ____)
                parziale.pop()

        def _score(self, parziale):
            score = 0
            for i in range(len(parziale) - 1):
                score += self._graph[parziale[i]][parziale[i + 1]]["weight"]
            return score

    #CASO FORMULA 1 IN CUI CERCO UN SET
    def cercaSet(self, k):
        self._bestSet = []
        self._bestVal = float('inf')  # o 0 se massimizzi
        components = list(nx.connected_components(self._graph))

        if len(components) < k:
            return None, 0

        parziale = []
        self._ricorsione(components, k, parziale, 0)
        return self._bestSet, self._bestVal

    def _ricorsione(self, components, k, parziale, idx):
        # HO SCELTO ABBASTANZA?
        if len(parziale) == k:
            val = self._valuta(parziale)
            if val < self._bestVal:  # < se minimizzo, > se massimizzo
                self._bestVal = val
                self._bestSet = copy.deepcopy(parziale)
            return

        # POSSO ANCORA SCEGLIERE?
        if idx >= len(components):
            return
        if len(components) - idx < k - len(parziale):
            return  # impossibile arrivare a k

        # PROVO OGNI NODO DI QUESTA COMPONENTE
        for nodo in components[idx]:
            parziale.append(nodo)
            self._ricorsione(components, k, parziale, idx + 1)
            parziale.pop()

        # SALTO QUESTA COMPONENTE
        self._ricorsione(components, k, parziale, idx + 1)
# ────────────────────────────────────────────────────────────────
# CASO R1 — Lunghezza esatta + nodo finale
# ────────────────────────────────────────────────────────────────

    def getCamminoR1(self, v0, end, lun):
        self._bestPath = []
        self._bestScore = 0
        parziale = [v0]
        self._ricorsioneR1(parziale, lun, end)
        return self._bestPath, self._bestScore

    def _ricorsioneR1(self, parziale, lun, end):
        #CONDIZIONE DI DI OTTIMALITA'
        if len(parziale) == lun:
            if parziale[-1] == end and self._score(parziale) > self._bestScore:
                self._bestScore = self._score(parziale)
                self._bestPath = copy.deepcopy(parziale)
            return  # TERMINAZIOEN: mi fermo SEMPRE a lunghezza raggiunta

        for n in self._graph.successors(parziale[-1]):  # .neighbors() se Graph
            if n not in parziale:
                parziale.append(n)
                self._ricorsioneR1(parziale, lun, end)
                parziale.pop()


# ────────────────────────────────────────────────────────────────
# CASO R2 — Lunghezza massima + nodo finale
# ────────────────────────────────────────────────────────────────
#(FLIGHT) - PESO MASSIMO
    def getCamminoR2(self, v0, end, t):
        self._bestPath = []
        self._bestScore = 0
        parziale = [v0]
        self._ricorsioneR2(parziale, end, t)
        return self._bestPath, self._bestScore

    def _ricorsioneR2(self, parziale, end, t):
        # salvo se sono arrivato a destinazione (ma NON mi fermo)
        #CONDIZONE DI OTTIMALITA'
        if parziale[-1] == end:
            if self._score(parziale) > self._bestScore:
                self._bestScore = self._score(parziale)
                self._bestPath = copy.deepcopy(parziale)

        #CONDIZONE DI TERMINAZIONE
        # mi fermo solo se ho esaurito le tratte
        if len(parziale) == t + 1:  # t tratte = t+1 nodi
            return

        for n in self._graph.neighbors(parziale[-1]):
            if n not in parziale:
                parziale.append(n)
                self._ricorsioneR2(parziale, end, t)
                parziale.pop()


# ────────────────────────────────────────────────────────────────
# CASO R3 — NODO iniziale, Nessun nodo finale, vincolo pesi decrescenti
# ────────────────────────────────────────────────────────────────
# (BASEBALL)- PERCORSO DI PESO MASSIMO
#SE C'è VINCOLO SUI PESI, PRIMO PASSO FUORI!! (PARZIALE[-2])
    def getCamminoR3(self, v0):
        self._bestPath = []
        self._bestScore = 0
        parziale = [v0]
        # primo passo FUORI dalla ricorsione (serve parziale[-2])
        for v in self._graph.neighbors(v0):
            parziale.append(v)
            self._ricorsioneR3(parziale)
            parziale.pop()
        return self._bestPath, self._bestScore

    def _ricorsioneR3(self, parziale):
        # ogni parziale è valida
        if self._score(parziale) > self._bestScore:
            self._bestScore = self._score(parziale)
            self._bestPath = copy.deepcopy(parziale)

        for v in self._graph.neighbors(parziale[-1]):
            peso_precedente = self._graph[parziale[-2]][parziale[-1]]["weight"]
            peso_nuovo = self._graph[parziale[-1]][v]["weight"]
            if peso_precedente > peso_nuovo and v not in parziale:
                parziale.append(v)
                self._ricorsioneR3(parziale)
                parziale.pop()


# ────────────────────────────────────────────────────────────────
# CASO R3bis — Nessun nodo finale, vincolo pesi CRESCENTI
# ────────────────────────────────────────────────────────────────

    def getCamminoR3bis(self, v0):
        self._bestPath = []
        self._bestScore = 0
        parziale = [v0]
        for v in self._graph.neighbors(v0):
            parziale.append(v)
            self._ricorsioneR3bis(parziale)
            parziale.pop()
        return self._bestPath, self._bestScore

    def _ricorsioneR3bis(self, parziale):
        if self._score(parziale) > self._bestScore:
            self._bestScore = self._score(parziale)
            self._bestPath = copy.deepcopy(parziale)

        for v in self._graph.neighbors(parziale[-1]):
            peso_precedente = self._graph[parziale[-2]][parziale[-1]]["weight"]
            peso_nuovo = self._graph[parziale[-1]][v]["weight"]
            if peso_precedente < peso_nuovo and v not in parziale:  # < invece di >
                parziale.append(v)
                self._ricorsioneR3bis(parziale)
                parziale.pop()

        #vedi anche es esercizio

# ────────────────────────────────────────────────────────────────
# CASO R4 — Lunghezza esatta, vincolo su attributo nodo
# ────────────────────────────────────────────────────────────────

    def getCamminoR4(self, v0, lun):
        self._bestPath = []
        self._bestScore = 0
        parziale = [v0]
        self._ricorsioneR4(parziale, lun)
        return self._bestPath, self._bestScore

    def _ricorsioneR4(self, parziale, lun):
        if len(parziale) == lun:
            if self._score(parziale) > self._bestScore:
                self._bestScore = self._score(parziale)
                self._bestPath = copy.deepcopy(parziale)
            return

        for n in self._graph.neighbors(parziale[-1]):
            if n not in parziale and parziale[-1].attributo == n.attributo:
                parziale.append(n)
                self._ricorsioneR4(parziale, lun)
                parziale.pop()

        # ────────────────────────────────────────────────────────────────
        # CASO R5 — Selezione da componenti connesse (no cammino su archi)
        # Esempio: Formula 1 — scegliere K piloti da K componenti diverse
        #
        # NON è un cammino sul grafo. È una scelta combinatoria:
        # per ogni componente connessa, scelgo UN elemento oppure NESSUNO.
        # L'obiettivo è ottimizzare un valore calcolato sul set scelto.
        #
        # Struttura: per ogni componente, due branch:
        #   1) provo ogni nodo della componente (append/ricorsione/pop)
        #   2) salto la componente (ricorsione senza append)
        # indexComponente tiene traccia di quale componente sto considerando.
        # ────────────────────────────────────────────────────────────────

        def getSetOttimo(self, k):
            self._bestSet = []
            self._bestVal = float('inf')  # o 0 se massimizzi
            components = list(nx.connected_components(self._graph))

            if len(components) < k:
                return None, 0

            parziale = []
            self._ricorsioneR5(components, k, parziale, 0)
            return self._bestSet, self._bestVal

        def _ricorsioneR5(self, components, k, parziale, indexComponente):
            # caso base — ho scelto k elementi
            if len(parziale) == k:
                val = self._valuta(parziale)  # calcola il valore della soluzione
                if val < self._bestVal:  # < se minimizzi, > se massimizzi
                    self._bestVal = val
                    self._bestSet = copy.deepcopy(parziale)
                return

            # terminazione — non ci sono abbastanza componenti rimaste
            if indexComponente >= len(components):
                return
            if (len(components) - indexComponente) < (k - len(parziale)):
                return  # pruning: impossibile arrivare a k

            componente = components[indexComponente]

            # BRANCH 1 — prendo un elemento da questa componente
            for nodo in componente:
                parziale.append(nodo)
                self._ricorsioneR5(components, k, parziale, indexComponente + 1)
                parziale.pop()

            # BRANCH 2 — salto questa componente (non prendo nessuno)
            self._ricorsioneR5(components, k, parziale, indexComponente + 1)

# ────────────────────────────────────────────────────────────────
# SCORE — funzione peso cammino (uguale per tutte le casistiche)
# ────────────────────────────────────────────────────────────────

    def _score(self, parziale):
        score = 0
        for i in range(len(parziale) - 1):
            score += self._graph[parziale[i]][parziale[i + 1]]["weight"]
        return score


# ================================================================
# 8. TEST MODEL (test_model.py)
# ================================================================

"""
from model.model import Model

myModel = Model()
myModel.buildGraph("Rock")
nNodes, nEdges = myModel.getGraphDetails()
print(f"Nodi: {nNodes} --- Archi: {nEdges}")

# test ricorsione
# path, score = myModel.getCamminoR1(nodo_partenza, nodo_arrivo, 5)
# print(f"Score: {score}")
# for n in path:
#     print(n)
"""


# ================================================================
# 9. CONTROLLER — TEMPLATE COMPLETO (UI/controller.py)
# ================================================================

class Controller:
    def __init__(self, view, model):
        self._view = view
        self._model = model
        self._sceltaDD1 = None
        self._sceltaDD2 = None

    # --- ERRORE HELPER (evita ripetizioni) ---
    def _showError(self, msg, color="red"):
        self._view._txtResult.controls.clear()
        self._view._txtResult.controls.append(ft.Text(msg, color=color))
        self._view.update_page()

    # --- RIEMPIRE DROPDOWN CON OGGETTI (on_click) ---
    def fillDDOggetti(self, lista):
        self._view._dd1.options.clear()
        for o in lista:
            self._view._dd1.options.append(
                ft.dropdown.Option(
                    data=o, #serve ad associare un oggetto all'opzione,
                    key=str(o), #quello che ottieni con .value, anche quella che mostro nel dd
                    on_click=self._handleDD1
                )
            )
        self._view.update_page()

    def _handleDD1(self, e):
        self._sceltaDD1 = e.control.data #ridà l'oggetto salvato nel dd

    # --- RIEMPIRE DROPDOWN CON VALORI SEMPLICI (on_change sul DD) ---
    def fillDDValori(self, lista):
        self._view._dd2.options = list(
            map(lambda x: ft.dropdown.Option(x), lista)
        )
        self._view.update_page()

    # on_change è nella view: on_change=self._controller.handleDD2
    def handleDD2(self, e):
        self._sceltaDD2 = self._view._dd2.value

    # --- HANDLER CREA GRAFO (con validazione dropdown) ---
    def handleCreaGrafo(self, e):
        if self._sceltaDD1 is None:
            self._view._txtResult.controls.clear()
            self._view._txtResult.controls.append(
                ft.Text("Selezionare un valore dal menu."))
            return

        self._model.buildGraph(self._sceltaDD1)
        nNodi, nArchi = self._model.getGraphDetails()

        self._view._txtResult.controls.clear()
        self._view._txtResult.controls.append(
            ft.Text("Grafo correttamente creato.", color="green"))
        self._view._txtResult.controls.append(
            ft.Text(f"Nodi: {nNodi}, Archi: {nArchi}"))
        self._view.update_page()

    # --- HANDLER CREA GRAFO (con validazione input numerico) ---
    def handleCreaGrafoConInput(self, e):
        txt = self._view._txtInput.value

        if txt == "":
            self._view._txtResult.controls.clear()
            self._view._txtResult.controls.append(
                ft.Text("Inserire un valore."))
            return

        try:
            val = int(txt)
        except ValueError:
            self._view._txtResult.controls.clear()
            self._view._txtResult.controls.append(
                ft.Text("Inserire un valore intero."))
            return


        if val < 1 or val > 100:
            self._view._txtResult.controls.clear()
            self._view._txtResult.controls.append(
                ft.Text("Inserire un valore tra 1 e 100."))
            return

        self._model.buildGraph(val)
        nNodi, nArchi = self._model.getGraphDetails()

        self._view._txtResult.controls.clear()
        self._view._txtResult.controls.append(
            ft.Text("Grafo correttamente creato.", color="green"))
        self._view._txtResult.controls.append(
            ft.Text(f"Nodi: {nNodi}, Archi: {nArchi}"))
        self._view.update_page()

    # --- HANDLER CERCA CAMMINO ---
    def handleCercaCammino(self, e):
        if self._sceltaDD1 is None:
            self._showError("Selezionare nodo di partenza.")
            return

        path, score = self._model.getCamminoR1(self._sceltaDD1, None, 5)

        self._view._txtResult.controls.clear()
        if not path:
            self._view._txtResult.controls.append(
                ft.Text("Nessun cammino trovato.", color="orange"))
        else:
            self._view._txtResult.controls.append(
                ft.Text(f"Cammino trovato con score {score}.", color="green"))
            for n in path:
                self._view._txtResult.controls.append(ft.Text(f"{n}"))
        self._view.update_page()


# ================================================================
# 10. CATENE JOIN CHINOOK — RIFERIMENTO RAPIDO
# ================================================================

"""
Cliente → cosa ha comprato:
    Customer → Invoice → InvoiceLine → Track

Track → artista:
    Track → Album → Artist

Track → genere:
    Track → Genre

Track → media type:
    Track → MediaType

Track → playlist:
    Track → PlaylistTrack → Playlist

Cliente → artista:
    Customer → Invoice → InvoiceLine → Track → Album → Artist

Cliente → genere:
    Customer → Invoice → InvoiceLine → Track → Genre

Playlist → artista:
    PlaylistTrack → Track → Album → Artist

Cliente → dipendente:
    Customer → Employee  (tramite SupportRepId = EmployeeId)

Dipendente → capo:
    Employee → Employee  (tramite ReportsTo = EmployeeId)
"""


# ================================================================
# 11. QUERY SQL RICORRENTI — RIFERIMENTO RAPIDO
# ================================================================

"""
-- Nodi: artisti con almeno una traccia acquistata
SELECT DISTINCT a.ArtistId, a.Name
FROM artist a, album al, track t, invoiceline il
WHERE a.ArtistId = al.ArtistId
AND al.AlbumId = t.AlbumId
AND t.TrackId = il.TrackId

-- Nodi: clienti che hanno acquistato genere X
SELECT DISTINCT c.CustomerId, c.FirstName, c.LastName
FROM customer c, invoice i, invoiceline il, track t, genre g
WHERE c.CustomerId = i.CustomerId
AND i.InvoiceId = il.InvoiceId
AND il.TrackId = t.TrackId
AND t.GenreId = g.GenreId
AND g.Name = %s

-- Nodi: album con almeno N tracce
SELECT a.AlbumId, a.Title
FROM album a, track t
WHERE a.AlbumId = t.AlbumId
GROUP BY a.AlbumId, a.Title
HAVING COUNT(t.TrackId) >= N

-- Archi Python (condiviso, nodo): cliente → artista
SELECT i.CustomerId, al.ArtistId
FROM invoice i, invoiceline il, track t, album al
WHERE i.InvoiceId = il.InvoiceId
AND il.TrackId = t.TrackId
AND t.AlbumId = al.AlbumId
GROUP BY i.CustomerId, al.ArtistId

-- Archi Python (condiviso, nodo): playlist → artista
SELECT pt.PlaylistId, al.ArtistId
FROM playlisttrack pt, track t, album al
WHERE pt.TrackId = t.TrackId
AND t.AlbumId = al.AlbumId
GROUP BY pt.PlaylistId, al.ArtistId

-- Archi Python (condiviso, nodo): cliente → genere
SELECT i.CustomerId, t.GenreId
FROM invoice i, invoiceline il, track t
WHERE i.InvoiceId = il.InvoiceId
AND il.TrackId = t.TrackId
GROUP BY i.CustomerId, t.GenreId

-- Archi Python (condiviso, nodo): cliente → album
SELECT i.CustomerId, t.AlbumId
FROM invoice i, invoiceline il, track t
WHERE i.InvoiceId = il.InvoiceId
AND il.TrackId = t.TrackId
GROUP BY i.CustomerId, t.AlbumId

-- Archi SQL: self-join corta (es. playlist condividono tracce)
SELECT pt1.PlaylistId, pt2.PlaylistId, COUNT(DISTINCT pt1.TrackId) as peso
FROM playlisttrack pt1, playlisttrack pt2
WHERE pt1.TrackId = pt2.TrackId
AND pt1.PlaylistId < pt2.PlaylistId
GROUP BY pt1.PlaylistId, pt2.PlaylistId

-- Archi SQL: employee (gerarchia)
SELECT e2.EmployeeId, e.EmployeeId,
       ABS(TIMESTAMPDIFF(YEAR, e.BirthDate, e2.BirthDate)) as peso
FROM employee e, employee e2
WHERE e.ReportsTo = e2.EmployeeId
"""