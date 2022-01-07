# System wspomagający kalibrowanie i walidowanie modeli dynamiki pieszych na bazie obrazu z kamer

Do uruchomienia systemy wymagane są niezbędne biblioteki:
- distutils
- wget
- json
- numpy
- cv2

## Przetwarzanie GPU
W celu przyspieszenia procesu analizy wideo zalecane jest wykorzystanie GPU. Projekt wykorzystuje technolgię opartą o architekturę CUDA.

## Zawartość systemu
Folder _calculations_ zawiera klasy oraz funkcje, które są odpowiedzialne za obliczanie charakterystyk pieszych. Aktualna wersja systemu zapewnia estymację:
- wszystkich odległości między pieszymi
- czasu przebywania pieszych na scenie
- średniej prędkości poruszania się ludzi
- szerokości ramion pieszych
- najmniejszej odległości między pieszymi

Folder _camera_calibration_ zawiera skrypty służące do pobrania obrazu z kamery oraz przeprowadzenia procesu kalibracji kamery. W katalogu _results_ znajdują się przykładowe wyniki dziłania systemu. Folder _settings_ zawiera ustawienia użytkownika, informacje o kamerze w postaci pliku _calibration.npz_ oraz skrypt wspomagający proces wyboru regionu zainteresowań opisanego w pracy oraz w instrukcji użytkowania systemu. Katalog _yolo_models_ zawiera model YOLOv4.

## Uruchomienie systemu

Po przeprowadzeniu niezbędnych kroków opisanych w instrukcji użytkowania należy z poziomu terminala wykonać komendę:

```sh
python main.py --run_gui=True
```

Lub

```sh
python main.py --run_gui=False
```

Druga komenda uruchamia system bez interfejsu graficznego.
