"""
╔══════════════════════════════════════════════════════════════════╗
║          TdP — TEMPLATE RAPIDO PER L'ESAME  (versione 3)         ║
║          Database: Chinook (esercitazioni 2026-06-29 A-B-C)      ║
║          Copia-incolla le sezioni che ti servono                 ║
╚══════════════════════════════════════════════════════════════════╝

INDICE
  1.  Import comuni
  2.  CLASSI (entità) per i nodi — una per ogni tabella Chinook
  3.  DAO — struttura base con try/except/finally
  4.  MODEL — struttura base + metodi base del grafo (nodi, archi)
  5.  Costruzione grafo (buildGraph)
  6.  Archi — tutte le casistiche (A-G)
  7.  Quando usare cosa (regola rapida)
  8.  Analisi del grafo — funzioni utili
  9.  Ricorsione — tutte le casistiche (R1-R5)
  10. Test del model (test_model.py)
  11. Controller — template completo
  12. View + main (Flet) — solo come riferimento
  13. Schema Chinook e catene di JOIN
  14. Query SQL ricorrenti
  15. Eccezioni e controlli — riepilogo di dove sono
  16. Checklist errori comuni
"""


# ================================================================
# 1. IMPORT COMUNI
# ================================================================

import networkx as nx
import itertools
from collections import defaultdict
import copy
from dataclasses import dataclass
import datetime
import flet as ft


# ================================================================
# 2. CLASSI (ENTITÀ) PER I NODI — CHINOOK
# ================================================================
# Una classe per tabella. Vanno in model/<nome>.py (o tutte in un file).
#
# Ogni classe ha:
#  - i campi con lo STESSO NOME delle colonne del DB (ArtistId, Name, ...)
#  - __hash__ e __eq__ basati SOLO sull'id → servono perché l'oggetto sia
#    un nodo valido di networkx (due oggetti con lo stesso id = stesso nodo)
#  - __str__ → è quello che compare nei dropdown e nelle stampe (str(n))
#
# COME LE CREO NEL DAO:
#  - Classe(**row)  funziona se la SELECT restituisce TUTTE le colonne
#    della tabella (usa  SELECT x.*  oppure elenca tutte le colonne).
#    Le chiavi del dizionario devono avere lo stesso nome dei campi.
#  - Se la query restituisce solo alcune colonne, crea una tua classe con
#    solo quei campi (vedi ArtistaConAlbum più sotto).
#  - A mano:  Artist(row["ArtistId"], row["Name"])
#
# L'ID di ogni classe ha il nome della colonna (ArtistId, AlbumId, TrackId,
# GenreId, ...). Nel buildGraph:  self._idMap[n.ArtistId] = n
#
# ATTENZIONE: MySQL restituisce i campi DECIMAL (UnitPrice, Total) come
# decimal.Decimal: se li sommi con dei float va in errore → float(row["Total"]).


@dataclass
class Artist:
    ArtistId: int
    Name: str

    def __hash__(self):
        return hash(self.ArtistId)

    def __eq__(self, other):
        return self.ArtistId == other.ArtistId

    def __str__(self):
        return f"{self.Name} [{self.ArtistId}]"


@dataclass
class Album:
    AlbumId: int
    Title: str
    ArtistId: int

    def __hash__(self):
        return hash(self.AlbumId)

    def __eq__(self, other):
        return self.AlbumId == other.AlbumId

    def __str__(self):
        return f"{self.Title} [{self.AlbumId}]"


@dataclass
class Track:
    TrackId: int
    Name: str
    AlbumId: int
    MediaTypeId: int
    GenreId: int
    Composer: str
    Milliseconds: int
    Bytes: int
    UnitPrice: float

    def __hash__(self):
        return hash(self.TrackId)

    def __eq__(self, other):
        return self.TrackId == other.TrackId

    def __str__(self):
        return f"{self.Name} [{self.TrackId}]"


@dataclass
class Genre:
    GenreId: int
    Name: str

    def __hash__(self):
        return hash(self.GenreId)

    def __eq__(self, other):
        return self.GenreId == other.GenreId

    def __str__(self):
        return f"{self.Name}"


@dataclass
class MediaType:
    MediaTypeId: int
    Name: str

    def __hash__(self):
        return hash(self.MediaTypeId)

    def __eq__(self, other):
        return self.MediaTypeId == other.MediaTypeId

    def __str__(self):
        return f"{self.Name}"


@dataclass
class Playlist:
    PlaylistId: int
    Name: str

    def __hash__(self):
        return hash(self.PlaylistId)

    def __eq__(self, other):
        return self.PlaylistId == other.PlaylistId

    def __str__(self):
        return f"{self.Name} [{self.PlaylistId}]"


@dataclass
class Customer:
    CustomerId: int
    FirstName: str
    LastName: str
    Company: str
    Address: str
    City: str
    State: str
    Country: str
    PostalCode: str
    Phone: str
    Fax: str
    Email: str
    SupportRepId: int

    def __hash__(self):
        return hash(self.CustomerId)

    def __eq__(self, other):
        return self.CustomerId == other.CustomerId

    def __str__(self):
        return f"{self.FirstName} {self.LastName} [{self.CustomerId}]"


@dataclass
class Employee:
    EmployeeId: int
    LastName: str
    FirstName: str
    Title: str
    ReportsTo: int
    BirthDate: datetime.datetime
    HireDate: datetime.datetime
    Address: str
    City: str
    State: str
    Country: str
    PostalCode: str
    Phone: str
    Fax: str
    Email: str

    def __hash__(self):
        return hash(self.EmployeeId)

    def __eq__(self, other):
        return self.EmployeeId == other.EmployeeId

    def __str__(self):
        return f"{self.FirstName} {self.LastName} [{self.EmployeeId}]"


@dataclass
class Invoice:
    InvoiceId: int
    CustomerId: int
    InvoiceDate: datetime.datetime
    BillingAddress: str
    BillingCity: str
    BillingState: str
    BillingCountry: str
    BillingPostalCode: str
    Total: float

    def __hash__(self):
        return hash(self.InvoiceId)

    def __eq__(self, other):
        return self.InvoiceId == other.InvoiceId

    def __str__(self):
        return f"Fattura {self.InvoiceId} ({self.Total})"


@dataclass
class InvoiceLine:
    InvoiceLineId: int
    InvoiceId: int
    TrackId: int
    UnitPrice: float
    Quantity: int

    def __hash__(self):
        return hash(self.InvoiceLineId)

    def __eq__(self, other):
        return self.InvoiceLineId == other.InvoiceLineId

    def __str__(self):
        return f"Riga {self.InvoiceLineId}"


# Tabella ponte playlisttrack: non ha un id proprio, la chiave è la coppia
@dataclass
class PlaylistTrack:
    PlaylistId: int
    TrackId: int

    def __hash__(self):
        return hash((self.PlaylistId, self.TrackId))

    def __eq__(self, other):
        return self.PlaylistId == other.PlaylistId and self.TrackId == other.TrackId

    def __str__(self):
        return f"Playlist {self.PlaylistId} - Traccia {self.TrackId}"


# ────────────────────────────────────────────────────────────────
# ARCO ESPLICITO — per le query che restituiscono (nodo1, nodo2, peso)
# Uso:  Arco(**row)   con SELECT ... AS id1, ... AS id2, ... AS peso
# ────────────────────────────────────────────────────────────────
@dataclass
class Arco:
    id1: int
    id2: int
    peso: float

    def __hash__(self):
        return hash((self.id1, self.id2))

    def __eq__(self, other):
        return self.id1 == other.id1 and self.id2 == other.id2

    def __str__(self):
        return f"{self.id1} -- {self.id2} (peso {self.peso})"


