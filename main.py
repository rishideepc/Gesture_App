from kivy.uix.boxlayout import BoxLayout
from kivy.uix.layout import Layout
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivy.uix.image import Image
from kivymd.uix.screen import Screen
from kivy.clock import Clock
from kivy.lang import Builder
import cv2
from kivy.core.window import Window
from kivy.graphics.texture import Texture
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import helper as htm
import math
import numpy as np
import time
import os
import sys

Window.size= (360, 600)

nav_helper="""

Screen:
    NavigationLayout:
        ScreenManager:
            Screen:
                BoxLayout:
                    orientation: 'vertical'
                    MDToolbar:
                        title: 'Application'
                        elevation: 10
                    Widget:

                Image:


        MDNavigationDrawer:
            id: nav_drawer

"""


class MainApp(MDApp):
    def build(self):
        
        self.title="RealVHC"
        self.theme_cls.primary_palette= "Teal"
        self.theme_cls.primary_hue= "A700"
        self.theme_cls.theme_style= "Dark"
        scr= Screen()   
        self.image= Image()

        btn=MDRaisedButton(on_release=self.load_video, pos_hint={"center_x": 0.5, "center_y":0.3}, text="Click")

    
        scr.add_widget(self.image)
        scr.add_widget(btn)
        self.wCam, self.hCam = 700, 588
        
        self.capture= cv2.VideoCapture(1)
        self.capture.set(3, self.wCam)
        self.capture.set(4, self.hCam)  
        self.pTime= 0

        self.detector= htm.handDectector(detectionCon=0.7, maxHands=1)
        self.devices=AudioUtilities.GetSpeakers()
        self.interface= self.devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)

        self.volume= cast(self.interface, POINTER(IAudioEndpointVolume))
        self.volRange= self.volume.GetVolumeRange()
        self.minVol=self.volRange[0]
        self.maxVol=self.volRange[1]
        self.vol=0
        self.volBar=400
        self.volPerc=0

        self.cTime = time.time()
        self.fps = 1/(self.cTime-self.pTime)
        self.pTime = self.cTime

        Clock.schedule_interval(self.load_video, 1.0/100.0)

        return scr


    def resource_path(relative_path):
        try:            
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def load_video(self, *args):
        success, frame= self.capture.read()
        frame= self.detector.findHands(frame)
        self.lmList= self.detector.findPosition(frame, draw=False)
        if len(self.lmList)!=0:
            x1, y1= self.lmList[4][1], self.lmList[4][2]
            x2, y2= self.lmList[16][1], self.lmList[16][2]
            cx, cy= (x1+x2)//2, (y1+y2)//2
            length= math.hypot(x2-x1, y2, y1)

            self.vol= np.interp(length, [280, 400], [self.minVol, self.maxVol])
            self.volBar= np.interp(length, [280, 400], [400, 150])
            self.volPerc= np.interp(length, [280, 400], [0, 100])
            print(int(length), self.vol)
            self.volume.SetMasterVolumeLevel(self.vol, None)
            sn=10
            self.volPerc = sn * round(self.volPerc/sn)

        cv2.rectangle(frame, (50, 150), (85, 400), (0, 0, 0), 3)
        cv2.rectangle(frame, (50, int(self.volBar)), (85, 400), (0, 0, 0), cv2.FILLED)
        cv2.putText(frame, f'{int(self.volPerc)}%', (48, 450), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 3)
                

        
        cv2.putText(frame, f'FPS: {int(self.fps)}', (48, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 3)
        cv2.putText(frame, f'CV Volume Control', (48, 90), cv2.FONT_HERSHEY_TRIPLEX, 1, (0, 0, 0), 3)

        

        self.image_frame= frame
        buffer =cv2.flip(frame, 0).tostring()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buffer, colorfmt='bgr', bufferfmt='ubyte')
        self.image.texture= texture
                       
        
if __name__ == "__main__":
    MainApp().run()