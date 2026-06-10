"""
Converters personalitzats per a les URLs de StreamSync.

El problema: els IDs de contingut tenen punts (movies-api-1-b2np.onrender.com_1)
que el converter <str:> no captura bé en producció, però <path:> captura també
les barres "/" i trenca les sub-rutes com /opinar/.

Solució: ContentIdConverter accepta qualsevol caràcter excepte "/" — igual que
<path:> però sense capturar barres.
"""


class ContentIdConverter:
    """
    Captura IDs de contingut que poden contenir punts i guions però NO barres.
    Exemples vàlids:
        movies-api-1-b2np.onrender.com_1
        localhost:8080_42
        8080_7
    """
    # [^/]+ = un o més caràcters que no siguin barra
    regex = r'[^/]+'

    def to_python(self, value: str) -> str:
        return value

    def to_url(self, value: str) -> str:
        return value
