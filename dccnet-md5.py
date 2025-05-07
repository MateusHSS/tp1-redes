import hashlib
import logging
import socket
import sys

from server import resolve_ip, communicate

def main():
    logging.basicConfig(level=logging.INFO)

    host, porta = sys.argv[1].split(":")
    (ip_address, family) = resolve_ip(host, int(porta))

    conexao = socket.socket(family, socket.SOCK_STREAM)
    conexao.connect((ip_address, int(porta)))
    conexao.settimeout(1)

    communicate(conexao, sys.argv[2], logging)

main()
