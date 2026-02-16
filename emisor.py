#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 27 20:50:37 2026

@author: da
"""

import neurokit2 as nk
import socket
import time

# GENERATION OF SIGNAL VARIABLES
SAMPLING_RATE = 100 #Hz
DURATION = 360 #Seconds
N_SCR = 60

# TRANSMISION VARIABLES
HOST = '127.0.0.1'
PORT = 65432

def transmision_simulator():
    # generate eda signal to send
    eda_signal = nk.eda_simulate(duration=DURATION, sampling_rate=SAMPLING_RATE, scr_number=N_SCR,noise=0.0)
    
    print("Iniciando simulación y envío...")
    
    #connect and send signal through TCP
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT)) # connect to the host port tuple
            
            for value in eda_signal:
                message = f"{value:.4f}\n"
                s.sendall(message.encode('utf-8'))
                
                # sampling rate sleep
                time.sleep(1/SAMPLING_RATE)
    except ConnectionRefusedError:
        print("Conexión rechazada, asegurarse que esta el receptor encendido")
    
if __name__ == "__main__":
    transmision_simulator()
