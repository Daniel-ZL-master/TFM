#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 27 21:12:03 2026

@author: da

TO-DO: extraer los parametros de un archivo externo para que se sincronicen con
el emisor
"""

from collections import deque
import matplotlib.pyplot as plt
import neurokit2 as nk
import numpy as np
import socket

def reciver():
    HOST = '127.0.0.1'
    PORT = 65432
    SAMPLING_RATE = 100 #Hz
    WINDOW_TIME = 15 #Secs
    MAX_POINTS = SAMPLING_RATE*WINDOW_TIME
    
    raw_data = deque([0]*MAX_POINTS, maxlen=MAX_POINTS)
    
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
                
                s.bind((HOST, PORT))
                s.listen(1)
                print(f"[SYSTEM] Waiting conexion on port {PORT}")
                
                conn, addr = s.accept()
                #Whitelisting for security
                if addr[0] != "127.0.0.1":
                    conn.close()
                    print(f"[SYSTEM] access dennied to {addr[0]}")
                
                with conn:
                    print(f"[SYSTEM] Connected to {addr}")
                    socket_file = conn.makefile('r')
                    counter = 0
                    
                    for line in socket_file:
                        try:
                            value = float(line.strip())
                            raw_data.append(value)
                            counter += 1
                            
                            if counter%10 == 0:
                                signal_array = np.array(raw_data)
                                signals, info = nk.eda_process(signal_array, sampling_rate=SAMPLING_RATE)
                                
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