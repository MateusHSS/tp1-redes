import socket
import sys
import hashlib

from quadro import recebe_quadro, quadro_valido, eh_reset, eh_end, eh_ack, faz_ack, faz_reset, encode

def cria_servidor(porta):
  if socket.has_dualstack_ipv6():
    return socket.create_server(("", porta), backlog=1, family=socket.AF_INET6, dualstack_ipv6=True)
  else:
    return socket.create_server(("", porta), backlog=1)
  
def inicializa_servidor(porta, input, output, logging):
    send_id = 0
    last_id = 1
    last_chksum = -1

    input_file = open(input, "rb")
    output_file = open(output, "wb")

    recebimento_finalizado = False
    envio_finalizado = False

    payload = input_file.read(4096)
    next_payload = input_file.read(4096)

    servidor = cria_servidor(porta)

    socket_info = servidor.getsockname()
    logging.info(f"server listening on ({socket_info[0]}):({socket_info[1]})")
    servidor.listen()

    conn, addr = servidor.accept()
    servidor.settimeout(1)

    while (not envio_finalizado) or (not recebimento_finalizado):
        if not recebimento_finalizado:
            try:
                recv = recebe_quadro(conn)
                print('quadro', recv)
                logging.info(f"quadro recebido: {recv}")

                if not quadro_valido(
                    recv["checksum"],
                    recv["length"],
                    recv["id"],
                    recv["flags"],
                    recv["data"],
                ):
                    logging.info("quadro não aceitável, descartando")
                    pass
                elif eh_reset(recv["flags"]):
                    # reset frame
                    logging.info("quadro de reset recebido")
                    logging.info(f"conteudo: {recv['data'].decode()}")
                    logging.info("terminando...")
                    sys.exit(1)
                elif eh_ack(recv["flags"]):
                    logging.info("ack duplicado, continuando ...")
                    pass
                else:
                    if recv["id"] == last_id and recv["checksum"] == last_chksum:
                        # quadro repetido
                        logging.info("duplicado, reenviando ack")
                        ack, _ = faz_ack(last_id)
                        conn.send(ack)
                    else:
                        # quadro de dados
                        last_id = recv["id"]
                        last_chksum = recv["checksum"]

                        logging.info("quadro de dados, escrevendo dado")
                        output_file.write(recv["data"])

                        if eh_end(recv["flags"]):
                            recebimento_finalizado = True
                            output_file.close()
                            logging.info("quadro com flag END recebido")

                        logging.info("enviando ACK")
                        ack, _ = faz_ack(recv["id"])
                        conn.send(ack)
            except socket.timeout:
                pass

        if not envio_finalizado:
            if payload == b"":
                if not envio_finalizado:
                    envio_finalizado = True
                    logging.info("todos os dados enviados")
            else:
                flags = 0x00
                if next_payload == b"":
                    flags |= 0x40
                    logging.info("ultimo quadro a ser enviado")

                frame, _ = encode(payload, send_id, flags)

                ack_received = False
                while not ack_received:
                    conn.send(frame)
                    logging.info(f"quadro enviado: {frame}")

                    try:
                        recv = recebe_quadro(conn)
                        logging.info(f"quadro recebido: {recv}")
                    except socket.timeout:
                        continue

                    if not quadro_valido(
                        recv["checksum"],
                        recv["length"],
                        recv["id"],
                        recv["flags"],
                        recv["data"],
                    ):
                        continue

                    if eh_ack(recv["flags"]) and send_id == recv["id"]:
                        if recv["id"] == send_id:
                            logging.info("quadro ACK")
                            send_id = (send_id + 1) % 2
                            payload = next_payload
                            next_payload = input_file.read(4096)
                            ack_received = True
                        elif recv["id"] == last_id:
                            continue
                    elif eh_reset(recv["flags"]):
                        logging.info("quadro RESET recebido")
                        logging.info(f"conteudo: {recv['data'].decode()}")
                        logging.info("terminando...")
                        sys.exit(1)
                    else:
                        if recv["id"] == last_id and recv["checksum"] == last_chksum:
                            # quadro repetido
                            logging.info("duplicado, reenviando ack")
                            ack, _ = faz_ack(last_id)
                            conn.send(ack)
                        else:
                            # quadro de dados
                            last_id = recv["id"]
                            last_chksum = recv["checksum"]

                            logging.info("quadro de dados, escrevendo dados")
                            output_file.write(recv["data"])

                            if eh_end(recv["flags"]):
                                recebimento_finalizado = True
                                output_file.close()
                                logging.info("quadro com a flag END recebido")

                            logging.info("enviando ACK")
                            ack, _ = faz_ack(recv["id"])
                            conn.send(ack)

    # logging.info("closing input file")
    input_file.close()

    # logging.info("server closing connection")
    conn.close()
    servidor.close()

