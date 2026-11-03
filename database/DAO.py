from database.DB_connect import DBConnect
from model.artist import Artist
from model.genre import Genre
from model.arco import Arco

class DAO():

    @staticmethod
    def getAllGenres():
        conn = DBConnect.get_connection()

        results = []

        cursor = conn.cursor(dictionary=True)
        query = "select distinct g.Name from genre g order by g.Name"

        cursor.execute(query)

        for row in cursor:
            results.append(row["Name"])

        # for row in cursor:
            # results.append(row["Name"])
        # Chiedi a MySQL di restituire ogni riga sotto forma di dizionario Python,
        # in cui le chiavi sono i nomi delle colonne del database (ad esempio {"Name": "Action"}).
        #
        # Di conseguenza, scrivere row["Name"] significa: "Prendi il dizionario della riga corrente
        # e dammi il valore associato alla chiave "Name""

        cursor.close()
        conn.close()
        return results

    @staticmethod
    def getAllNodes(genere):
        conn = DBConnect.get_connection()

        results = []

        cursor = conn.cursor(dictionary=True)
        query = """SELECT distinct art.ArtistId as  ArtistId,  art.Name as Name
                    from artist art, album a, track t, genre g 
                    where art.ArtistId = a.ArtistId 
                    and t.AlbumId = a.AlbumId 
                    and g.GenreId = t.GenreId 
                    and g.Name = %s """

        cursor.execute(query, (genere, ))

        for row in cursor:
            results.append(Artist(**row))

        cursor.close()
        conn.close()
        return results

    @staticmethod
    def getAllEdges(genere):
        conn = DBConnect.get_connection()

        results = []

        cursor = conn.cursor(dictionary=True)
        query = """ SELECT t1.artista as u, t2.artista as v
FROM
(SELECT distinct art.ArtistId as artista, i.CustomerId as cliente
FROM invoice i, invoiceline il, track t, genre g, artist art, album a
						where i.InvoiceId  = il.InvoiceId 
                        and t.TrackId = il.TrackId 
                        and t.AlbumId = a.AlbumId
                        and g.GenreId = t.GenreId
                        and art.ArtistId = a.ArtistId 
                        and g.Name = %s) t1,
                        (SELECT distinct art.ArtistId as artista, i.CustomerId as cliente
FROM invoice i, invoiceline il, track t, genre g, artist art, album a
						where i.InvoiceId  = il.InvoiceId 
                        and t.TrackId = il.TrackId 
                        and t.AlbumId = a.AlbumId
                        and g.GenreId = t.GenreId
                        and art.ArtistId = a.ArtistId 
                        and g.Name = %s) t2
WHERE t1.artista < t2.artista
AND t1.cliente = t2.cliente
GROUP by t1.artista, t2.artista"""

        cursor.execute(query, (genere, genere))

        for row in cursor:
            results.append((row["u"], row["v"]))

        cursor.close()
        conn.close()
        return results

    @staticmethod
    def getArtistPop(genere):
        conn = DBConnect.get_connection()

        results = []

        cursor = conn.cursor(dictionary=True)
        query = """SELECT art.ArtistId as id, SUM(i.Quantity) as pop
from artist art, album a, track t, genre g, invoiceline i
                        where art.ArtistId = a.ArtistId 
                        and t.AlbumId = a.AlbumId 
                        and g.GenreId = t.GenreId 
                        and g.Name = %s
                        and i.TrackId = t.TrackId
                        GROUP by art.ArtistId  """

        cursor.execute(query, (genere,))

        for row in cursor:
            results.append((row["id"], row["pop"]))

        cursor.close()
        conn.close()
        return results






    # QUERY PER BUILD GRAPH DEL PROF
    @staticmethod
    def getCustomerArtistCounts(genere):
        conn = DBConnect.get_connection()

        results = []

        cursor = conn.cursor(dictionary=True)
        query = """select i.CustomerId, art.ArtistId, count(*) as ntracks
                        from invoice i, invoiceline i2, track t, genre g, artist art,album a
                        where i.InvoiceId  = i2.InvoiceId 
                        and t.TrackId = i2.TrackId 
                        and t.AlbumId = a.AlbumId
                        and g.GenreId = t.GenreId
                        and art.ArtistId = a.ArtistId 
                        and g.GenreId = %s
                        group by i.CustomerId, art.ArtistId"""
        cursor.execute(query, (genere.GenreId,))

        for row in cursor:
            results.append((row["CustomerId"], row["ArtistId"], row["ntracks"]))

        cursor.close()
        conn.close()
        return results