# ────────────────────────────────────────────────────────────────
# NODO PERSONALIZZATO — quando la traccia vuole un nodo "aggregato"
# (es. artista + numero di album, cliente + totale speso) o quando la
# query restituisce solo alcune colonne.
# ────────────────────────────────────────────────────────────────
class ArtistaConAlbum:
    def __init__(self, id, nome, nAlbum):
        self.id = id
        self.nome = nome
        self.nAlbum = nAlbum

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return f"{self.nome} ({self.nAlbum} album)"

    def __repr__(self):
        return f"ArtistaConAlbum({self.id}, {self.nome!r}, {self.nAlbum})"


# ================================================================
# 3. DAO — STRUTTURA BASE (model/DAO.py)
# ================================================================
# Schema fisso, da ricopiare per ogni metodo:
#   1) connessione  → se None, esci subito
#   2) cursor(dictionary=True)  → row["NomeColonna"]
#      (cursor() semplice → row è una tupla: for a, b in cursor)
#   3) try: execute + riempi result   except: stampa errore
#   4) finally: chiudi SEMPRE cursor e connessione
#   5) return result
#
# Parametri: sempre %s + tupla, MAI f-string dentro la query.
#   cursor.execute(query, (parametro,))      ← la virgola serve!
#   cursor.execute(query, (p1, p2))
#
# NB: nell'esame la classe di connessione è già nel template del prof
# (DBConnect.get_connection()): usa quella che trovi lì. Se invece trovi
# DAO.getConnection() (come nel mio primo template), scrivi
#   conn = DAO.getConnection()   al posto di   cnx = DBConnect.get_connection()

"""
import mysql.connector

from database.DB_connect import DBConnect
from model.nome_oggetto import NomeOggetto
from model.entities import (Artist, Album, Track, Genre, MediaType, Playlist,
                            Customer, Employee, Invoice, InvoiceLine, Arco)


class DAO:

    # ── (ORIGINALE) Lista di valori SEMPLICI: nomi dei generi ─────
    @staticmethod
    def getAllGenres():
        cnx = DBConnect.get_connection()
        if cnx is None:
            print("Connessione fallita")
            return []
        cursor = cnx.cursor(dictionary=True)
        result = []
        try:
            query = "SELECT * FROM genre ORDER BY Name"
            cursor.execute(query)
            for row in cursor:
                result.append(row["Name"])
        except Exception as e:                    # oppure mysql.connector.Error
            print(f"Errore in getAllGenres: {e}")
        finally:
            cursor.close()
            cnx.close()
        return result

    # ── Lista di OGGETTI (per dropdown con data=oggetto, o per nodi) ──
    @staticmethod
    def getAllGenreObjects():
        cnx = DBConnect.get_connection()
        if cnx is None:
            print("Connessione fallita")
            return []
        cursor = cnx.cursor(dictionary=True)
        result = []
        try:
            query = "SELECT * FROM genre ORDER BY Name"
            cursor.execute(query)
            for row in cursor:
                result.append(Genre(**row))      # row = {"GenreId":.., "Name":..}
        except Exception as e:
            print(f"Errore in getAllGenreObjects: {e}")
        finally:
            cursor.close()
            cnx.close()
        return result

    # ── (ORIGINALE) NODI con parametro — schema generico ──────────
    @staticmethod
    def getAllNodes(parametro):
        cnx = DBConnect.get_connection()
        if cnx is None:
            print("Connessione fallita")
            return []
        cursor = cnx.cursor(dictionary=True)
        result = []
        try:
            query = "SELECT ... FROM ... WHERE ... = %s"
            cursor.execute(query, (parametro,))
            for row in cursor:
                result.append(NomeOggetto(row["Id"], row["Name"]))
        except Exception as e:
            print(f"Errore in getAllNodes: {e}")
        finally:
            cursor.close()
            cnx.close()
        return result

    # ── NODI con parametro (%s) — esempio Chinook ─────────────────
    @staticmethod
    def getCustomersByGenre(genreName):
        cnx = DBConnect.get_connection()
        if cnx is None:
            print("Connessione fallita")
            return []
        cursor = cnx.cursor(dictionary=True)
        result = []
        try:
            query = '''SELECT DISTINCT c.*
                       FROM customer c, invoice i, invoiceline il, track t, genre g
                       WHERE c.CustomerId = i.CustomerId
                       AND i.InvoiceId = il.InvoiceId
                       AND il.TrackId = t.TrackId
                       AND t.GenreId = g.GenreId
                       AND g.Name = %s'''
            cursor.execute(query, (genreName,))
            for row in cursor:
                result.append(Customer(**row))   # c.* = tutte le colonne di customer
        except Exception as e:
            print(f"Errore in getCustomersByGenre: {e}")
        finally:
            cursor.close()
            cnx.close()
        return result

    # ── NODI con soglia numerica (HAVING) ─────────────────────────
    @staticmethod
    def getAlbumsMinTracks(n):
        cnx = DBConnect.get_connection()
        if cnx is None:
            print("Connessione fallita")
            return []
        cursor = cnx.cursor(dictionary=True)
        result = []
        try:
            query = '''SELECT a.AlbumId, a.Title, a.ArtistId
                       FROM album a, track t
                       WHERE a.AlbumId = t.AlbumId
                       GROUP BY a.AlbumId, a.Title, a.ArtistId
                       HAVING COUNT(t.TrackId) >= %s'''
            cursor.execute(query, (n,))
            for row in cursor:
                result.append(Album(**row))
        except Exception as e:
            print(f"Errore in getAlbumsMinTracks: {e}")
        finally:
            cursor.close()
            cnx.close()
        return result

    # ── ARCHI con peso calcolato in SQL (CASO B / C del model) ────
    @staticmethod
    def getEdgesPlaylistConTracceInComune():
        cnx = DBConnect.get_connection()
        if cnx is None:
            print("Connessione fallita")
            return []
        cursor = cnx.cursor(dictionary=True)
        result = []
        try:
            query = '''SELECT pt1.PlaylistId AS id1, pt2.PlaylistId AS id2,
                              COUNT(DISTINCT pt1.TrackId) AS peso
                       FROM playlisttrack pt1, playlisttrack pt2
                       WHERE pt1.TrackId = pt2.TrackId
                       AND pt1.PlaylistId < pt2.PlaylistId
                       GROUP BY pt1.PlaylistId, pt2.PlaylistId'''
            cursor.execute(query)
            for row in cursor:
                result.append(Arco(**row))       # Arco(id1=.., id2=.., peso=..)
        except Exception as e:
            print(f"Errore in getEdgesPlaylist: {e}")
        finally:
            cursor.close()
            cnx.close()
        return result

    # ── COPPIE (condiviso, nodo) per i CASI D/E (cursor semplice) ─
    @staticmethod
    def getCustomerArtistPairs():
        cnx = DBConnect.get_connection()
        if cnx is None:
            print("Connessione fallita")
            return []
        cursor = cnx.cursor()                    # senza dictionary → tuple
        result = []
        try:
            query = '''SELECT i.CustomerId, al.ArtistId
                       FROM invoice i, invoiceline il, track t, album al
                       WHERE i.InvoiceId = il.InvoiceId
                       AND il.TrackId = t.TrackId
                       AND t.AlbumId = al.AlbumId
                       GROUP BY i.CustomerId, al.ArtistId'''
            cursor.execute(query)
            for (condiviso, nodo) in cursor:
                result.append((condiviso, nodo))
        except Exception as e:
            print(f"Errore in getCustomerArtistPairs: {e}")
        finally:
            cursor.close()
            cnx.close()
        return result

    # ── TRIPLE (condiviso, nodo, valore) per il CASO F ────────────
    @staticmethod
    def getPlaylistArtistCount():
        cnx = DBConnect.get_connection()
        if cnx is None:
            print("Connessione fallita")
            return []
        cursor = cnx.cursor()
        result = []
        try:
            query = '''SELECT pt.PlaylistId, al.ArtistId, COUNT(*) AS n
                       FROM playlisttrack pt, track t, album al
                       WHERE pt.TrackId = t.TrackId
                       AND t.AlbumId = al.AlbumId
                       GROUP BY pt.PlaylistId, al.ArtistId'''
            cursor.execute(query)
            for (condiviso, nodo, valore) in cursor:
                result.append((condiviso, nodo, valore))
        except Exception as e:
            print(f"Errore in getPlaylistArtistCount: {e}")
        finally:
            cursor.close()
            cnx.close()
        return result

    # ── Valore per nodo (dizionario id → valore), per il CASO G ───
    @staticmethod
    def getTotaleSpesoPerCliente():
        cnx = DBConnect.get_connection()
        if cnx is None:
            print("Connessione fallita")
            return {}
        cursor = cnx.cursor(dictionary=True)
        result = {}
        try:
            query = '''SELECT CustomerId, SUM(Total) AS tot
                       FROM invoice GROUP BY CustomerId'''
            cursor.execute(query)
            for row in cursor:
                result[row["CustomerId"]] = float(row["tot"])   # Decimal → float
        except Exception as e:
            print(f"Errore in getTotaleSpesoPerCliente: {e}")
        finally:
            cursor.close()
            cnx.close()
        return result
"""


