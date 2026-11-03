import flet as ft


class Controller:
    def __init__(self, view, model):
        # the view, with the graphical elements of the UI
        self._view = view
        # the model, which implements the logic of the program and holds the data
        self._model = model
        self._choiceArtist = None

    def fillDDGenre(self):
        for g in self._model.getAllGenres():
            self._view._ddGenre.options.append(ft.dropdown.Option(g))


    def handleCreaGrafo(self, e):
        self._view.txt_result.controls.clear()

        genre = self._view._ddGenre.value

        # if genre == None:
        #     self._view.txt_result.controls.clear()
        #     self._view.txt_result.controls.append("Inserire un genere")
        #     self._view.update_page()

        self._model.buildGraph(genre)

        nNodes, nEdges = self._model.getGraphDetails()
        self._view.txt_result.controls.append(ft.Text(f"Il grafo ha {nNodes} nodi e {nEdges} archi"))

        topArtista, influenza = self._model.getTopArtista()
        self._view.txt_result.controls.append(ft.Text(f"il migliore artista è {topArtista} con influenza {influenza}"))

        edges = self._model.getAllEdges()
        migliori5 = edges[0:5]
        self._view.txt_result.controls.append(ft.Text(f"Ecco i migliori 5 archi"))
        for e in migliori5:
            self._view.txt_result.controls.append(ft.Text(f"{e[0]} -> {e[1]}: {e[2]['weight']} "))
        # cosa è e : tupla composta da 3 elementi per ogni arco:
        # e = (nodo_sorgente, nodo_destinazione, dizionario_attributi) (attributi arco esempio peso)



        self.fillDDArtist()

        self._view.update_page()


    def fillDDArtist(self):
        artisti = self._model.getAllNodes()
        for artist in artisti:
            self._view._ddArtist.options.append(ft.dropdown.Option(data=artist,
                                                                   key=artist.Name,
                                                                   on_click=self._handleChoiceArtist))


    def _handleChoiceArtist(self,e):
        self._choiceArtist = e.control.data

    def handleCammino(self,e):
        bestPath = self._model.getBestPath(self._choiceArtist)
        self._view.txt_result.controls.append(ft.Text(f"Cammino massimo trovato ({len(bestPath)} nodi):"))

        for a in bestPath:
            self._view.txt_result.controls.append(ft.Text(a.Name))

        self._view.update_page()