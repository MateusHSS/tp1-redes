def verifica_checksum(check1, check2):
  return check1 == check2

def calcula_checksum(data):
  if len(data) % 2 == 1:
    data += b"\x00"

  check = 0

  for i in range(0, len(data), 2):
    word = data[i] + (data[i + 1] << 8)
    check += word
    check = (check >> 16) + (check & 0xFFFF)
  
  check = ~check & 0xFFFF

  return check