# ================================================================
# 4. MODEL — STRUTTURA BASE + METODI BASE DEL GRAFO (model/model.py)
# ================================================================
"""
from model.DAO import DAO
"""

class Model:
    def __init__(self):
        self._graph = nx.Graph()       # oppure nx.DiGraph()
        self._idMap = {}               # id -> oggetto nodo
        self._bestPath = []
        self._bestScore = 0

    def getGraphDetails(self):
        return len(self._graph.nodes), len(self._graph.edges)

    # ---- NUMERO NODI / ARCHI (quelli che chiama il controller) ----
    def getNumNodi(self):
        return self._graph.number_of_nodes()      # = len(self._graph.nodes)

    def getNumEdges(self):
        return self._graph.number_of_edges()      # = len(self._graph.edges)

    # ---- NODI ----
    def getNodes(self):
        return list(self._graph.nodes)

    def getNodesSorted(self):
        # ordinati per nome (str(n) è il __str__ della classe)
        lista = []
        for n in self._graph.nodes:
            lista.append(n)
        lista.sort(key=lambda x: str(x))
        return lista

    def getNodeById(self, id):
        return self._idMap.get(id)      # None se non esiste

    def hasNode(self, nodo):
        return nodo in self._graph

    # ---- ARCHI ----
    def getEdges(self):
        # lista di tuple (u, v, {"weight": w})  →  edge[0], edge[1], edge[2]["weight"]
        return list(self._graph.edges(data=True))

    def getEdgesWeighted(self):
        # lista di tuple (u, v, peso)
        lista = []
        for edge in self.getEdges():
            lista.append((edge[0], edge[1], edge[2]["weight"]))
        return lista

    def getEdgesOrdinati(self):
        # (u, v, peso) con peso decrescente; a parità di peso, per nome.
        # In ogni arco metto prima il nodo con nome minore (grafo NON orientato).
        # Nota: .Name va cambiato col campo della classe (Customer: LastName, Album: Title)
        # Grafo ORIENTATO: niente scambio, l'arco ha già un verso:
        #     lista.append((edge[0], edge[1], edge[2]["weight"]))
        lista = []
        for edge in self.getEdges():
            if edge[0].Name <= edge[1].Name:
                lista.append((edge[0], edge[1], edge[2]["weight"]))
            else:
                lista.append((edge[1], edge[0], edge[2]["weight"]))

        lista.sort(key=lambda x: (-x[2], x[0].Name, x[1].Name))
        return lista

    def getPesoArco(self, u, v):
        if self._graph.has_edge(u, v):
            return self._graph[u][v]["weight"]
        return None

    # ---- GRAFO COSTRUITO? (utile nel controller prima di cercare cammini) ----
    def graphIsBuilt(self):
        return self._graph.number_of_nodes() > 0


# ================================================================
# 5. COSTRUZIONE GRAFO — BUILD GRAPH
# ================================================================

    # Template generico
    def buildGraph(self, parametro):
        self._graph.clear()            # SEMPRE: se premo il bottone due volte

        # 1) Nodi
        nodes = []  # DAO.getAllNodes(parametro)
        self._idMap = {}
        for n in nodes:
            self._idMap[n.ArtistId] = n     # n.<NomeColonnaId> della tua classe
            #                                 (nei template del prof: n.id)
        self._graph.add_nodes_from(nodes)

        # 2) Archi (scegli la casistica sotto)
        self._addEdges(parametro)
        # ↑ sostituisci con la casistica che ti serve:
        #   self._addEdges_casoA()  ...  self._addEdges_casoG()


# ================================================================
# 6. ARCHI — TUTTE LE CASISTICHE
# ================================================================
# In tutti i casi: controlla che i due estremi siano NEI nodi del grafo
# (i nodi sono filtrati dalla query, gli archi potrebbero riferirsi a nodi
# esclusi → con l'idMap darebbe KeyError, con add_edge creerebbe nodi extra).

# ────────────────────────────────────────────────────────────────
# CASO A — Arco esplicito nel DB, senza peso
# Esempio: Metro Paris (tabella connessione con id_stazP, id_stazA)
# ────────────────────────────────────────────────────────────────

    def _addEdges_casoA(self):
        edges = []  # DAO.getAllEdges()
        for e in edges:
            if e.id_partenza in self._idMap and e.id_arrivo in self._idMap:
                u = self._idMap[e.id_partenza]
                v = self._idMap[e.id_arrivo]
                self._graph.add_edge(u, v)


# ────────────────────────────────────────────────────────────────
# CASO B — Arco esplicito, peso = conteggio SQL
# SQL: SELECT col1, col2, COUNT(*) as peso FROM ... GROUP BY col1, col2
# ────────────────────────────────────────────────────────────────
    def _addEdges_casoB(self):
        edges = []  # DAO.getAllEdges()  → oggetti Arco(id1, id2, peso)
        for e in edges:
            if e.id1 not in self._idMap or e.id2 not in self._idMap:
                continue
            u = self._idMap[e.id1]
            v = self._idMap[e.id2]
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
            if id1 in self._idMap and id2 in self._idMap:
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
        condivisoMap = defaultdict(list)  # oppure dict
        for condiviso, nodo in result:
            condivisoMap[condiviso].append(nodo)

        # crea archi con peso = n. elementi condivisi
        pesoArco = defaultdict(int)
        for condiviso, nodi in condivisoMap.items():
            for a, b in itertools.combinations(nodi, 2):
                pesoArco[(a, b)] += 1
                # ATTENZIONE: se i nodi in 'nodi' non sono ordinati, (a,b) e (b,a)
                # potrebbero finire come chiavi diverse. Se serve: nodi = sorted(nodi)

        for (a, b), peso in pesoArco.items():
            if a in self._idMap and b in self._idMap:
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

        self._addEdgesDiretti(coppie, popolarita)

    # Parte comune ai casi E e F: arco dal più popolare al meno popolare
    # (a parità → due archi, uno per verso). Il grafo deve essere nx.DiGraph().
    def _addEdgesDiretti(self, coppie, popolarita):
        for (a, b) in coppie:
            if a not in self._idMap or b not in self._idMap:
                continue
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

        self._addEdgesDiretti(coppie, popolarita)


# ────────────────────────────────────────────────────────────────
# CASO G — Grafo completo (tutti i nodi collegati tra loro)
# Quando: la traccia dice "tutti collegati" — nessuna query archi
# ────────────────────────────────────────────────────────────────

    def _addEdges_casoG(self):
        edges = list(itertools.combinations(self._graph.nodes, 2))
        self._graph.add_edges_from(edges)
        # pesi calcolati dopo, in un loop separato
        # mapValori = DAO.getValori(...)      → dict  id → valore
        # for u, v in self._graph.edges:
        #     self._graph[u][v]["weight"] = mapValori[u.CustomerId] + mapValori[v.CustomerId]


