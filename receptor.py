#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 27 21:12:03 2026

@author: da

TO-DO: Arquitectura de ventana deslizante para representación y analisis en tiempo real
"""

import socket

def reciver():
    HOST = '127.0.0.1'
    PORT = 65432
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"Esperando conexión en {HOST}:{PORT}...")
        
        conn, addr = s.accept()
        with conn:
            print(f"Conectado por: {addr}")
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                print(f"Recibidos {data.decode('utf-8')} uS")

if __name__ == "__main__":
    reciver()