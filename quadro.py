import struct
from checksum import verifica_checksum, calcula_checksum

SYNC = 0xDCC023C2

def quadro(length_recv, id_recv, flags_recv, data_recv):
    frame = struct.pack(
        f">IIHHHB{length_recv}s",
        SYNC,
        SYNC,
        0,
        length_recv,
        id_recv,
        flags_recv,
        data_recv,
    )

    chksum = calcula_checksum(frame)
    checksum = struct.pack("<H", chksum)

    frame = struct.pack(
        f">II2sHHB{length_recv}s",
        SYNC,
        SYNC,
        checksum,
        length_recv,
        id_recv,
        flags_recv,
        data_recv,
    )

    return frame, chksum

def recebe_quadro(conn):
    sws = bytearray()

    for _ in range(8):
        byte = conn.recv(1)
        
        if byte is None:
            return None
        
        sws.extend(byte)

    while True:
        sync1 = sws[:4]
        sync2 = sws[4 : 4 * 2]

        if sync1 == b"\xdc\xc0\x23\xc2" and sync2 == b"\xdc\xc0\x23\xc2":
            break
        else:
            sws.pop(0)
            byte = conn.recv(1)
            
            if byte is None:
                return None
            
            sws.extend(byte)

    checksum = struct.unpack("<H", conn.recv(2))[0]
    length = struct.unpack("!H", conn.recv(2))[0]
    id = struct.unpack("!H", conn.recv(2))[0]
    flags = struct.unpack("!B", conn.recv(1))[0]
    data = conn.recv(length)

    return {
        "id": id,
        "flags": flags,
        "checksum": checksum,
        "length": length,
        "data": data,
    }

def quadro_valido(check, tam, id, flags, dado):
  frame, check_quadro = quadro(tam, id, flags, dado)

  return verifica_checksum(check_quadro, check)

def eh_ack(flag):
  return flag & 0x80

def eh_end(flag):
  return flag & 0x40

def eh_reset(flag):
  return flag & 0x20

def encode(data: bytes, id: int, flags: int):
    frame = struct.pack(
        f">IIHHHB{len(data)}s", SYNC, SYNC, 0, len(data), id, flags, data
    )

    chksum = calcula_checksum(frame)
    checksum = struct.pack("<H", chksum)

    frame = struct.pack(
        f">II2sHHB{len(data)}s",
        SYNC,
        SYNC,
        checksum,
        len(data),
        id,
        flags,
        data,
    )

    return frame, chksum

def faz_ack(id: int):
  frame, chksum = encode("".encode(), id, 0x80)
  return frame, chksum

def faz_reset(message):
  frame, chksum = encode(message.encode(), 0xFFFF, 0x20)
  return frame, chksum

def envia_quadro(conexao, quadro):
  conexao.send(quadro)