# ================================================================
# 7. QUANDO USARE COSA — REGOLA RAPIDA
# ================================================================
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
# Verso (orientato)           → CASO E o F   (e self._graph = nx.DiGraph())
# Grafo completo              → CASO G
# Arco già scritto nel DB     → CASO A (senza peso) o B (con peso)
# ════════════════════════════════════════════════════════════════


# ================================================================
# 8. ANALISI GRAFO — FUNZIONI UTILI
# ================================================================

    # --- Info base ---
    # len(self._graph.nodes)
    # len(self._graph.edges)
    # self._graph.edges(data=True)   → lista (u, v, {"weight": w})
    # self._graph.nodes(data=True)   → lista (n, {attributi})
    # nx.get_edge_attributes(self._graph, "weight")  → dict {(u,v): peso}

    # --- Vicini ---
    # self._graph.neighbors(nodo)    → Graph non orientato, nodi adiacenti a quello selezionato (es in flight)
    # self._graph.successors(nodo)   → DiGraph (solo uscenti)
    # self._graph.predecessors(nodo) → DiGraph (solo entranti)
    # (se il nodo NON è nel grafo → nx.NetworkXError: controlla prima  nodo in self._graph)

    def getVicini(self, source):
        if source not in self._graph:               # CONTROLLO: nodo non nel grafo
            return []
        vicini = self._graph.neighbors(source)      # DiGraph: successors
        viciniTuples = []
        for v in vicini:
            viciniTuples.append((v, self._graph[source][v]["weight"]))

        viciniTuples.sort(key=lambda x: x[1], reverse=True)

        return viciniTuples

    # --- Grado ---
    # self._graph.degree(nodo)       → Graph (numero di archi)
    # self._graph.degree(nodo, weight="weight")  → grado pesato (somma pesi)
    # self._graph.out_degree(nodo)   → DiGraph uscenti
    # self._graph.in_degree(nodo)    → DiGraph entranti

    # --- Archi con peso ---
    # self._graph.edges(nodo, data=True)      → Graph
    # self._graph.out_edges(nodo, data=True)  → DiGraph uscenti
    # self._graph.in_edges(nodo, data=True)   → DiGraph entranti

    # --- Connettività (solo Graph) ---
    # nx.node_connected_component(self._graph, nodo)  → set nodi raggiungibili:
    #     return v1 in nx.node_connected_component(self._graph, v0)  # true se esiste cammino tra v0 e v1
    # nx.number_connected_components(self._graph)      → intero
    # components = list(nx.connected_components(self._graph))
    # largest = max(components, key=len)
    # nx.is_connected(self._graph)                     → bool (grafo intero; su grafo vuoto
    #                                                      dà nx.NetworkXPointlessConcept)
    # nx.has_path(self._graph, u, v)                   → bool, True se esiste cammino
    #
    # --- Connettività (DiGraph) ---
    # nx.descendants(self._graph, nodo)        → nodi raggiungibili da nodo
    # nx.ancestors(self._graph, nodo)          → nodi da cui si raggiunge nodo
    # nx.weakly_connected_components(self._graph)
    # nx.strongly_connected_components(self._graph)

    def isConnessi(self, v0, v1):
        """True se esiste un cammino tra v0 e v1 (Graph)."""
        # CONTROLLO: se v0 non è nel grafo, networkx dà KeyError
        if v0 not in self._graph or v1 not in self._graph:
            return False
        return v1 in nx.node_connected_component(self._graph, v0)

    def getComponenteConnessa(self, nodo):
        if nodo not in self._graph:                 # CONTROLLO: nodo non nel grafo (KeyError)
            return set()
        return nx.node_connected_component(self._graph, nodo)

    def getComponentePiuGrande(self):
        components = list(nx.connected_components(self._graph))
        if len(components) == 0:                    # CONTROLLO: grafo vuoto
            return set()
        largest = components[0]
        for c in components:
            if len(c) > len(largest):
                largest = c
        return largest

    # --- Sotto-grafo ---
    # subgraph = self._graph.subgraph(largest).copy()

    # --- Cammini minimi ---
    # nx.dijkstra_path(self._graph, u, v)              → percorso pesato [u, ..., v]
    # nx.dijkstra_path_length(self._graph, u, v)       → costo
    # costo, path = nx.single_source_dijkstra(self._graph, u, v)
    # nx.shortest_path(self._graph, u, v)              → percorso con meno archi (ignora pesi)
    # nx.shortest_path_length(self._graph, u, v)       → n. archi
    # (i pesi usati sono quelli dell'attributo "weight"; per cambiare: weight="altro")
    # Eccezioni: nx.NetworkXNoPath (nessun cammino), nx.NodeNotFound (nodo non nel grafo)

    def getCamminoMinimo(self, u, v):
        """Restituisce (costo, path) oppure (None, []) se non esiste cammino."""
        try:
            costo, path = nx.single_source_dijkstra(self._graph, u, v)
            return costo, path
        except nx.NetworkXNoPath:
            return None, []
        except nx.NodeNotFound:
            return None, []

    # VEDI ALTRI PERCORSI IN FLIGHT DELAY MODEL-GET PATH

    # --- Visite ---
    # archi = nx.bfs_edges(self._graph, source)  → coppie (u,v) ampiezza
    # archi = nx.dfs_edges(self._graph, source)  → coppie (u,v) profondità
    # nodi_raggiunti = [v for u, v in nx.bfs_edges(self._graph, source)]
    # albero = nx.bfs_tree(self._graph, source)  → sotto-grafo dell'albero di visita
    # albero = nx.dfs_tree(self._graph, source)

    def getRaggiungibili(self, source):
        if source not in self._graph:               # CONTROLLO: nodo non nel grafo
            return []
        nodi_raggiunti = []
        for u, v in nx.bfs_edges(self._graph, source):
            nodi_raggiunti.append(v)
        return nodi_raggiunti

    # --- Arco di peso massimo / minimo ---
    def getArcoMaxPeso(self):
        archi = self.getEdgesWeighted()
        if len(archi) == 0:                         # CONTROLLO: nessun arco
            return None
        migliore = archi[0]
        for a in archi:
            if a[2] > migliore[2]:
                migliore = a
        return migliore

    def getArcoMinPeso(self):
        archi = self.getEdgesWeighted()
        if len(archi) == 0:
            return None
        migliore = archi[0]
        for a in archi:
            if a[2] < migliore[2]:
                migliore = a
        return migliore

    # --- Archi con peso maggiore di una soglia ---
    def getArchiOltreSoglia(self, soglia):
        lista = []
        for edge in self.getEdgesWeighted():
            if edge[2] > soglia:
                lista.append(edge)
        return lista

    # --- Top 5 influenza (DiGraph): somma pesi uscenti - somma pesi entranti ---
    def getTop5Influenza(self):
        scores = []
        for n in self._graph.nodes:
            out = 0
            for edge in self._graph.out_edges(n, data=True):
                out += edge[2]["weight"]
            in_ = 0
            for edge in self._graph.in_edges(n, data=True):
                in_ += edge[2]["weight"]
            scores.append((n, out - in_))

        # punteggio decrescente; a parità, per nome (.Name → campo della tua classe)
        scores.sort(key=lambda x: (-x[1], x[0].Name))
        return scores[:5]

    # --- Top 5 peso totale (Graph): somma dei pesi degli archi del nodo ---
    def getTop5PesoTotale(self):
        scores = []
        for n in self._graph.nodes:
            score = 0
            for edge in self._graph.edges(n, data=True):
                score += edge[2]["weight"]
            scores.append((n, score))

        scores.sort(key=lambda x: (-x[1], x[0].Name))
        return scores[:5]

    # --- Top 5 archi per peso ---
    def getTop5Archi(self):
        return self.getEdgesOrdinati()[:5]

    # --- Nodi con grado massimo ---
    def getNodiGradoMax(self):
        gradoMax = 0
        for n in self._graph.nodes:
            if self._graph.degree(n) > gradoMax:
                gradoMax = self._graph.degree(n)

        lista = []
        for n in self._graph.nodes:
            if self._graph.degree(n) == gradoMax:
                lista.append(n)
        return lista


