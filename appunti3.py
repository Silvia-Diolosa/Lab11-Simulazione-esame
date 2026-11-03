import networkx as nx

from database.dao import DAO


class Model:
    def __init__(self):
        self._graph = nx.Graph()
        self._idMap = {}

    # ---------- PUNTO 1a ----------
    def getGenres(self):
        return DAO.getAllGenres()

    # ---------- PUNTO 1b, 1c ----------
    def buildGraph(self, genre: str):
        self._graph.clear()
        self._idMap = {}

        # vertici
        albums = DAO.getAlbums(genre)
        for a in albums:
            self._idMap[a.id] = a
            self._graph.add_node(a)

        # archi pesati
        edges = DAO.getEdges(genre)
        for (id1, id2, peso) in edges:
            self._graph.add_edge(self._idMap[id1], self._idMap[id2], weight=peso)

    # ---------- PUNTO 1d ----------
    def getNumNodes(self):
        return self._graph.number_of_nodes()

    def getNumEdges(self):
        return self._graph.number_of_edges()

    # ---------- PUNTO 1e.a ----------
    def getComponentsInfo(self):
        """Restituisce (numero di componenti connesse, dimensione della componente piu' grande)."""
        componenti = list(nx.connected_components(self._graph))
        maxSize = 0
        for c in componenti:
            if len(c) > maxSize:
                maxSize = len(c)
        return len(componenti), maxSize

    # ---------- PUNTO 1e.b ----------
    def getMaxDegreeAlbum(self):
        """Restituisce l'album di grado massimo (a parita' il primo in ordine alfabetico di titolo)
        e la lista dei suoi adiacenti come tuple (album, peso), per peso decrescente
        (a parita' di peso, ordine alfabetico di titolo)."""
        if self._graph.number_of_nodes() == 0:
            return None, []

        # scorro i nodi in ordine alfabetico di titolo: tengo il primo con grado massimo
        nodi = list(self._graph.nodes())
        nodi.sort(key=lambda x: x.title)

        best = None
        bestDegree = -1
        for n in nodi:
            grado = self._graph.degree(n)
            if grado > bestDegree:
                bestDegree = grado
                best = n

        adiacenti = []
        for v in self._graph.neighbors(best):
            peso = self._graph[best][v]["weight"]
            adiacenti.append((v, peso))
        # prima peso decrescente, poi titolo crescente
        adiacenti.sort(key=lambda x: (-x[1], x[0].title))

        return best, adiacenti

    # ---------- PUNTO 1e.c ----------
    def getNumEdgesSameArtist(self):
        """Numero di archi che collegano due album dello stesso artista."""
        count = 0
        for (u, v) in self._graph.edges():
            if u.artistId == v.artistId:
                count += 1
        return count



from database.DB_connect import DBConnect
from model.album import Album


class DAO:

    @staticmethod
    def getAllGenres():
        """Restituisce la lista dei nomi dei generi (Genre.Name) presenti nel database."""
        cnx = DBConnect.get_connection()
        cursor = cnx.cursor(dictionary=True)
        query = """SELECT Name
                   FROM Genre
                   ORDER BY Name"""
        cursor.execute(query)
        result = []
        for row in cursor:
            result.append(row["Name"])
        cursor.close()
        cnx.close()
        return result

    @staticmethod
    def getAlbums(genre: str):
        """Album con almeno un brano del genere scelto venduto almeno una volta
        (compare in almeno una riga di InvoiceLine).
        La durata e' la somma dei Milliseconds di TUTTI i brani dell'album, convertita in minuti."""
        cnx = DBConnect.get_connection()
        cursor = cnx.cursor(dictionary=True)
        query = """SELECT a.AlbumId, a.Title, ar.ArtistId, ar.Name AS ArtistName,
                          (SELECT SUM(t2.Milliseconds)
                           FROM Track t2
                           WHERE t2.AlbumId = a.AlbumId) AS TotMs
                   FROM Album a, Artist ar
                   WHERE a.ArtistId = ar.ArtistId
                     AND a.AlbumId IN (SELECT t.AlbumId
                                       FROM Track t, Genre g, InvoiceLine il
                                       WHERE t.GenreId = g.GenreId
                                         AND t.TrackId = il.TrackId
                                         AND g.Name = %s)"""
        cursor.execute(query, (genre,))
        result = []
        for row in cursor:
            durata = float(row["TotMs"]) / 60000
            result.append(Album(row["AlbumId"], row["Title"], row["ArtistId"], row["ArtistName"], durata))
        cursor.close()
        cnx.close()
        return result

    @staticmethod
    def getEdges(genre: str):
        """Coppie di album (id1, id2, peso): esiste almeno una fattura con un brano di A1 e un brano di A2,
        entrambi del genere scelto. Il peso e' il numero di fatture DISTINTE in cui sono acquistati insieme.
        Con t1.AlbumId < t2.AlbumId ogni coppia compare una sola volta (grafo non orientato)."""
        cnx = DBConnect.get_connection()
        cursor = cnx.cursor(dictionary=True)
        query = """SELECT t1.AlbumId AS a1, t2.AlbumId AS a2, COUNT(DISTINCT il1.InvoiceId) AS peso
                   FROM InvoiceLine il1, InvoiceLine il2, Track t1, Track t2, Genre g
                   WHERE il1.InvoiceId = il2.InvoiceId
                     AND il1.TrackId = t1.TrackId
                     AND il2.TrackId = t2.TrackId
                     AND t1.GenreId = g.GenreId
                     AND t2.GenreId = g.GenreId
                     AND g.Name = %s
                     AND t1.AlbumId < t2.AlbumId
                   GROUP BY t1.AlbumId, t2.AlbumId"""
        cursor.execute(query, (genre,))
        result = []
        for row in cursor:
            result.append((row["a1"], row["a2"], row["peso"]))
        cursor.close()
        cnx.close()
        return result


