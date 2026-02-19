#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 27 21:12:03 2026

@author: da

TO-DO: extraer los parametros de un archivo externo para que se sincronicen con
el emisor
"""

from collections import deque
from scipy.optimize import curve_fit
import json
import matplotlib.pyplot as plt
import neurokit2 as nk
import numpy as np
import socket

def bateman_fit(t, amp, lambda1, lambda2):
    if lambda2 <= lambda1 or lambda1 <= 0:
        return np.ones_like(t)*1e6
    peak = amp * (np.exp(-lambda1*t) - np.exp(-lambda2*t))
    t_max = np.log(lambda2/lambda1) / (lambda2-lambda1)
    gain = 1 / (np.exp(-lambda1*t_max) - np.exp(-lambda2*t_max))
    return peak * gain

def reciver():
    HOST = '127.0.0.1'
    PORT_IN = 65432
    PORT_OUT = 65433
    SAMPLING_RATE = 100 #Hz
    WINDOW_TIME = 15 #Secs
    MAX_POINTS = SAMPLING_RATE*WINDOW_TIME
    
    raw_data = deque([0.0]*MAX_POINTS, maxlen=MAX_POINTS)
    
    #Graph config
    plt.ion()
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(10,8))
    line_raw, = ax1.plot(raw_data, color='black', label='EDA RAW', alpha=0.5)
    line_tonic, = ax1.plot(raw_data, color='blue', label='EDA TONIC (SCL)', linewidth=2)
    line_phasic, = ax2.plot(raw_data, color='red', label='EDA PHASIC (SCR)')
    ax1.set_title("EDA raw and SCL")
    ax1.legend(loc='upper right')
    ax2.set_title("EDA phasic SCR")
    ax2.set_ylim(-2.0, 2.0)
    
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                
                s.bind((HOST, PORT_IN))
                s.listen(1)
                print(f"[SYSTEM] Waiting connexion on port {PORT_IN}")
                
                conn, addr = s.accept()
                #Whitelisting for security
                if addr[0] != "127.0.0.1":
                    conn.close()
                    print(f"[SYSTEM] access denied to {addr[0]}")

                s_out = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    s_out.connect((HOST, PORT_OUT))
                    print("[SYSTEM] Connected to final consumer")
                except:
                    print("[SYSTEM] Couldn't connect to final consumer, check that is started")
                
                with conn:
                    print(f"[SYSTEM] Connected to {addr}")
                    socket_file = conn.makefile('r')
                    counter = 0
                    
                    for line in socket_file:
                        try:
                            value = float(line.strip())
                            raw_data.append(value)
                            counter += 1

                            if counter % 100 == 0:
                                signal_array = np.array(raw_data)
                                signals, info = nk.eda_process(signal_array, sampling_rate=SAMPLING_RATE)

                                # Ignoramos los picos que ocurren al final de la ventana
                                SAFETY_MARGIN = 2 * SAMPLING_RATE
                                CONFIRMED_LIMIT = MAX_POINTS - SAFETY_MARGIN

                                index_peaks = np.where(signals["SCR_Peaks"] == 1)[0]
                                index_onsets = np.where(signals["SCR_Onsets"] == 1)[0]

                                optimized_peaks = []
                                for p_idx in index_peaks:
                                    # Buscamos el onset que ocurrió justo antes del peak_index
                                    possible_onsets = index_onsets[index_onsets <= p_idx]

                                    if len(possible_onsets) > 0:
                                        start_idx = possible_onsets[-1]  # El onset más reciente
                                    else:
                                        start_idx = p_idx - 50  # Fallback: 0.5s antes si no hay onset claro

                                    if start_idx < CONFIRMED_LIMIT and (start_idx + 400 < MAX_POINTS):
                                        amp = signals["SCR_Amplitude"].iloc[p_idx]
                                        y_real = signals["EDA_Phasic"].iloc[start_idx: start_idx + 400].values

                                        try:
                                            # Ajustamos usando start_idx como punto cero del tiempo
                                            popt, _ = curve_fit(bateman_fit, np.linspace(0, 4, 400), y_real,
                                                                p0=[amp, 0.75, 2.0])

                                            optimized_peaks.append({
                                                "idx": int(start_idx),  # Enviamos el ONSET como punto de inicio
                                                "amp": float(popt[0]),
                                                "l1": float(popt[1]),
                                                "l2": float(popt[2])
                                            })
                                        except:
                                            continue

                                characteristics = {
                                    "raw_segment": signal_array[:CONFIRMED_LIMIT].tolist(),
                                    "tonic_start": float(signals["EDA_Tonic"].iloc[0]),
                                    "tonic_end": float(signals["EDA_Tonic"].iloc[CONFIRMED_LIMIT]),
                                    "peaks": optimized_peaks
                                }
                                message = json.dumps(characteristics) + "\n"
                                s_out.sendall(message.encode('utf-8'))

                                #Update graph
                                line_raw.set_ydata(signal_array)
                                line_tonic.set_ydata(signals["EDA_Tonic"])
                                line_phasic.set_ydata(signals["EDA_Phasic"])
                                ax1.set_ylim(min(signal_array)-0.5, max(signal_array)+0.5)
                                plt.pause(0.001)
                                
                        except Exception as e:
                            print(f"[ERROR] error processing {e}")
                            continue
                    
                print("[SYSTEM] Transmisor closed connection")
                
        except ConnectionResetError:
            print("[ERROR] Transmisor closed abruptly (Crash).")
        except KeyboardInterrupt:
            print("\n[STOP] Closing server...")
            break
        except Exception as e:
            print(f"[UNEXPECTED ERROR] {e}")
            break
            

if __name__ == "__main__":
    reciver()