# ================================================================
# 9. RICORSIONE — TUTTE LE CASISTICHE
# ================================================================
# Per salvare il best uso copy.deepcopy(parziale) (va bene anche list(parziale)):
# senza copia, il pop() successivo modificherebbe anche il best salvato.
#
# SCHEMA GENERALE (tutte le casistiche sono varianti di questo):
#
#   cercaCammino(...):  azzera best, parziale = [partenza], chiama ricorsione
#   _ricorsione(parziale, ...):
#       1) SE la soluzione parziale è valida e migliore → salva (CONDIZIONE DI OTTIMALITÀ)
#       2) SE ho raggiunto il limite → return            (CONDIZIONE DI TERMINAZIONE)
#       3) for ogni vicino che rispetta i vincoli:
#              append → ricorsione → pop                 (BACKTRACKING)
#
# ──────────────────────────────────────────────────────────────────
# TEMPLATE GENERICO DA COMPILARE (i ____ sono i punti da riempire)
# ──────────────────────────────────────────────────────────────────
#
#     def cercaCammino(self, nodoPartenza, ____):
#         self._bestPath = []
#         self._bestScore = 0  # oppure togliere se uso len()
#         parziale = [nodoPartenza]
#
#         # SCELTA 5: primo passo fuori? (solo se vincolo usa parziale[-2])
#         # SE SÌ:
#         #     for v in self._graph._______(nodoPartenza):
#         #         parziale.append(v)
#         #         self._ricorsione(parziale, ____)
#         #         parziale.pop()
#         # SE NO:
#         #     self._ricorsione(parziale, ____)
#         return self._bestPath, self._bestScore
#
#     def _ricorsione(self, parziale, ____):
#         # ──────────────────────────────────────
#         # SCELTA 3: c'è un nodo finale?
#         # SE SÌ (senza lunghezza esatta):
#         #     if parziale[-1] == ____:
#         # SE NO:
#         #     (salvo sempre, senza if)
#         # ──────────────────────────────────────
#
#         # ──────────────────────────────────────
#         # SCELTA 1: cosa ottimizzo?
#         # LUNGHEZZA:  if len(parziale) > len(self._bestPath):
#         # PESO:       if self._score(parziale) > self._bestScore:
#         # ──────────────────────────────────────
#         self._bestPath = copy.deepcopy(parziale)
#         # ──────────────────────────────────────
#         # SCELTA 2: c'è un limite?
#         # ESATTA:   if len(parziale) == lun:
#         #               (mettere ottimalità + nodo finale QUI DENTRO, non sopra)
#         #               return
#         # MASSIMA:  if len(parziale) == t + 1:
#         #               return
#         # NESSUNO:  (niente return)
#         # ──────────────────────────────────────
#
#         # ──────────────────────────────────────
#         # ESPANSIONE
#         # ──────────────────────────────────────
#         for n in self._graph._______(parziale[-1]):
#             #                neighbors (Graph) o successors (DiGraph)
#             # SCELTA 4: vincolo sull'espansione?
#             # NESSUNO:      if n not in parziale:
#             # PESO CRESC:   if n not in parziale and peso_nuovo > peso_prec:
#             # PESO DECRESC: if n not in parziale and peso_nuovo < peso_prec:
#             # ATTRIBUTO:    if n not in parziale and n.attr == parziale[-1].attr:
#             if n not in parziale ____:
#                 parziale.append(n)
#                 self._ricorsione(parziale, ____)
#                 parziale.pop()
#
#     # ESEMPIO ESPANSIONE CON VINCOLO PESO CRESCENTE (DiGraph → successors):
#     #     for n in self._graph.successors(parziale[-1]):
#     #         peso_prec = self._graph[parziale[-2]][parziale[-1]]["weight"]
#     #         peso_nuovo = self._graph[parziale[-1]][n]["weight"]
#     #         if n not in parziale and peso_nuovo > peso_prec:
#     #             parziale.append(n)
#     #             self._ricorsione(parziale)
#     #             parziale.pop()
#
#     # ALTRO MODO UGUALE PER NON DOVER FARE IL PRIMO PASSO FUORI
#     # (lo trovi funzionante sotto come CASO R3-ALT):
#     #     def cercaCammino(self, nodoPartenza):
#     #         self._bestPath = []
#     #         parziale = [nodoPartenza]
#     #         self._ricorsione(parziale, -1)  # -1 così qualsiasi peso è > di lastWeight
#     #         return self._bestPath
#     #     # ESPANSIONE
#     #         for _, vicino, data in self._graph.out_edges(parziale[-1], data=True):
#     #             peso = data["weight"]
#     #             if peso > lastWeight and vicino not in parziale:
#     #                 parziale.append(vicino)
#     #                 self._ricorsione(parziale, peso)
#     #                 parziale.pop()
#
# ──────────────────────────────────────────────────────────────────
# RIASSUNTO DELLE SCELTE
# ──────────────────────────────────────────────────────────────────
# SCELTA 1: cosa ottimizzo?  LUNGHEZZA → len(parziale) > len(bestPath)
#                            PESO      → _score(parziale) > bestScore
# SCELTA 2: limite?          ESATTA  → if len(parziale) == lun: (...) return
#                            MASSIMA → if len(parziale) == t + 1: return
#                            NESSUNO → niente return
# SCELTA 3: nodo finale?     SÌ → salvo solo se parziale[-1] == fine
#                            NO → salvo sempre
# SCELTA 4: vincolo?         nessuno / peso crescente / peso decrescente / attributo
# SCELTA 5: primo passo fuori? solo se il vincolo usa parziale[-2]
#
# Graph → self._graph.neighbors(n)      DiGraph → self._graph.successors(n)

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
        # CONDIZIONE DI OTTIMALITA'
        if len(parziale) == lun:
            if parziale[-1] == end and self._score(parziale) > self._bestScore:
                self._bestScore = self._score(parziale)
                self._bestPath = copy.deepcopy(parziale)
            return  # TERMINAZIONE: mi fermo SEMPRE a lunghezza raggiunta

        for n in self._graph.successors(parziale[-1]):  # .neighbors() se Graph
            if n not in parziale:
                parziale.append(n)
                self._ricorsioneR1(parziale, lun, end)
                parziale.pop()


# ────────────────────────────────────────────────────────────────
# CASO R2 — Lunghezza massima + nodo finale
# ────────────────────────────────────────────────────────────────
# (FLIGHT) - PESO MASSIMO
    def getCamminoR2(self, v0, end, t):
        self._bestPath = []
        self._bestScore = 0
        parziale = [v0]
        self._ricorsioneR2(parziale, end, t)
        return self._bestPath, self._bestScore

    def _ricorsioneR2(self, parziale, end, t):
        # salvo se sono arrivato a destinazione (ma NON mi fermo)
        # CONDIZIONE DI OTTIMALITA'
        if parziale[-1] == end:
            if self._score(parziale) > self._bestScore:
                self._bestScore = self._score(parziale)
                self._bestPath = copy.deepcopy(parziale)

        # CONDIZIONE DI TERMINAZIONE
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
# SE C'è VINCOLO SUI PESI, PRIMO PASSO FUORI!! (PARZIALE[-2])
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

        # vedi anche es esercizio