class Album:
    def __init__(self, id: int, title: str, artistId: int, artistName: str, durata: float):
        self.id = id
        self.title = title
        self.artistId = artistId
        self.artistName = artistName
        self.durata = durata  # durata complessiva in minuti (tutti i brani, di qualsiasi genere)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return f"{self.title} - {self.artistName} ({self.durata:.2f} min)"



import networkx as nx

from database.dao import DAO


class Model:
    def __init__(self):
        self._graph = nx.Graph()
        self._idMap = {}

    # ---------- PUNTO 1a ----------
    def getGenres(self):
        return DAO.getAllGenres()

    # ---------- PUNTO 1b, 1c ----------
    def buildGraph(self, genre: str):
        self._graph.clear()
        self._idMap = {}

        # vertici
        albums = DAO.getAlbums(genre)
        for a in albums:
            self._idMap[a.id] = a
            self._graph.add_node(a)

        # archi pesati
        edges = DAO.getEdges(genre)
        for (id1, id2, peso) in edges:
            self._graph.add_edge(self._idMap[id1], self._idMap[id2], weight=peso)

    # ---------- PUNTO 1d ----------
    def getNumNodes(self):
        return self._graph.number_of_nodes()

    def getNumEdges(self):
        return self._graph.number_of_edges()

    # ---------- PUNTO 1e.a ----------
    def getComponentsInfo(self):
        """Restituisce (numero di componenti connesse, dimensione della componente piu' grande)."""
        componenti = list(nx.connected_components(self._graph))
        maxSize = 0
        for c in componenti:
            if len(c) > maxSize:
                maxSize = len(c)
        return len(componenti), maxSize

    # ---------- PUNTO 1e.b ----------
    def getMaxDegreeAlbum(self):
        """Restituisce l'album di grado massimo (a parita' il primo in ordine alfabetico di titolo)
        e la lista dei suoi adiacenti come tuple (album, peso), per peso decrescente
        (a parita' di peso, ordine alfabetico di titolo)."""
        if self._graph.number_of_nodes() == 0:
            return None, []

        # scorro i nodi in ordine alfabetico di titolo: tengo il primo con grado massimo
        nodi = list(self._graph.nodes())
        nodi.sort(key=lambda x: x.title)

        best = None
        bestDegree = -1
        for n in nodi:
            grado = self._graph.degree(n)
            if grado > bestDegree:
                bestDegree = grado
                best = n

        adiacenti = []
        for v in self._graph.neighbors(best):
            peso = self._graph[best][v]["weight"]
            adiacenti.append((v, peso))
        # prima peso decrescente, poi titolo crescente
        adiacenti.sort(key=lambda x: (-x[1], x[0].title))

        return best, adiacenti

    # ---------- PUNTO 1e.c ----------
    def getNumEdgesSameArtist(self):
        """Numero di archi che collegano due album dello stesso artista."""
        count = 0
        for (u, v) in self._graph.edges():
            if u.artistId == v.artistId:
                count += 1
        return count

    # ---------- PUNTO 2a ----------
    def getAlbumsOrdinati(self):
        """Album presenti nel grafo, in ordine alfabetico di titolo (per il menu a tendina)."""
        nodi = list(self._graph.nodes())
        nodi.sort(key=lambda x: x.title)
        return nodi

    # ---------- PUNTO 2b ----------
    def getBestPath(self, start, D: int):
        """Percorso d'ascolto: cammino semplice che parte da 'start', con album consecutivi
        collegati da un arco e di artisti diversi, durata complessiva <= D.
        Massimizza l'affinita' (somma dei pesi degli archi); a parita' di affinita'
        sceglie la durata complessiva minore.
        Restituisce (percorso, affinita', durata). Se l'album di partenza da solo supera D
        non esiste alcun percorso: restituisce ([], 0, 0)."""
        if start.durata > D:
            return [], 0, 0

        # il solo album di partenza (affinita' 0) e' gia' una soluzione ammissibile
        self._bestPath = [start]
        self._bestAffinity = 0
        self._bestDurata = start.durata

        self._ricorsione([start], start.durata, 0, D)

        return self._bestPath, self._bestAffinity, self._bestDurata

    def _ricorsione(self, parziale: list, durata: float, affinita: int, D: int):
        # ogni cammino parziale e' ammissibile: controllo se e' il migliore finora
        if affinita > self._bestAffinity or (affinita == self._bestAffinity and durata < self._bestDurata):
            self._bestPath = list(parziale)
            self._bestAffinity = affinita
            self._bestDurata = durata

        ultimo = parziale[-1]
        for v in self._graph.neighbors(ultimo):
            if v in parziale:
                continue  # cammino semplice
            if v.artistId == ultimo.artistId:
                continue  # consecutivi di artisti diversi
            if durata + v.durata > D:
                continue  # vincolo sulla durata complessiva

            peso = self._graph[ultimo][v]["weight"]
            parziale.append(v)
            self._ricorsione(parziale, durata + v.durata, affinita + peso, D)
            parziale.pop()


