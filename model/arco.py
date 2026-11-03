from dataclasses import dataclass

from model.artist import Artist


@dataclass
class Arco:
    nodoP : Artist
    nodoA: Artist
    peso: int