# ────────────────────────────────────────────────────────────────
# CASO R3-ALT — Stesso vincolo sui pesi, ma SENZA primo passo fuori
# Passo l'ultimo peso come parametro (lastWeight): -1 all'inizio così
# qualsiasi peso è > di lastWeight (per pesi DECRESCENTI parti da float('inf')
# e usa  peso < lastWeight).
# ────────────────────────────────────────────────────────────────

    def getCamminoR3alt(self, v0):
        self._bestPath = []
        self._bestScore = 0
        parziale = [v0]
        self._ricorsioneR3alt(parziale, -1)
        return self._bestPath, self._bestScore

    def _ricorsioneR3alt(self, parziale, lastWeight):
        if self._score(parziale) > self._bestScore:
            self._bestScore = self._score(parziale)
            self._bestPath = copy.deepcopy(parziale)

        # ESPANSIONE (DiGraph: out_edges; Graph: self._graph.edges(parziale[-1], data=True))
        for _, vicino, data in self._graph.out_edges(parziale[-1], data=True):
            peso = data["weight"]
            if peso > lastWeight and vicino not in parziale:
                parziale.append(vicino)
                self._ricorsioneR3alt(parziale, peso)
                parziale.pop()


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
            # .attributo = campo della classe nodo (es. .GenreId, .Country, .ArtistId)
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
# CASO FORMULA 1 IN CUI CERCO UN SET  (stessa idea di R5, versione originale)
# ────────────────────────────────────────────────────────────────

    def cercaSet(self, k):
        self._bestSet = []
        self._bestVal = float('inf')  # o 0 se massimizzi
        components = list(nx.connected_components(self._graph))

        if len(components) < k:
            return None, 0

        parziale = []
        self._ricorsioneSet(components, k, parziale, 0)
        return self._bestSet, self._bestVal

    def _ricorsioneSet(self, components, k, parziale, idx):
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
            self._ricorsioneSet(components, k, parziale, idx + 1)
            parziale.pop()

        # SALTO QUESTA COMPONENTE
        self._ricorsioneSet(components, k, parziale, idx + 1)

    def _valuta(self, parziale):
        # ESEMPIO: somma di un attributo dei nodi scelti. Adatta alla traccia.
        totale = 0
        for n in parziale:
            totale += n.ArtistId
        return totale


# ────────────────────────────────────────────────────────────────
# SCORE — funzione peso cammino (uguale per tutte le casistiche)
# ────────────────────────────────────────────────────────────────

    def _score(self, parziale):
        score = 0
        for i in range(len(parziale) - 1):
            score += self._graph[parziale[i]][parziale[i + 1]]["weight"]
        return score

    # Variante: punteggio basato sui NODI (non sugli archi)
    def _scoreNodi(self, parziale):
        score = 0
        for n in parziale:
            score += n.Milliseconds       # esempio con Track
        return score


# ================================================================
# 10. TEST MODEL (test_model.py)
# ================================================================

"""
from model.model import Model

myModel = Model()
myModel.buildGraph("Rock")
nNodes, nEdges = myModel.getGraphDetails()
print(f"Nodi: {nNodes} --- Archi: {nEdges}")
print(f"Nodi: {myModel.getNumNodi()} --- Archi: {myModel.getNumEdges()}")

# stampa nodi e archi
for n in myModel.getNodes()[:10]:
    print(n)
for edge in myModel.getTop5Archi():
    print(f"{edge[0]} -- {edge[1]}  (peso {edge[2]})")

# test ricorsione
# path, score = myModel.getCamminoR1(nodo_partenza, nodo_arrivo, 5)
# print(f"Score: {score}")
# for n in path:
#     print(n)

# test del DAO da solo
# from model.DAO import DAO
# print(DAO.getAllGenres())
"""


# ================================================================
# 11. CONTROLLER — TEMPLATE COMPLETO (UI/controller.py)
# ================================================================

class Controller:
    def __init__(self, view, model):
        self._view = view
        self._model = model
        self._sceltaDD1 = None
        self._sceltaDD2 = None

    # --- ERRORE HELPER (evita ripetizioni) ---
    def _showError(self, msg, color="red"):
        self._view._txt_result.controls.clear()
        self._view._txt_result.controls.append(ft.Text(msg, color=color))
        self._view.update_page()

    # --- RIEMPIRE DROPDOWN CON OGGETTI (on_click) ---
    def fillDDOggetti(self, lista):
        self._view._dd1.options.clear()
        for o in lista:
            self._view._dd1.options.append(
                ft.dropdown.Option(
                    data=o,       # serve ad associare un oggetto all'opzione
                    key=str(o),   # quello che ottieni con .value, anche quella che mostro nel dd
                    on_click=self._handleDD1
                )
            )
        self._view.update_page()

    def _handleDD1(self, e):
        self._sceltaDD1 = e.control.data  # ridà l'oggetto salvato nel dd

    # --- RIEMPIRE DROPDOWN CON VALORI SEMPLICI (on_change sul DD) ---
    def fillDDValori(self, lista):
        # (versione compatta: self._view._dd2.options = list(map(lambda x: ft.dropdown.Option(x), lista)))
        self._view._dd2.options.clear()
        for x in lista:
            self._view._dd2.options.append(ft.dropdown.Option(x))
        self._view.update_page()

    # on_change è nella view: on_change=self._controller.handleDD2
    def handleDD2(self, e):
        self._sceltaDD2 = self._view._dd2.value

    # --- HANDLER CREA GRAFO (con validazione dropdown) ---
    def handleCreaGrafo(self, e):
        # CONTROLLO: nessuna scelta nel dropdown
        if self._sceltaDD1 is None:
            self._showError("Selezionare un valore dal menu.")
            return

        self._model.buildGraph(self._sceltaDD1)

        self._view._txt_result.controls.clear()

        # CONTROLLO: la query non ha restituito nodi → grafo vuoto
        if self._model.getNumNodi() == 0:
            self._view._txt_result.controls.append(
                ft.Text("Nessun nodo trovato: il grafo è vuoto.", color="orange")
            )
            self._view.update_page()
            return

        self._view._txt_result.controls.append(
            ft.Text("Grafo correttamente creato.")
        )
        self._view._txt_result.controls.append(
            ft.Text(f"Numero nodi: {self._model.getNumNodi()}")
        )
        self._view._txt_result.controls.append(
            ft.Text(f"Numero archi: {self._model.getNumEdges()}")
        )
        self._view.update_page()

    # --- HANDLER CREA GRAFO (con validazione input numerico) ---
    def handleCreaGrafoConInput(self, e):
        txt = self._view._txtInput.value.strip()

        # CONTROLLO: campo vuoto
        if txt == "":
            self._showError("Inserire un valore.")
            return

        # CONTROLLO: non è un numero  (float(txt) se la traccia vuole un decimale)
        try:
            val = int(txt)
        except ValueError:
            self._showError("Inserire un valore intero.")
            return

        # CONTROLLO: fuori range
        if val < 1 or val > 100:
            self._showError("Inserire un valore tra 1 e 100.")
            return

        self._model.buildGraph(val)

        self._view._txt_result.controls.clear()

        if self._model.getNumNodi() == 0:
            self._view._txt_result.controls.append(
                ft.Text("Nessun nodo trovato: il grafo è vuoto.", color="orange")
            )
            self._view.update_page()
            return

        self._view._txt_result.controls.append(
            ft.Text("Grafo correttamente creato.")
        )
        self._view._txt_result.controls.append(
            ft.Text(f"Numero nodi: {self._model.getNumNodi()}")
        )
        self._view._txt_result.controls.append(
            ft.Text(f"Numero archi: {self._model.getNumEdges()}")
        )
        self._view.update_page()

    # --- HANDLER: STAMPA I 5 ARCHI DI PESO MAGGIORE ---
    def handleTopArchi(self, e):
        # CONTROLLO: grafo non ancora creato
        if not self._model.graphIsBuilt():
            self._showError("Creare prima il grafo.")
            return

        self._view._txt_result.controls.clear()
        for edge in self._model.getTop5Archi():
            self._view._txt_result.controls.append(
                ft.Text(f"{edge[0]} -- {edge[1]}  (peso {edge[2]})")
            )
        self._view.update_page()

    # --- HANDLER: VICINI DEL NODO SELEZIONATO (ordinati per peso) ---
    def handleVicini(self, e):
        if not self._model.graphIsBuilt():
            self._showError("Creare prima il grafo.")
            return
        if self._sceltaDD1 is None:
            self._showError("Selezionare un nodo.")
            return

        vicini = self._model.getVicini(self._sceltaDD1)

        self._view._txt_result.controls.clear()
        # CONTROLLO: nodo non nel grafo oppure senza vicini
        if len(vicini) == 0:
            self._view._txt_result.controls.append(
                ft.Text("Nessun vicino per il nodo selezionato.", color="orange")
            )
        for v, peso in vicini:
            self._view._txt_result.controls.append(ft.Text(f"{v}  -  peso {peso}"))
        self._view.update_page()

    # --- HANDLER CERCA CAMMINO ---
    def handleCercaCammino(self, e):
        if not self._model.graphIsBuilt():
            self._showError("Creare prima il grafo.")
            return
        if self._sceltaDD1 is None:
            self._showError("Selezionare nodo di partenza.")
            return
        # CONTROLLO: il nodo scelto deve essere nel grafo (es. grafo ricreato con altro parametro)
        if not self._model.hasNode(self._sceltaDD1):
            self._showError("Il nodo selezionato non è nel grafo.")
            return

        # NB: getCamminoR1 vuole un nodo finale: con None non trova mai nulla.
        # Per "nessun nodo finale" usa R3 / R3bis / R4 (che non lo richiedono).
        try:
            path, score = self._model.getCamminoR1(self._sceltaDD1, None, 5)
        except nx.NetworkXError:        # nodo di partenza non presente nel grafo
            self._showError("Il nodo selezionato non è nel grafo.")
            return
        except RecursionError:          # ricorsione troppo profonda
            self._showError("Ricerca troppo profonda: ridurre la lunghezza.")
            return

        self._view._txt_result.controls.clear()
        if not path:
            self._view._txt_result.controls.append(
                ft.Text("Nessun cammino trovato.", color="orange"))
        else:
            self._view._txt_result.controls.append(
                ft.Text(f"Cammino trovato con score {score}.", color="green"))
            for n in path:
                self._view._txt_result.controls.append(ft.Text(f"{n}"))
        self._view.update_page()