from database.DB_connect import DBConnect
from model.album import Album


class DAO:

    @staticmethod
    def getAllGenres():
        """Restituisce la lista dei nomi dei generi (Genre.Name) presenti nel database."""
        cnx = DBConnect.get_connection()
        cursor = cnx.cursor(dictionary=True)
        query = """SELECT Name
                   FROM Genre
                   ORDER BY Name"""
        cursor.execute(query)
        result = []
        for row in cursor:
            result.append(row["Name"])
        cursor.close()
        cnx.close()
        return result

    @staticmethod
    def getAlbums(genre: str):
        """Album con almeno un brano del genere scelto venduto almeno una volta
        (compare in almeno una riga di InvoiceLine).
        La durata e' la somma dei Milliseconds di TUTTI i brani dell'album, convertita in minuti."""
        cnx = DBConnect.get_connection()
        cursor = cnx.cursor(dictionary=True)
        query = """SELECT a.AlbumId, a.Title, ar.ArtistId, ar.Name AS ArtistName,
                          (SELECT SUM(t2.Milliseconds)
                           FROM Track t2
                           WHERE t2.AlbumId = a.AlbumId) AS TotMs
                   FROM Album a, Artist ar
                   WHERE a.ArtistId = ar.ArtistId
                     AND a.AlbumId IN (SELECT t.AlbumId
                                       FROM Track t, Genre g, InvoiceLine il
                                       WHERE t.GenreId = g.GenreId
                                         AND t.TrackId = il.TrackId
                                         AND g.Name = %s)"""
        cursor.execute(query, (genre,))
        result = []
        for row in cursor:
            durata = float(row["TotMs"]) / 60000
            result.append(Album(row["AlbumId"], row["Title"], row["ArtistId"], row["ArtistName"], durata))
        cursor.close()
        cnx.close()
        return result

    @staticmethod
    def getEdges(genre: str):
        """Coppie di album (id1, id2, peso): esiste almeno una fattura con un brano di A1 e un brano di A2,
        entrambi del genere scelto. Il peso e' il numero di fatture DISTINTE in cui sono acquistati insieme.
        Con t1.AlbumId < t2.AlbumId ogni coppia compare una sola volta (grafo non orientato)."""
        cnx = DBConnect.get_connection()
        cursor = cnx.cursor(dictionary=True)
        query = """SELECT t1.AlbumId AS a1, t2.AlbumId AS a2, COUNT(DISTINCT il1.InvoiceId) AS peso
                   FROM InvoiceLine il1, InvoiceLine il2, Track t1, Track t2, Genre g
                   WHERE il1.InvoiceId = il2.InvoiceId
                     AND il1.TrackId = t1.TrackId
                     AND il2.TrackId = t2.TrackId
                     AND t1.GenreId = g.GenreId
                     AND t2.GenreId = g.GenreId
                     AND g.Name = %s
                     AND t1.AlbumId < t2.AlbumId
                   GROUP BY t1.AlbumId, t2.AlbumId"""
        cursor.execute(query, (genre,))
        result = []
        for row in cursor:
            result.append((row["a1"], row["a2"], row["peso"]))
        cursor.close()
        cnx.close()
        return result


import flet as ft