def inicializa_client(ip, porta, input, output, logging):
    send_id = 0
    last_id = 1
    last_chksum = -1

    input_file = open(input, "rb")
    output_file = open(output, "wb")

    recebimento_finalizado = False
    envio_finalizado = False

    payload = input_file.read(4096)
    next_payload = input_file.read(4096)

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.connect((ip, porta))
    servidor.settimeout(1)

    while (not envio_finalizado) or (not recebimento_finalizado):
        if not recebimento_finalizado:
            try:
                recv = recebe_quadro(servidor)
                #logging.info(f"frame received: {recv}")

                if not quadro_valido(
                    recv["checksum"],
                    recv["length"],
                    recv["id"],
                    recv["flags"],
                    recv["data"],
                ):
                    #logging.info("not acceptable packet, discarting")
                    pass
                elif eh_reset(recv["flags"]):
                    # reset frame
                    #logging.info("received an RESET frame")
                    #logging.info(f"content: {recv['data'].decode()}")
                    #logging.info("terminating...")
                    sys.exit(1)
                elif eh_ack(recv["flags"]):
                    #logging.info("duplicate ack, continuing...")
                    pass
                else:
                    if recv["id"] == last_id and recv["checksum"] == last_chksum:
                        # quadro repetido
                        #logging.info("duplicate, resending ack")
                        ack, _ = faz_ack(last_id)
                        servidor.send(ack)
                    else:
                        # quadro de dados
                        last_id = recv["id"]
                        last_chksum = recv["checksum"]

                        #logging.info("data frame, writing data")
                        output_file.write(recv["data"])

                        if eh_end(recv["flags"]):
                            recebimento_finalizado = True
                            output_file.close()
                            #logging.info("frame with END flag received")

                        #logging.info("sending ACK")
                        ack, _ = faz_ack(recv["id"])
                        servidor.send(ack)
            except socket.timeout:
                pass

        if not envio_finalizado:
            if payload == b"":
                if not envio_finalizado:
                    envio_finalizado = True
                    #logging.info("all data sent")
            else:
                flags = 0x00
                if next_payload == b"":
                    flags |= 0x40
                    #logging.info("last frame is about to be sent")

                frame, _ = encode(payload, send_id, flags)

                ack_received = False
                while not ack_received:
                    servidor.send(frame)
                    #logging.info(f"frame sent: {frame}")

                    try:
                        recv = recebe_quadro(servidor)
                        #logging.info(f"frame received: {recv}")
                    except socket.timeout:
                        continue

                    if not quadro_valido(
                        recv["checksum"],
                        recv["length"],
                        recv["id"],
                        recv["flags"],
                        recv["data"],
                    ):
                        continue

                    if eh_ack(recv["flags"]) and send_id == recv["id"]:
                        if recv["id"] == send_id:
                            #logging.info("ACK frame")
                            send_id = (send_id + 1) % 2
                            payload = next_payload
                            next_payload = input_file.read(4096)
                            ack_received = True
                        elif recv["id"] == last_id:
                            continue
                    elif eh_reset(recv["flags"]):
                        #logging.info("received an RESET frame")
                        #logging.info(f"content: {recv['data'].decode()}")
                        #logging.info("terminating...")
                        sys.exit(1)
                    else:
                        if recv["id"] == last_id and recv["checksum"] == last_chksum:
                            # quadro repetido
                            #logging.info("duplicate, resending ack")
                            ack, _ = faz_ack(last_id)
                            servidor.send(ack)
                        else:
                            # quadro de dados
                            last_id = recv["id"]
                            last_chksum = recv["checksum"]

                            #logging.info("data frame, writing data")
                            output_file.write(recv["data"])

                            if eh_end(recv["flags"]):
                                recebimento_finalizado = True
                                output_file.close()
                                #logging.info("frame with END flag received")

                            #logging.info("sending ACK")
                            ack, _ = faz_ack(recv["id"])
                            servidor.send(ack)

    #logging.info("closing input file")
    input_file.close()

    #logging.info("client closing connection")
    servidor.close()