# ================================================================
# 12. VIEW + MAIN (FLET) — SOLO COME RIFERIMENTO
# ================================================================
# All'esame view.py e main.py sono GIÀ forniti dal prof: non riscriverli.
# Servono per sapere i nomi dei widget che il controller usa
# (_dd1, _txtInput, _txt_result, update_page...). La versione di flet può
# cambiare qualche nome (es. ft.app / ft.run): segui il template dell'esame.

"""
# ---------- UI/view.py ----------
import flet as ft

class View:
    def __init__(self, page: ft.Page):
        self._page = page
        self._page.title = "TdP - Esame"
        self._page.horizontal_alignment = "CENTER"
        self._page.theme_mode = ft.ThemeMode.LIGHT
        self._controller = None

    def load_interface(self):
        self._title = ft.Text("Titolo", color="blue", size=24)
        self._page.controls.append(self._title)

        self._dd1 = ft.Dropdown(label="Scelta 1", width=250)
        self._dd2 = ft.Dropdown(label="Scelta 2", width=250,
                                on_change=self._controller.handleDD2)
        self._txtInput = ft.TextField(label="Valore", width=150)
        self._btnCrea = ft.ElevatedButton(text="Crea grafo",
                                          on_click=self._controller.handleCreaGrafo)
        self._btnCammino = ft.ElevatedButton(text="Cerca cammino",
                                             on_click=self._controller.handleCercaCammino)

        row1 = ft.Row([self._dd1, self._dd2, self._txtInput, self._btnCrea],
                      alignment=ft.MainAxisAlignment.CENTER)
        row2 = ft.Row([self._btnCammino], alignment=ft.MainAxisAlignment.CENTER)
        self._page.controls.extend([row1, row2])

        self._txt_result = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=True)
        self._page.controls.append(self._txt_result)

        # riempio i dropdown all'avvio
        # self._controller.fillDDOggetti(DAO.getAllGenreObjects())
        self._page.update()

    def set_controller(self, controller):
        self._controller = controller

    def update_page(self):
        self._page.update()


# ---------- main.py ----------
import flet as ft
from UI.view import View
from UI.controller import Controller
from model.model import Model

def main(page: ft.Page):
    view = View(page)
    model = Model()
    controller = Controller(view, model)
    view.set_controller(controller)
    view.load_interface()

ft.app(target=main)
"""


# ================================================================
# 13. SCHEMA CHINOOK E CATENE JOIN — RIFERIMENTO RAPIDO
# ================================================================

"""
TABELLE E CHIAVI  (→ = chiave esterna)
    artist        (ArtistId, Name)
    album         (AlbumId, Title, ArtistId → artist)
    track         (TrackId, Name, AlbumId → album, MediaTypeId → mediatype,
                   GenreId → genre, Composer, Milliseconds, Bytes, UnitPrice)
    genre         (GenreId, Name)
    mediatype     (MediaTypeId, Name)
    playlist      (PlaylistId, Name)
    playlisttrack (PlaylistId → playlist, TrackId → track)
    customer      (CustomerId, FirstName, LastName, Company, Address, City, State,
                   Country, PostalCode, Phone, Fax, Email, SupportRepId → employee)
    employee      (EmployeeId, LastName, FirstName, Title, ReportsTo → employee,
                   BirthDate, HireDate, Address, City, State, Country, PostalCode,
                   Phone, Fax, Email)
    invoice       (InvoiceId, CustomerId → customer, InvoiceDate, BillingAddress,
                   BillingCity, BillingState, BillingCountry, BillingPostalCode, Total)
    invoiceline   (InvoiceLineId, InvoiceId → invoice, TrackId → track,
                   UnitPrice, Quantity)

CATENE
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
# 14. QUERY SQL RICORRENTI — RIFERIMENTO RAPIDO
# ================================================================
# Per creare l'oggetto con Classe(**row) la SELECT deve restituire TUTTE
# le colonne della classe (usa  x.*  oppure elencale tutte).

"""
-- ===================== NODI =====================

-- Nodi: artisti con almeno una traccia acquistata
SELECT DISTINCT a.ArtistId, a.Name
FROM artist a, album al, track t, invoiceline il
WHERE a.ArtistId = al.ArtistId
AND al.AlbumId = t.AlbumId
AND t.TrackId = il.TrackId

-- Nodi: clienti che hanno acquistato genere X
-- (per Customer(**row) usa  SELECT DISTINCT c.*  invece delle 3 colonne)
SELECT DISTINCT c.CustomerId, c.FirstName, c.LastName
FROM customer c, invoice i, invoiceline il, track t, genre g
WHERE c.CustomerId = i.CustomerId
AND i.InvoiceId = il.InvoiceId
AND il.TrackId = t.TrackId
AND t.GenreId = g.GenreId
AND g.Name = %s

-- Nodi: album con almeno N tracce
-- (per Album(**row) aggiungi a.ArtistId, anche nel GROUP BY)
SELECT a.AlbumId, a.Title
FROM album a, track t
WHERE a.AlbumId = t.AlbumId
GROUP BY a.AlbumId, a.Title
HAVING COUNT(t.TrackId) >= N

-- Nodi: artisti con almeno N album
SELECT a.ArtistId, a.Name
FROM artist a, album al
WHERE a.ArtistId = al.ArtistId
GROUP BY a.ArtistId, a.Name
HAVING COUNT(al.AlbumId) >= %s

-- Nodi: tracce di un genere con durata tra min e max (millisecondi)
SELECT t.*
FROM track t, genre g
WHERE t.GenreId = g.GenreId
AND g.Name = %s
AND t.Milliseconds BETWEEN %s AND %s

-- Nodi: clienti di un paese
SELECT *
FROM customer
WHERE Country = %s

-- Nodi: playlist con almeno N tracce
SELECT p.PlaylistId, p.Name
FROM playlist p, playlisttrack pt
WHERE p.PlaylistId = pt.PlaylistId
GROUP BY p.PlaylistId, p.Name
HAVING COUNT(pt.TrackId) >= %s

