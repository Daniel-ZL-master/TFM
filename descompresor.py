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
import os
import csv
from datetime import datetime

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

    # --- Configuración de Logs y Gráficos ---
    log_filename = f"log_correlacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    history_corr = []

    # Preparamos el archivo CSV
    with open(log_filename, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Timestamp', 'Correlacion_Pearson'])

    # Configuración de la figura con dos subplots
    plt.ion()
    fig, (ax_sig, ax_corr) = plt.subplots(2, 1, figsize=(10, 8))

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
            original = np.array(data['raw_segment'])  # Ahora viene ya recortado por el receptor
            n = len(original)

            # Reconstrucción de la tónica (segmento confirmado)
            reconstructed = np.linspace(data['tonic_start'], data['tonic_end'], n)
            phasic_synthetic = np.zeros(n)

            for p in data['peaks']:
                idx = p['idx']
                # Si el receptor ya filtró por CONFIRMED_LIMIT, idx debería ser < n
                if 0 <= idx < n:
                    t_peaks = np.linspace(0, 4, 400)
                    curve = bateman(t_peaks, p['amp'], p['l1'], p['l2'])

                    end = min(idx + len(curve), n)
                    available = end - idx
                    phasic_synthetic[idx:end] += curve[:available]

            reconstructed += phasic_synthetic

            # --- CÁLCULO DE PÉRDIDA ---
            correlation_matrix = np.corrcoef(original, reconstructed)
            correlation = correlation_matrix[0, 1]
            if np.isnan(correlation):
                correlation = 0.0
            history_corr.append(correlation)
            timestamp = datetime.now().strftime('%H:%M:%S')
            with open(log_filename, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, correlation])

            ax_sig.clear()
            ax_sig.plot(original, label='Original (Buffer)', color='gray', alpha=0.5)
            ax_sig.plot(reconstructed, label='Sintética (Optimized)', color='blue')
            ax_sig.set_title(f"Reconstrucción - Fidelidad: {correlation * 100:.2f}%")
            ax_sig.legend()

            ax_corr.clear()
            ax_corr.plot(history_corr, color='red', marker='.')
            ax_corr.set_ylim(0, 1.1)
            ax_corr.set_ylabel("Pearson R")
            ax_corr.set_title("Evolución de la Correlación en Tiempo Real")

            plt.tight_layout()
            plt.pause(0.1)

            print(f"Correlation of Pearson: {correlation:.6f}")

if __name__ == "__main__":
    descompresor()
