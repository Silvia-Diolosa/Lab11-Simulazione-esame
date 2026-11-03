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