-- Nodi: tutti i dipendenti
SELECT * FROM employee

-- ===================== DROPDOWN / VALORI =====================

-- Anni presenti nelle fatture (per un dropdown)
SELECT DISTINCT YEAR(InvoiceDate) AS anno FROM invoice ORDER BY anno

-- Paesi dei clienti
SELECT DISTINCT Country FROM customer ORDER BY Country

-- ===================== ARCHI PYTHON (condiviso, nodo) =====================

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

-- playlist → traccia  (per "playlist che condividono tracce" in Python)
SELECT PlaylistId, TrackId FROM playlisttrack

-- ===================== ARCHI SQL (peso calcolato) =====================

-- Archi SQL: self-join corta (es. playlist condividono tracce)
SELECT pt1.PlaylistId, pt2.PlaylistId, COUNT(DISTINCT pt1.TrackId) as peso
FROM playlisttrack pt1, playlisttrack pt2
WHERE pt1.TrackId = pt2.TrackId
AND pt1.PlaylistId < pt2.PlaylistId
GROUP BY pt1.PlaylistId, pt2.PlaylistId

-- album collegati se hanno tracce dello stesso genere (peso = n. generi in comune)
SELECT t1.AlbumId, t2.AlbumId, COUNT(DISTINCT t1.GenreId) as peso
FROM track t1, track t2
WHERE t1.GenreId = t2.GenreId
AND t1.AlbumId < t2.AlbumId
GROUP BY t1.AlbumId, t2.AlbumId

-- Archi SQL: employee (gerarchia)
SELECT e2.EmployeeId, e.EmployeeId,
       ABS(TIMESTAMPDIFF(YEAR, e.BirthDate, e2.BirthDate)) as peso
FROM employee e, employee e2
WHERE e.ReportsTo = e2.EmployeeId

-- cliente → dipendente di supporto (arco esplicito)
SELECT c.CustomerId, c.SupportRepId
FROM customer c
WHERE c.SupportRepId IS NOT NULL

-- ===================== VALORI PER NODO (dict id → valore) =====================

-- totale speso per cliente
SELECT CustomerId, SUM(Total) AS tot FROM invoice GROUP BY CustomerId

-- n. tracce acquistate per cliente
SELECT i.CustomerId, SUM(il.Quantity) AS n
FROM invoice i, invoiceline il
WHERE i.InvoiceId = il.InvoiceId
GROUP BY i.CustomerId

-- durata totale per album (millisecondi)
SELECT AlbumId, SUM(Milliseconds) AS durata FROM track GROUP BY AlbumId

-- n. di volte che una traccia è stata venduta
SELECT TrackId, SUM(Quantity) AS venduta FROM invoiceline GROUP BY TrackId

-- ===================== FILTRI UTILI =====================
-- per anno:       AND YEAR(i.InvoiceDate) = %s
-- tra due date:   AND i.InvoiceDate BETWEEN %s AND %s
-- testo parziale: AND t.Name LIKE %s      (passa "%rock%" come parametro)
-- più valori:     AND g.Name IN (%s, %s)
-- NULL:           WHERE colonna IS NULL / IS NOT NULL
"""


# ================================================================
# 15. ECCEZIONI E CONTROLLI — RIEPILOGO DI DOVE SONO NEL FILE
# ================================================================
#
#  DAO (sezione 3)
#   - connessione fallita (cnx is None)            → return lista/dict vuoto
#   - errore SQL / di connessione                   → try / except / finally
#   - chiusura cursor e connessione                 → finally (sempre eseguito)
#
#  MODEL (sezioni 5-8)
#   - estremo dell'arco non presente nei nodi       → controllo "in self._idMap" (casi A-F)
#   - nodo non nel grafo                            → controllo "nodo in self._graph" in getVicini,
#                                                      getRaggiungibili, isConnessi,
#                                                      getComponenteConnessa (senza il controllo
#                                                      networkx dà KeyError o NetworkXError)
#   - nessun cammino / nodo non trovato (dijkstra)  → nx.NetworkXNoPath, nx.NodeNotFound
#                                                      in getCamminoMinimo
#   - grafo vuoto / nessun arco                     → controllo len(...) == 0 in
#                                                      getComponentePiuGrande, getArcoMaxPeso,
#                                                      getArcoMinPeso
#   - troppe componenti richieste (R5)              → if len(components) < k: return None, 0
#
#  CONTROLLER (sezione 11)
#   - dropdown non selezionato (None)               → in ogni handler
#   - campo di testo vuoto                          → txt == ""
#   - testo non numerico                            → try / except ValueError
#   - numero fuori range                            → if val < ... or val > ...
#   - grafo non ancora creato                       → graphIsBuilt()
#   - grafo vuoto dopo la creazione                 → getNumNodi() == 0
#   - nodo non nel grafo / nessun vicino            → lista vuota da getVicini
#   - nodo di partenza non presente                 → except nx.NetworkXError
#   - ricorsione troppo profonda                    → except RecursionError
#   - nessun cammino trovato                        → if not path
#
#  In tutti i casi di errore nel controller: _showError(...) + return, così
#  la pagina viene aggiornata (update_page) e il codice sotto non gira.


# ================================================================
# 16. CHECKLIST ERRORI COMUNI
# ================================================================
#
#  GRAFO
#  [ ] Graph o DiGraph? → neighbors vs successors (e out_edges/in_edges)
#  [ ] self._graph.clear() all'inizio di buildGraph
#  [ ] idMap riempita PRIMA di aggiungere gli archi
#  [ ] estremi dell'arco presenti in idMap / nel grafo prima di add_edge
#  [ ] self-join: sempre  t1.col < t2.col  (altrimenti archi doppi e self-loop)
#  [ ] nodi HASHABLE: __hash__ e __eq__ basati sull'id nella classe
#  [ ] il peso si chiama "weight" (default di dijkstra) e va sempre letto con ["weight"]
#  [ ] Decimal (UnitPrice, Total) → float() prima di sommare con altri float
#  [ ] sommare con += se l'arco può essere già presente (CASO B)
#
#  RICORSIONE
#  [ ] best azzerato (bestPath = [], bestScore = 0) a ogni chiamata
#  [ ] copia di parziale quando salvo il best (deepcopy o list())
#  [ ] append → ricorsione → pop (il pop sempre, anche dopo l'ultima chiamata)
#  [ ] lunghezza ESATTA: ottimalità + nodo finale dentro l'if, poi return
#  [ ] lunghezza MASSIMA: ottimalità sopra, return solo a len == t + 1
#  [ ] vincolo su parziale[-2] → primo passo fuori dalla ricorsione (o lastWeight)
#  [ ] "n not in parziale" per evitare cicli
#  [ ] se è troppo lento: pruning (esci se non puoi più migliorare il best)
#
#  DAO / SQL
#  [ ] parametri con %s e tupla  (param,)  — la virgola!
#  [ ] try / except / finally con cursor.close() e cnx.close()
#  [ ] cnx is None → return subito
#  [ ] cursor(dictionary=True) per row["Colonna"], cursor() per le tuple
#  [ ] nomi colonne della SELECT = nomi dei campi della classe (per Classe(**row))
#  [ ] GROUP BY con tutte le colonne non aggregate
#
#  CONTROLLER / VIEW
#  [ ] controllo dropdown None prima di usarlo
#  [ ] input: strip(), "" → errore, int()/float() dentro try/except ValueError
#  [ ] controls.clear() prima di scrivere un nuovo risultato
#  [ ] self._view.update_page() alla fine di OGNI handler (anche in caso di errore/return)
#  [ ] dropdown con data=oggetto: e.control.data nell'on_click dell'opzione
#  [ ] dropdown con valori semplici: self._view._dd.value (è una stringa!)
#  [ ] grafo creato prima di cercare cammino / vicini / componenti