import logging
import sys

from server import inicializa_client, inicializa_servidor

def main():
    logging.basicConfig(
        level=logging.INFO, datefmt="%H:%M:%S", format="%(asctime)s: %(message)s"
    )

    if(sys.argv[1] == '-s'):
        inicializa_servidor(int(sys.argv[2]), sys.argv[3], sys.argv[4], logging)
    elif(sys.argv[1] == '-c'):
        ip, porta = sys.argv[2].split(":")
        inicializa_client(ip, int(porta), sys.argv[3], sys.argv[4], logging)
    else:
        print('Flag inválida')


main()
