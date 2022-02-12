
# Echap pour finir proprement le script
# Espace pour bascule, plein écran / normal


import os
from time import time, sleep
from threading import Thread

import cv2
import numpy as np

from oscpy.server import OSCThreadServer

from pynput.mouse import Button, Controller

from filtre import moving_average
from my_config import MyConfig


global GE_LOOP
GE_LOOP = 1



class GrandeEchelleViewer:
    """Affichage dans une fenêtre OpenCV, et gestion des fenêtres"""
    global GE_LOOP

    def __init__(self, config):

        self.config = config

        freq = int(self.config['histopocene']['frame_rate_du_film'])
        if freq != 0:
            self.tempo = int(1000/freq)
        else:
            print("Le frame rate du film est à 0 !")
            os._exit(0)

        self.info = int(self.config['histopocene']['info'])
        self.mode_expo = int(self.config['histopocene']['mode_expo'])
        self.full_screen = int(self.config['histopocene']['full_screen'])
        if self.mode_expo:
            self.info = 0
            self.full_screen = 1
        self.create_window()
        self.mouse = Controller()

    def create_window(self):
        cv2.namedWindow('histopocene', cv2.WND_PROP_FULLSCREEN)

    def set_window(self):
        """ from pynput.mouse import Button, Controller
            mouse = Controller()
            mouse.position = (50,60)
        """
        if self.full_screen:
            cv2.setWindowProperty(  'histopocene',
                                    cv2.WND_PROP_FULLSCREEN,
                                    cv2.WINDOW_FULLSCREEN)
            x, y, w, h = cv2.getWindowImageRect('histopocene')
            self.mouse.position = (w, h)
        else:
            cv2.setWindowProperty(  'histopocene',
                                    cv2.WND_PROP_FULLSCREEN,
                                    cv2.WINDOW_NORMAL)

    def run(self):
        """Boucle infinie du script"""
        global GE_LOOP

        while GE_LOOP:
            self.video.set(cv2.CAP_PROP_POS_FRAMES, self.frame_nbr)
            ret, img = self.video.read()

            if self.mode_expo:
                self.info = 0
                self.full_screen = 1
                self.set_window()

            if ret:
                if self.info:
                    img = self.draw_text(img, self.frame_nbr)
                    # # print(self.frame_nbr)
                cv2.imshow('histopocene', img)

            k = cv2.waitKey(10)
            # Space pour full screen or not
            if k == 32:  # space
                if not self.mode_expo:
                    if self.full_screen == 1:
                        self.full_screen = 0
                    elif self.full_screen == 0:
                        self.full_screen = 1
                    self.set_window()
            # Esc to  exit
            if k == 27:
                GE_LOOP = 0

        self.video.release()
        cv2.destroyAllWindows()



class GrandeEchelle(GrandeEchelleViewer):

    global GE_LOOP

    def __init__(self, current_dir, config):

        self.config = config

        # Fenêtres OpenCV
        GrandeEchelleViewer.__init__(self, config)


        osc = OSCThreadServer()
        sock = osc.listen(address='127.0.0.1', port=8000, default=True)
        @osc.address(b'/depth')
        def callback(*values):
            depth = int(values[0])
            # # print(f"depth: {depth}")
            self.get_frame(depth)

        self.frame_nbr = 0
        self.last_time = time()
        self.raz = int(self.config['histopocene']['raz'])

        film = str(current_dir) + "/" + self.config['histopocene']['film']
        print("Le film est:", film)
        self.video = cv2.VideoCapture(film)
        self.lenght = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        print("Longueur du film :", self.lenght)  # 38400

        self.profondeur_mini = int(self.config['histopocene']['profondeur_mini'])
        self.profondeur_maxi = int(self.config['histopocene']['profondeur_maxi'])
        self.largeur_maxi = int(self.config['histopocene']['largeur_maxi'])
        self.pile_size = int(self.config['histopocene']['pile_size'])
        self.lissage = int(self.config['histopocene']['lissage'])
        print("self.lissage", self.lissage)
        self.depth = 1
        self.histo = [self.profondeur_mini + 1000]*self.pile_size

        # Stockage des 8 dernières valeurs de frame
        self.slow_size = int(self.config['histopocene']['slow_size'])
        self.histo_slow = [0]*self.slow_size

    def get_frame(self, depth):
        """ Appelé à chaque réception de depth dans receive 'depth',
        longueur en mm
        160 frame pour 12 000 ans
        39750 frame pour 300 cm
        1 cm pour 132 frames
        """
        # # print("depth", depth)
        # Mise à jour de la pile
        self.histo.append(depth)
        del self.histo[0]

        try:
            depth = int(moving_average( np.array(self.histo),
                                        self.lissage,
                                        type_='simple')[0])
        except:
            print("Erreur moving_average depth")

        # Pour bien comprendre
        mini = self.profondeur_mini + 500  # frame 0 si mini
        maxi = self.profondeur_maxi - 500  # frame lenght si maxi
        lenght = self.lenght

        # Voir le dessin
        # (x1, y1, x2, y2) = (mini, 0, maxi, lenght)
        a, b = get_a_b(mini, lenght, maxi, 0)
        frame = int(a*depth + b)
        print("frame", frame)
        # Pour ne jamais planté
        if frame < 0:
            frame = 0
        if frame >= lenght:
            frame = lenght - 1

        # Pile des 8 dernières valeurs lissées
        self.histo_slow.append(frame)
        del self.histo_slow[0]
        try:
            frame = int(moving_average( np.array(self.histo_slow),
                                        self.slow_size - 1,
                                        type_='simple')[0])
        except:
            print("Erreur moving_average depth")

        # Si pas de nouvelle frame en self.raz secondes, remise à 0
        if time() - self.last_time > self.raz:
            # Si tout près del'écran et non capturé
            if frame > self.lenght - 500:
                frame = self.lenght - 1
            else:
                frame = 0

            self.last_time = time()

        self.frame_nbr = frame

    def draw_text(self, img, frame):
        d = {   "Frame du Film": frame,
                "Profondeur mini": self.profondeur_mini,
                "Profondeur maxi": self.profondeur_maxi,
                "X maxi": self.largeur_maxi,
                "Taille pile": self.pile_size,
                "Lissage": self.lissage}
        i = 0
        for key, val in d.items():
            text = key + " : " + str(val)
            cv2.putText(img,  # image
                        text,
                        (30, 150*i+200),  # position
                        cv2.FONT_HERSHEY_SIMPLEX,  # police
                        2,  # taille police
                        (0, 255, 0),  # couleur
                        6)  # épaisseur
            i += 1

        return img



def get_a_b(x1, y1, x2, y2):
    a = (y1 - y2)/(x1 - x2)
    b = y1 - a*x1
    return a, b



if __name__ == '__main__':
    current_dir = '/media/data/3D/projets/depthai_blazepose_labo'

    mc = MyConfig('/media/data/3D/projets/depthai_blazepose_labo/grande_echelle.ini')
    config = mc.conf

    ge = GrandeEchelle(current_dir, config)
    # run est dans Viewer
    ge.run()
