#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Mon Feb 2 12:51:03 2026

@author: da
TO-DO: Cambiar reconstruccion de phasic
"""

import socket
import json
import numpy as np
import matplotlib.pyplot as plt

def bateman(t, amp ,lambda1=0.75, lambda2=2.0):
    """
    Generates the SCR peaks according to bateman function
    lambda1: controls decay time
    lambda2: controls rise time
    """
    peak = amp * (np.exp(-lambda1*t)-np.exp(-lambda2*t))
    t_max = np.log(lambda2/lambda1)/(lambda2-lambda1)
    gain = 1/ (np.exp(-lambda1*t_max)-np.exp(-lambda2*t_max))
    return peak*gain

def descompresor():
    HOST, PORT = '127.0.0.1', 65433
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        conn, addr = s.accept()
        #Whitelisting for security
        if addr[0] != "127.0.0.1":
            conn.close()
            print(f"[SYSTEM] access dennied to {addr[0]}")
        
        file = conn.makefile('r')

        for line in file:
            data = json.loads(line)
            original = np.array(data['raw_segment'])
            n = len(original)
            
            # --- RECONSTRUCCIÓN SIMPLIFICADA ---
            reconstructed = np.linspace(data['tonic_start'], data['tonic_end'], n)
            
            # add phasic peaks
            for idx, amp in zip(data['peak_indexes'], data['peaks_amps']):
                if not np.isnan(amp):
                    # Simulamos un pico simple (una función impulso suavizada)
                    reconstructed[idx:idx+20] += amp 

            # --- CÁLCULO DE PÉRDIDA ---
            error = np.mean((original - reconstructed)**2) # MSE
            loss_percentage = (error / np.var(original)) * 100 if np.var(original) != 0 else 0

            print(f"Pérdida de información (MSE): {error:.6f}")
            print(f"Fidelidad de la señal: {100 - loss_percentage:.2f}%")

            # Comparación visual
            plt.clf()
            plt.plot(original, label='Original (Cruda)', alpha=0.7)
            plt.plot(reconstructed, label='Reconstruida (Params)', linestyle='--')
            plt.title(f"Reconstrucción vs Realidad - Error: {error:.4f}")
            plt.legend()
            plt.pause(0.1)

if __name__ == "__main__":
    descompresor()