def resolve_ip(host, port):
  try:
      addr_info = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
      for family, _, _, _, sockaddr in addr_info:
          ip_address = sockaddr[0]
          if family == socket.AF_INET6:
              return (ip_address, family)
      for family, _, _, _, sockaddr in addr_info:
          ip_address = sockaddr[0]
          if family == socket.AF_INET:
              return (ip_address, family)
  except socket.gaierror as e:
      print("error connecting to the server:", e)
      sys.exit(1)

def communicate(conn, gas, logging):
    send_id = 0
    last_id = 1
    last_chksum = -1

    authenticated = False
    all_data_received = False

    acc = ""

    while not authenticated:
        auth, _ = encode((gas + "\n").encode(), send_id, 0x00)
        conn.send(auth)

        try:
            recv = recebe_quadro(conn)
        except socket.timeout:
            continue

        if not quadro_valido(
            recv["checksum"], recv["length"], recv["id"], recv["flags"], recv["data"]
        ):
            continue

        if eh_ack(recv["flags"]) and send_id == recv["id"]:
            authenticated = True
            send_id = (send_id + 1) % 2
        if eh_reset(recv["flags"]):
            conn.close()
            return

    while not all_data_received:
        try:
            recv = recebe_quadro(conn)
        except socket.timeout:
            continue

        if not quadro_valido(
            recv["checksum"], recv["length"], recv["id"], recv["flags"], recv["data"]
        ):
            continue

        if eh_reset(recv["flags"]):
            conn.close()
            return

        if recv["id"] == last_id and recv["checksum"] == last_chksum:
            ack, _ = faz_ack(last_id)
            conn.send(ack)
            continue

        last_id = recv["id"]
        last_chksum = recv["checksum"]

        ack, _ = faz_ack(recv["id"])
        conn.send(ack)

        if eh_end(recv["flags"]):
            all_data_received = True
            continue

        message = recv["data"].decode()
        to_send = []

        if message[-1] != "\n":
            acc += message
        else:
            if acc != "":
                acc += message[0:-1]
                to_send.append(acc)
                acc = ""
            else:
                for m in message.split("\n"):
                    if m != "":
                        to_send.append(m)

        for message in to_send:
            hash = hashlib.md5(message.encode())
            frame, _ = encode((hash.hexdigest() + "\n").encode(), send_id, 0x00)

            ack_received = False
            while not ack_received:
                conn.send(frame)
                try:
                    recv = recebe_quadro(conn)
                except socket.timeout:
                    continue

                if not quadro_valido(
                    recv["checksum"],
                    recv["length"],
                    recv["id"],
                    recv["flags"],
                    recv["data"],
                ):
                    continue

                if eh_ack(recv["flags"]) and send_id == recv["id"]:
                    ack_received = True
                    send_id = (send_id + 1) % 2
                elif eh_reset(recv["flags"]):
                    conn.close()
                    return

    conn.close()