class Controller:
    def __init__(self, view, model):
        self._view = view
        self._model = model

    # ---------- PUNTO 1a: riempie il menu dei generi ----------
    def fillDDGenre(self):
        generi = self._model.getGenres()
        for g in generi:
            self._view._ddGenere.options.append(ft.dropdown.Option(g))
        self._view.update_page()

    # ---------- PUNTO 1b, 1c, 1d: "Crea grafo" ----------
    def handleCreaGrafo(self, e):
        self._view._txt_result.controls.clear()

        genere = self._view._ddGenere.value
        if genere is None:
            self._view._txt_result.controls.append(ft.Text("Selezionare un genere musicale.", color="red"))
            self._view.update_page()
            return

        self._model.buildGraph(genere)

        self._view._txt_result.controls.append(ft.Text("Grafo creato."))
        self._view._txt_result.controls.append(
            ft.Text(f"Numero di vertici: {self._model.getNumNodes()}"))
        self._view._txt_result.controls.append(
            ft.Text(f"Numero di archi: {self._model.getNumEdges()}"))

        # PUNTO 2a: riempie il menu degli album di partenza con i vertici del grafo
        self._view._ddAlbum.options.clear()
        self._view._ddAlbum.value = None
        albums = self._model.getAlbumsOrdinati()
        for a in albums:
            self._view._ddAlbum.options.append(ft.dropdown.Option(key=a.id, text=a.title))

        self._view.update_page()

    # ---------- PUNTO 1e: "Stampa Info" ----------
    def handleStampaInfo(self, e):
        self._view._txt_result.controls.clear()

        if self._model.getNumNodes() == 0:
            self._view._txt_result.controls.append(ft.Text("Creare prima il grafo.", color="red"))
            self._view.update_page()
            return

        # a. componenti connesse
        numComp, maxSize = self._model.getComponentsInfo()
        self._view._txt_result.controls.append(
            ft.Text(f"Componenti connesse: {numComp}. "
                    f"Dimensione della componente piu' grande: {maxSize} album."))

        # b. album di grado massimo e suoi adiacenti
        best, adiacenti = self._model.getMaxDegreeAlbum()
        self._view._txt_result.controls.append(
            ft.Text(f"Album di grado massimo: {best.title} - {best.artistName}"))
        self._view._txt_result.controls.append(ft.Text("Album adiacenti:"))
        for (album, peso) in adiacenti:
            self._view._txt_result.controls.append(
                ft.Text(f"   {album.title} - {album.artistName} (peso {peso})"))

        # c. archi tra album dello stesso artista
        self._view._txt_result.controls.append(
            ft.Text(f"Archi tra album dello stesso artista: {self._model.getNumEdgesSameArtist()}"))

        self._view.update_page()

    # ---------- PUNTO 2: "Trova percorso" ----------
    def handleTrovaPercorso(self, e):
        self._view._txt_result.controls.clear()

        if self._model.getNumNodes() == 0:
            self._view._txt_result.controls.append(ft.Text("Creare prima il grafo.", color="red"))
            self._view.update_page()
            return

        # album di partenza
        idAlbum = self._view._ddAlbum.value
        if idAlbum is None:
            self._view._txt_result.controls.append(
                ft.Text("Selezionare un album di partenza.", color="red"))
            self._view.update_page()
            return
        start = self._model.getAlbumById(int(idAlbum))

        # durata massima D: intero tra 1 e 480
        testo = self._view._txtD.value
        try:
            D = int(testo)
        except (ValueError, TypeError):
            self._view._txt_result.controls.append(
                ft.Text("Inserire un valore intero per la durata massima D.", color="red"))
            self._view.update_page()
            return
        if D < 1 or D > 480:
            self._view._txt_result.controls.append(
                ft.Text("La durata massima D deve essere compresa tra 1 e 480 minuti.", color="red"))
            self._view.update_page()
            return

        percorso, affinita, durata = self._model.getBestPath(start, D)

        if len(percorso) == 0:
            self._view._txt_result.controls.append(
                ft.Text(f"Non esiste alcun percorso: l'album {start.title} da solo supera {D} minuti."))
            self._view.update_page()
            return

        # PUNTO 2d: ATTENZIONE, il formato esatto della stampa va controllato sul testo
        self._view._txt_result.controls.append(
            ft.Text(f"Percorso d'ascolto da {start.title} (D = {D} min)"))
        self._view._txt_result.controls.append(
            ft.Text(f"Numero di album: {len(percorso)}, affinita': {affinita}, durata: {durata:.2f} min"))
        for a in percorso:
            self._view._txt_result.controls.append(
                ft.Text(f"{a.title} - {a.artistName} ({a.durata:.2f} min)"))

        self._view.update_page()